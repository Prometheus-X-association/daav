import json
import os
import logging
from typing import Annotated, List, Optional
from fastapi import APIRouter, HTTPException, Request , status, Header, Query
from fastapi.responses import JSONResponse
import duckdb

from app.routes.workflows import import_and_execute_workflow
from app.services.dataset_service import DatasetService
from app.services.user_service import UserService
from app.services.workflow_service import WorkflowService
from app.models.interface.pdc_chain_interface import PdcChainHeaders, PdcChainResponse, PdcChainRequest
from app.utils.auth_utils import AuthenticatedUser, authenticate_m2m_credentials
from app.services.workflow_output import (
    ensure_output_file, filtered_response, find_node_by_type, find_node_by_url, parse_filters, resolve_owner,
)
from app.utils.utils import get_user_output_path
from app.routes.responses import error_responses

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/output", tags=["outputs"])
UPLOADS_DIR = os.path.join("app", "uploads")

NO_VALID_CREDENTIALS = "No valid credentials found in headers"

# Initialize services
dataset_service = DatasetService()
workflow_service = WorkflowService()
user_service = UserService()

@router.get("/{custom_path}", responses=error_responses(400, 401, 404, 500, 503))
async def get_output_from_custom_path(custom_path: str, request: Request,):
    """
    Get output from custom path by searching through workflows with optional filtering.
    Args:
        custom_path (str): The custom URL path to search for
        request (Request): FastAPI request object containing query parameters
    Returns:
        JSONResponse: JSON output data, filtered if query parameters are provided.
    Raises:
        HTTPException: 
            - 404: If no matching PdcOutput node is found.
            - 500: For workflow execution failures, output generation issues, or unexpected errors.
    
    Example of filter:
            Input: "filter[test][condition][path]=model&filter[test][condition][operator]=STARTS_WITH&filter[test][condition][value]=M"
    """
    try:
        logger.info(f"Searching for output with custom path: {custom_path}")
        # Look for the workflow that has PdcOutput with urlInput == custom_path
        workflow, node = find_node_by_url(await workflow_service.get_workflows(), "PdcOutput", custom_path)
        if node is None:
            logger.warning(f"No PdcOutput node found with URL: {custom_path}")
            raise HTTPException(status_code=404, detail="No PdcOutput node with this URL found")

        user = await resolve_owner(workflow)
        _check_owner_credentials(request, user)
        return await _workflow_output_response(request, workflow, node, user)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error processing custom path {custom_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def _check_owner_credentials(request: Request, user) -> None:
    """401 unless the request headers carry M2M credentials of the workflow owner.

    A workflow without owner has no credentials to check against: it is refused, not served to anyone.
    """
    if not user:
        logger.warning("Output refused: the workflow has no owner to check the credentials against")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=NO_VALID_CREDENTIALS
        )
    authenticated_users: List[AuthenticatedUser] = authenticate_m2m_credentials(request.headers, [user])
    if not authenticated_users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=NO_VALID_CREDENTIALS
        )


async def _workflow_output_response(request: Request, workflow, node, user) -> JSONResponse:
    """Output data of the node, filtered by the query string; the workflow runs if the output is missing."""
    # Construct output file path with user isolation
    file_path = get_user_output_path(node.id, user)
    await ensure_output_file(file_path, workflow, user, import_and_execute_workflow)
    where_clause, params = parse_filters(request)
    return filtered_response(file_path, where_clause, params)


@router.get("/workflow/{workflow_id}", responses=error_responses(400, 401, 404, 500, 503))
async def get_workflow_output(workflow_id: str, request: Request):
    """
    Get workflow output by workflow ID with optional filtering.
    Args:
        workflow_id (str): The ID of the workflow
        request (Request): FastAPI request object containing query parameters
    Returns:
        JSONResponse: JSON output data, filtered if query parameters are provided.
    Raises:
        HTTPException:  
                    - 404 if workflow not found,
                    - 500 for server errors

    """
    try:
        all_users = await user_service.get_all_users()
        authenticated_users: List[AuthenticatedUser] = authenticate_m2m_credentials(request.headers, all_users)
        if not authenticated_users:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=NO_VALID_CREDENTIALS
            )
        logger.info(f"Getting workflow output for ID: {workflow_id}")

        # Get specific workflow from the service
        workflow = await workflow_service.get_workflow(workflow_id)
        if workflow is None:
            logger.warning(f"Workflow not found: {workflow_id}")
            raise HTTPException(status_code=404, detail="Workflow not found")

        node = find_node_by_type(workflow, "PdcOutput")
        if node is None:
            logger.error(f"No PdcOutput node found in workflow: {workflow_id}")
            raise HTTPException(status_code=400, detail="PdcOutput node not found")

        user = await resolve_owner(workflow)
        _check_owner_credentials(request, user)
        return await _workflow_output_response(request, workflow, node, user)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error processing workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
