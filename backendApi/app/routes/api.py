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
from app.utils.drupal_filter_converter import DrupalFilterConverter
from app.utils.utils import filter_data_with_duckdb, verify_route_access, get_user_output_path
import logging
from app.services.user_service import UserService
from app.models.interface.user_interface import User
from app.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["api"])

dataset_service = DatasetService()
workflow_service = WorkflowService()
drupal_filter_converter = DrupalFilterConverter()
user_service = UserService()

@router.get("/{custom_path}")
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
        
        # Get all workflows and search for matching node
        workflows = await workflow_service.get_workflows()
        
        # Find ApiOutput node with matching URL and its workflow
        node = None
        workflow = None
        tokenInput = None
        for wf in workflows:
            for wf_node in wf.pschema.nodes:
                if ((wf_node.type == "ApiOutput") and 
                    wf_node.data.get("urlInput", {}).get("value") == custom_path):
                    node = wf_node
                    workflow = wf
                    tokenInput = wf_node.data.get("tokenInput", {}).get("value")
                    break
            if node:
                break
        
        if node is None:
            logger.warning(f"No ApiOutput node found with URL: {custom_path}")
            raise HTTPException(status_code=404, detail="No data found with this URL")

        # M2M Access Control - Verify route access using tokenInput if present
        api_keys = [tokenInput] if tokenInput else None
        verify_route_access(request, api_keys=api_keys)
        try:
            user = await user_service.get_user_from_workflow(workflow)
            logger.debug(f"Retrieved user from workflow: {getattr(user, 'id', user)}")
        except Exception:
            logger.error("UserService.get_user_from_workflow failed, cannot resolve file isolation", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to verify workflow ownership"
            )
        # Construct output file path with user isolation
        file_path = get_user_output_path(node.id, user)
        
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
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/workflow/{workflow_id}")
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

        # Find ApiOutput node
        api_node = next(
            (node for node in workflow.pschema.nodes if node.type == "ApiOutput"), 
            None
        )
        if not api_node:
            logger.error(f"No ApiOutput node in workflow: {workflow_id}")
            raise HTTPException(status_code=400, detail="ApiOutput node not found")
    
        # Get expected token for M2M control
        expected_token = api_node.data.get("tokenInput", {}).get("value")
        
        # M2M Access Control - Verify route access using tokenInput if present
        api_keys = [expected_token] if expected_token else None
        verify_route_access(request, api_keys=api_keys)

        # Get user from workflow for file isolation
        try:
            user = await user_service.get_user_from_workflow(workflow)
            logger.debug(f"Retrieved user from workflow: {getattr(user, 'id', user)}")
        except Exception:
            logger.error("UserService.get_user_from_workflow failed, cannot resolve file isolation", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to verify workflow ownership"
            )

        # Construct output file path with user isolation
        output_file = get_user_output_path(api_node.id, user)

        # Execute workflow if output doesn't exist
        if not os.path.isfile(output_file):
            logger.info(f"Output file not found, executing workflow: {workflow_id}")
            try:
                await import_and_execute_workflow(workflow, current_user=user)
            except Exception as exec_error:
                logger.error(f"Workflow execution failed: {exec_error}", exc_info=True)
                raise HTTPException(
                    status_code=500, 
                    detail=f"Workflow execution failed: {str(exec_error)}"
                )

            if not os.path.isfile(output_file):
                logger.error(f"Output file not generated after execution: {output_file}")
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
            data = filter_data_with_duckdb(output_file, where=where_clause, params=params)
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
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )



