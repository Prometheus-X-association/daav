"""
Steps shared by the workflow output routes of routes/output.py and routes/api.py.

The access control is not shared: each route keeps its own check (M2M credentials of the
users for /output, token of the node for /api) at its own position in the sequence.
"""
import logging
import os
from typing import Any, Awaitable, Callable, Iterable, Optional, Tuple

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.services.user_service import UserService
from app.utils.drupal_filter_converter import DrupalFilterConverter
from app.utils.utils import filter_data_with_duckdb

logger = logging.getLogger(__name__)

user_service = UserService()
drupal_filter_converter = DrupalFilterConverter()


def find_node_by_url(workflows: Iterable[Any], node_type: str, custom_path: str) -> Tuple[Any, Any]:
    """(workflow, node) of the first node of this type whose URL is the custom path; (None, None) if none."""
    for workflow in workflows:
        for node in workflow.pschema.nodes:
            if node.type == node_type and node.data.get("urlInput", {}).get("value") == custom_path:
                return workflow, node
    return None, None


def find_node_by_type(workflow: Any, node_type: str) -> Optional[Any]:
    """The first node of this type in the workflow, or None."""
    return next((node for node in workflow.pschema.nodes if node.type == node_type), None)


async def resolve_owner(workflow: Any):
    """The owner of the workflow; 503 if the user service fails, rather than skipping the ownership checks."""
    try:
        user = await user_service.get_user_from_workflow(workflow)
        logger.debug(f"Retrieved user from workflow: {getattr(user, 'id', user)}")
        return user
    except Exception:
        logger.error("UserService.get_user_from_workflow failed, cannot verify workflow ownership", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to verify workflow ownership"
        )


async def ensure_output_file(file_path: str, workflow: Any, user: Any,
                             execute: Callable[..., Awaitable[Any]]) -> None:
    """Run the workflow if its output file is missing; 500 if it fails or does not produce the file."""
    logger.debug(f"Looking for output file: {file_path}")
    if os.path.isfile(file_path):
        return

    logger.info(f"Output file not found, executing workflow: {workflow.id}")
    try:
        await execute(workflow, current_user=user)
    except Exception as exec_error:
        logger.error(f"Workflow execution failed: {exec_error}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(exec_error)}"
        )

    if not os.path.isfile(file_path):
        logger.error(f"Output file not generated after execution: {file_path}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate output file"
        )


def parse_filters(request: Request) -> Tuple[Optional[str], Optional[list]]:
    """(WHERE clause, parameters) of the Drupal filters of the query string; (None, None) without query; 400 if invalid."""
    if not request.query_params:
        return None, None
    logger.info(f"Applying filters with parameters: {request.query_params}")
    try:
        return drupal_filter_converter.convert_query_string_to_where(str(request.query_params))
    except Exception as filter_error:
        logger.error(f"Filter parsing failed: {filter_error}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid filter parameters: {str(filter_error)}"
        )


def filtered_response(file_path: str, where: Optional[str], params: Optional[list]) -> JSONResponse:
    """The output data, filtered; 500 if the filtering fails."""
    try:
        data = filter_data_with_duckdb(file_path, where=where, params=params)
        return JSONResponse(content=data)
    except Exception as filter_error:
        logger.error(f"Data filtering failed: {filter_error}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error filtering data: {str(filter_error)}"
        )
