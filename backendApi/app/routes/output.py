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
from app.utils.drupal_filter_converter import DrupalFilterConverter
from app.utils.utils import filter_data_with_duckdb, get_user_output_path

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/output", tags=["outputs"])
UPLOADS_DIR = os.path.join("app", "uploads")

# Initialize services
dataset_service = DatasetService()
workflow_service = WorkflowService()
user_service = UserService()
drupal_filter_converter = DrupalFilterConverter()

@router.get("/{custom_path}")
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
        # Get all workflows from the service
        workflows = await workflow_service.get_workflows()
        
        # Look for the workflow that has PdcOutput with urlInput == custom_path
        node = None
        workflow = None
        for wf in workflows:
            for wf_node in wf.pschema.nodes:
                if ((wf_node.type == "PdcOutput") and 
                    wf_node.data.get("urlInput", {}).get("value") == custom_path):
                    node = wf_node
                    workflow = wf
                    break
            if node:
                break

        if node is None:
            logger.warning(f"No PdcOutput node found with URL: {custom_path}")
            raise HTTPException(status_code=404, detail="No PdcOutput node with this URL found")
                # Attempt to fetch user info from UserService if available

        try:
            user = await user_service.get_user_from_workflow(workflow)
            logger.debug(f"Retrieved user from workflow: {getattr(user, 'id', user)}")
        except Exception:
            # Service error: cannot determine ownership → reject rather than silently bypass auth
            logger.error("UserService.get_user_from_workflow failed, denying access", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to verify workflow ownership"
            )
        if user:
            authenticated_users: List[AuthenticatedUser] = await authenticate_m2m_credentials(request.headers, [user])
            if not authenticated_users:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No valid credentials found in headers"
                )
        # Construct output file path with user isolation
        file_path = get_user_output_path(node.id, user)
        logger.debug(f"Looking for output file: {file_path}")

        # Execute workflow if output doesn't exist
        if not os.path.isfile(file_path):
            logger.info(f"Output file not found, executing workflow: {workflow.id}")
            try:
                await import_and_execute_workflow(workflow, current_user=user)
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

        # Apply filters if query parameters exist
        where_clause = None
        params = None
        if request.query_params:
            logger.info(f"Applying filters with parameters: {request.query_params}")
            try:
                where_clause, params = drupal_filter_converter.convert_query_string_to_where(
                    str(request.query_params)
                )
            except Exception as filter_error:
                logger.error(f"Filter parsing failed: {filter_error}", exc_info=True)
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid filter parameters: {str(filter_error)}"
                )

        # Get filtered data
        try:
            data = filter_data_with_duckdb(file_path, where=where_clause, params=params)
            return JSONResponse(content=data)
        except Exception as filter_error:
            logger.error(f"Data filtering failed: {filter_error}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error filtering data: {str(filter_error)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing custom path {custom_path}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/workflow/{workflow_id}")
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
        authenticated_users: List[AuthenticatedUser] = await authenticate_m2m_credentials(request.headers, all_users)
        if not authenticated_users:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No valid credentials found in headers"
            )
        logger.info(f"Getting workflow output for ID: {workflow_id}")
        
        # Get specific workflow from the service
        workflow = await workflow_service.get_workflow(workflow_id)
        
        if workflow is None:
            logger.warning(f"Workflow not found: {workflow_id}")
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Find PdcOutput node in the workflow
        node = None
        for wf_node in workflow.pschema.nodes:
            if wf_node.type == "PdcOutput":
                node = wf_node
                break
        
        if node is None:
            logger.error(f"No PdcOutput node found in workflow: {workflow_id}")
            raise HTTPException(status_code=400, detail="PdcOutput node not found")
        
        try:
            user = await user_service.get_user_from_workflow(workflow)
            logger.debug(f"Retrieved user from workflow: {getattr(user, 'id', user)}")
        except Exception:
            # Service error: cannot determine ownership → reject rather than silently bypass auth
            logger.error("UserService.get_user_from_workflow failed, denying access", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to verify workflow ownership"
            )
        if user:
            authenticated_users: List[AuthenticatedUser] = await authenticate_m2m_credentials(request.headers, [user])
            if not authenticated_users:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No valid credentials found in headers"
                )
        # Construct output file path with user isolation
        file_path = get_user_output_path(node.id, user)

        logger.debug(f"Looking for workflow output file: {file_path}")

        # Execute workflow if output doesn't exist
        if not os.path.isfile(file_path):
            logger.info(f"Output file not found, executing workflow: {workflow_id}")
            try:
                await import_and_execute_workflow(workflow, current_user=user)
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

        # Apply filters if query parameters exist
        where_clause = None
        params = None
        if request.query_params:
            logger.info(f"Applying filters with parameters: {request.query_params}")
            try:
                where_clause, params = drupal_filter_converter.convert_query_string_to_where(
                    str(request.query_params)
                )
            except Exception as filter_error:
                logger.error(f"Filter parsing failed: {filter_error}", exc_info=True)
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid filter parameters: {str(filter_error)}"
                )

        # Get filtered data
        try:
            data = filter_data_with_duckdb(file_path, where=where_clause, params=params)
            return JSONResponse(content=data)
        except Exception as filter_error:
            logger.error(f"Data filtering failed: {filter_error}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error filtering data: {str(filter_error)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
