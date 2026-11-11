import json
from typing import Annotated, Optional
from fastapi import APIRouter, HTTPException, Query, Request, Header, status
from app.routes.workflows import execute_workflow, import_and_execute_workflow
from app.services.dataset_service import DatasetService
from app import main
from app.core.workflow import Workflow
import os
from fastapi.responses import JSONResponse

from app.services.workflow_service import WorkflowService
from app.services.workflow_output import (
    ensure_output_file, filtered_response, find_node_by_type, find_node_by_url, parse_filters, resolve_owner,
)
from app.utils.utils import verify_route_access, get_user_output_path
import logging
from app.services.user_service import UserService
from app.models.interface.user_interface import User
from app.config.settings import settings
from app.routes.responses import error_responses

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["api"])

dataset_service = DatasetService()
workflow_service = WorkflowService()
user_service = UserService()

@router.get("/{custom_path}", responses=error_responses(400, 404, 500, 503))
async def get_output_from_custom_path(
        custom_path: str, 
        request: Request
    ):
    """
    Get output from custom path by searching through workflows with optional filtering.
    Args:
        custom_path (str): The custom URL path to search for
        request (Request): FastAPI request object containing query parameters
    Returns:
        JSONResponse: JSON output data, filtered if query parameters are provided.
    Raises:
        HTTPException: 
            - 403: If access is denied (M2M control)
            - 404: If no matching ApiOutput node is found.
            - 500: For workflow execution failures, output generation issues, or unexpected errors.
    Example of filter:
            Input: "filter[test][condition][path]=model&filter[test][condition][operator]=STARTS_WITH&filter[test][condition][value]=M"
    """
    try:
        logger.info(f"Searching for output with custom path: {custom_path}")
        # Find ApiOutput node with matching URL and its workflow
        workflow, node = find_node_by_url(await workflow_service.get_workflows(), "ApiOutput", custom_path)
        if node is None:
            logger.warning(f"No ApiOutput node found with URL: {custom_path}")
            raise HTTPException(status_code=404, detail="No data found with this URL")

        # M2M Access Control - Verify route access using tokenInput if present
        _verify_node_token(request, node)
        return await _workflow_output_response(request, workflow, node)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing custom path {custom_path}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


def _verify_node_token(request: Request, node) -> None:
    """403 unless the request carries the token of the node (or comes from a whitelisted domain)."""
    token_input = node.data.get("tokenInput", {}).get("value")
    api_keys = [token_input] if token_input else None
    verify_route_access(request, api_keys=api_keys)


async def _workflow_output_response(request: Request, workflow, node) -> JSONResponse:
    """Output data of the node, filtered by the query string; the workflow runs if the output is missing."""
    # Get user from workflow for file isolation
    user = await resolve_owner(workflow)
    # Construct output file path with user isolation
    file_path = get_user_output_path(node.id, user)
    await ensure_output_file(file_path, workflow, user, import_and_execute_workflow)
    where_clause, params = parse_filters(request)
    return filtered_response(file_path, where_clause, params)


@router.get("/workflow/{workflow_id}", responses=error_responses(400, 404, 500, 503))
async def get_workflow_output(
        workflow_id: str, 
        request: Request
    ):
    """
    Get workflow output data with optional filtering.
    Args:
        workflow_id (str): The ID of the workflow
        request (Request): FastAPI request object containing query parameters
    Returns:
        JSONResponse: JSON output data, filtered if query parameters are provided.
    Raises:
        HTTPException: 
            - 403: If access is denied (M2M control)
            - 404: If workflow not found
    """
    try:
        logger.info(f"Getting output for workflow: {workflow_id}")

        # Get workflow and validate
        workflow = await workflow_service.get_workflow(workflow_id)
        if not workflow:
            logger.warning(f"Workflow not found: {workflow_id}")
            raise HTTPException(status_code=404, detail="Workflow not found")

        api_node = find_node_by_type(workflow, "ApiOutput")
        if not api_node:
            logger.error(f"No ApiOutput node in workflow: {workflow_id}")
            raise HTTPException(status_code=400, detail="ApiOutput node not found")

        # M2M Access Control - Verify route access using tokenInput if present
        _verify_node_token(request, api_node)
        return await _workflow_output_response(request, workflow, api_node)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
