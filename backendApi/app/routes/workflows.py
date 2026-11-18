import logging
from fastapi import APIRouter, HTTPException, status, Body, Depends
from typing import Annotated, List, Optional
from app.models.interface.workflow_interface import IProject
from app.services.workflow_service import workflow_service
from app.middleware.auth import CurrentUser
from app.core.workflow import Workflow
from app.core.execution_context import ExecutionContext
from app.models.interface.user_interface import User
from app.routes.responses import error_responses

logger = logging.getLogger(__name__)

INTERNAL_SERVER_ERROR = "Internal server error"

router = APIRouter(
    prefix="/workflows",
    tags=["workflows"], 
    responses={404: {"description": "Not found"}}
)

@router.get("/", responses=error_responses(500))
async def get_workflows(current_user: CurrentUser) -> List[IProject]:
    """
    Fetch the list of workflows accessible by current user.

    This endpoint retrieves all workflows stored in the database.

    Returns:
        List[IProject]: A list of workflow projects.
        
    Raises:
        HTTPException: 500 if there's an internal server error.
        
    Example:
        ```
        GET /workflows/
        ```
        
    Response:
        ```json
        [
            {
                "id": "workflow-123",
                "name": "My Workflow",
                "revision": "1.0",
                "dataConnectors": [],
                "schema": {...},
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        ]
        ```
    """
    try:
        logger.info(f"User {current_user.username} fetching workflows")
        workflows = await workflow_service.get_workflows(current_user)
        logger.info(f"Successfully returned {len(workflows)} workflows to user {current_user.username}")
        return workflows
    except Exception as e:
        logger.exception(f"Error fetching workflows: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)

@router.get("/{id}", responses=error_responses(500))
async def get_workflow(id: str, current_user: CurrentUser) -> IProject:
    """
    Retrieve a workflow by its ID with permission check.

    This endpoint fetches a specific workflow from the database using its unique identifier.

    Args:
        id (str): The unique identifier of the workflow to retrieve.

    Returns:
        IProject: The workflow with the specified ID.

    Raises:
        HTTPException: 404 if the workflow with the specified ID is not found.
        HTTPException: 500 if there's an internal server error.
        
    Example:
        ```
        GET /workflows/workflow-123
        ```
        
    Response:
        ```json
        {
            "id": "workflow-123",
            "name": "My Workflow",
            "revision": "1.0",
            "dataConnectors": ["connector-1", "connector-2"],
            "schema": {
                "nodes": [...],
                "connections": [...],
                "revision": "1.0"
            },
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        ```
    """
    try:
        logger.info(f"User {current_user.username} fetching workflow with ID: {id}")
        workflow = await workflow_service.get_workflow(id, current_user)
        return workflow
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching workflow {id}: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)

@router.post("/", status_code=status.HTTP_201_CREATED, responses=error_responses(500))
async def create_workflow(current_user: CurrentUser, workflow_data: IProject) -> IProject:
    """
    Create a new workflow with ownership assignment.

    This endpoint creates a new workflow in the database from a JSON representation.
    If no ID is provided, a new UUID will be automatically generated.

    Args:
        workflow_data (IProject): The workflow data to create.
                                Must contain at least 'name' field.

    Returns:
        IProject: The newly created workflow with generated timestamps.

    Raises:
        HTTPException: 400 if the workflow data is invalid.
        HTTPException: 500 if there's an internal server error.
        
    Example:
        ```
        POST /workflows/
        Content-Type: application/json
        
        {
            "name": "Data Processing Workflow",
            \"revision\": \"1.0\",
            \"dataConnectors\": [\"connector-123\", \"connector-456\"],
            \"schema\": {
                \"nodes\": [
                    {
                        \"id\": \"node-1\",
                        \"type\": \"input\",
                        \"label\": \"Data Input\",
                        \"inputs\": {},
                        \"outputs\": {
                            \"output1\": {
                                \"id\": \"output1\",
                                \"label\": \"Data Output\",
                                \"socket\": {
                                    \"name\": \"data\"
                                }
                            }
                        },
                        \"controls\": {
                            \"dataset\": {
                                \"type\": \"select\",
                                \"id\": \"dataset\",
                                \"readonly\": false,
                                \"value\": \"dataset-123\",
                                \"__type\": \"control\"
                            }
                        },
                        \"position\": {
                            \"x\": 100,
                            \"y\": 200
                        },
                        \"data\": {
                            \"selectedDataset\": \"dataset-123\"
                        }
                    },
                    {
                        \"id\": \"node-2\",
                        \"type\": \"filter\",
                        \"label\": \"Data Filter\",
                        \"inputs\": {
                            \"input1\": {
                                \"id\": \"input1\",
                                \"label\": \"Data Input\",
                                \"socket\": {
                                    \"name\": \"data\"
                                }
                            }
                        },
                        \"outputs\": {
                            \"output1\": {
                                \"id\": \"output1\",
                                \"label\": \"Filtered Data\",
                                \"socket\": {
                                    \"name\": \"data\"
                                }
                            }
                        },
                        \"controls\": {
                            \"condition\": {
                                \"type\": \"text\",
                                \"id\": \"condition\",
                                \"readonly\": false,
                                \"value\": \"age > 18\",
                                \"__type\": \"control\"
                            }
                        },
                        \"position\": {
                            \"x\": 400,
                            \"y\": 200
                        },
                        \"data\": {
                            \"filterCondition\": \"age > 18\"
                        }
                    }
                ],
                \"connections\": [
                    {
                        \"id\": \"connection-1\",
                        \"sourceNode\": \"node-1\",
                        \"targetNode\": \"node-2\",
                        \"sourcePort\": \"output1\",
                        \"targetPort\": \"input1\"
                    }
                ],
                \"revision\": \"1.0\"
            }
        }"
        ```
        
    Response:
        ```json
        {
            "id": "generated-uuid-123",
            "name": "Data Processing Workflow",
            "revision": "1.0",
            "dataConnectors": ["connector-123", "connector-456"],
            "schema": {
                "nodes": [
                    {
                        "id": "node-1",
                        "type": "input",
                        "label": "Data Input",
                        "inputs": {},
                        "outputs": {
                            "output1": {
                                "id": "output1",
                                "label": "Data Output",
                                "socket": {
                                    "name": "data"
                                }
                            }
                        },
                        "controls": {
                            "dataset": {
                                "type": "select",
                                "id": "dataset",
                                "readonly": false,
                                "value": "dataset-123",
                                "__type": "control"
                            }
                        },
                        "position": {
                            "x": 100,
                            "y": 200
                        },
                        "data": {
                            "selectedDataset": "dataset-123"
                        }
                    },
                    {
                        "id": "node-2",
                        "type": "filter",
                        "label": "Data Filter",
                        "inputs": {
                            "input1": {
                                "id": "input1",
                                "label": "Data Input",
                                "socket": {
                                    "name": "data"
                                }
                            }
                        },
                        "outputs": {
                            "output1": {
                                "id": "output1",
                                "label": "Filtered Data",
                                "socket": {
                                    "name": "data"
                                }
                            }
                        },
                        "controls": {
                            "condition": {
                                "type": "text",
                                "id": "condition",
                                "readonly": false,
                                "value": "age > 18",
                                "__type": "control"
                            }
                        },
                        "position": {
                            "x": 400,
                            "y": 200
                        },
                        "data": {
                            "filterCondition": "age > 18"
                        }
                    }
                ],
                "connections": [
                    {
                        "id": "connection-1",
                        "sourceNode": "node-1",
                        "targetNode": "node-2",
                        "sourcePort": "output1",
                        "targetPort": "input1"
                    }
                ],
                "revision": "1.0"
            },
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        ```
    """
    try:
        logger.info(f"User {current_user.username} creating new workflow")
        
        # Pass IProject directly to service (UUID generated automatically if needed)
        new_workflow = await workflow_service.create_workflow(workflow_data, current_user)
        logger.info(f"User {current_user.username} successfully created workflow: {new_workflow.name}")
        return new_workflow
        
    except Exception as e:
        logger.exception(f"Error creating workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to create workflow")

@router.put("/", responses=error_responses(400, 500))
async def update_workflow(current_user: CurrentUser, workflow_data: IProject) -> IProject:
    """
    Update an existing workflow with permission check.

    This endpoint updates an existing workflow in the database. Only fields explicitly
    provided in the request will be updated. System fields (owner_id, created_at) are preserved.

    Args:
        workflow_data (IProject): The workflow data with fields to update.
                                Must include the 'id' field to identify the workflow to update.

    Returns:
        IProject: The updated workflow with new timestamp.

    Raises:
        HTTPException: 400 if the workflow ID is missing or data is invalid.
        HTTPException: 404 if the workflow with the specified ID is not found.
        HTTPException: 500 if there's an internal server error.
        
    Example:
        ```
        PUT /workflows/
        Content-Type: application/json
        
        {
            "id": "workflow-123",
            \"name\": \"Updated Workflow\",
            \"revision\": \"2.0\",
            \"dataConnectors\": [\"connector-1\"],
            \"schema\": {
                \"nodes\": [...],
                \"connections\": [...],
                \"revision\": \"2.0\"
            }
        }"
        ```
        
    Response:
        ```json
        {
            "id": "workflow-123",
            "name": "Updated Workflow",
            "revision": "2.0",
            "dataConnectors": ["connector-1"],
            "schema": {...},
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T12:00:00"
        }
        ```
    """
    try:
        logger.info(f"User {current_user.username} updating workflow")
        
        if not workflow_data.id:
            raise HTTPException(status_code=400, detail="Workflow ID is required for update")
        
        # Update workflow with permission check - pass IProject directly
        updated_workflow = await workflow_service.update_workflow(workflow_data, current_user)
        logger.info(f"User {current_user.username} successfully updated workflow: {updated_workflow.name}")
        return updated_workflow
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error updating workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to update workflow")

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, responses=error_responses(404, 500))
async def delete_workflow(id: str, current_user: CurrentUser):
    """
    Delete a workflow by its ID with permission check.

    This endpoint permanently removes a workflow from the database.
    This operation cannot be undone.

    Args:
        id (str): The unique identifier of the workflow to delete.

    Returns:
        None: Returns 204 No Content on successful deletion.

    Raises:
        HTTPException: 404 if the workflow with the specified ID is not found.
        HTTPException: 500 if there's an internal server error.
        
    Example:
        ```
        DELETE /workflows/workflow-123
        ```
        
    Response:
        ```
        HTTP 204 No Content
        ```
    """
    try:
        logger.info(f"User {current_user.username} deleting workflow with ID: {id}")
        success = await workflow_service.delete_workflow(id, current_user)
        
        if not success:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        logger.info(f"User {current_user.username} successfully deleted workflow: {id}")
        logger.info(f"Successfully deleted workflow: {id}")
        return
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting workflow {id}: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)

@router.post("/execute/{id}", status_code=status.HTTP_200_OK, response_model=IProject, responses=error_responses(500))
async def execute_workflow(id: str, current_user: CurrentUser):
    """
    Execute a workflow by its ID.

    This endpoint executes all nodes in a workflow sequentially according to their connections.
    The workflow will process all data (not limited to samples).

    Args:
        id (str): The unique identifier of the workflow to execute.

    Returns:
        IProject: The updated project configuration after execution, including any output data.

    Raises:
        HTTPException: 404 if the workflow with the specified ID is not found.
        HTTPException: 500 if there's an execution error or internal server error.
        
    Example:
        ```
        POST /workflows/execute/workflow-123
        ```
        
    Response:
        ```json
        {
            "id": "workflow-123",
            "name": "My Workflow",
            "schema": {
                "nodes": [...],
                "connections": [...],
                "revision": "1.0"
            },
            "updated_at": "2023-01-01T12:00:00"
        }
        ```
    """
    try:
        logger.info(f"User {current_user.username} executing workflow with ID: {id}")
        workflow_data = await workflow_service.get_workflow(id, current_user)
        result = await import_and_execute_workflow(workflow_data, current_user=current_user)
        logger.info(f"User {current_user.username} successfully executed workflow: {id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error executing workflow {id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute workflow")

@router.post("/execute_node/{id}/{node_id}", status_code=status.HTTP_200_OK, response_model=IProject, responses=error_responses(404, 500))
async def execute_node(id: str, node_id: str, current_user: CurrentUser):
    """
    Execute a specific node in a workflow by its ID.

    This endpoint executes only a specific node within a workflow.
    This operation works on a sample level (limited to 20 items) for performance reasons.

    Args:
        id (str): The unique identifier of the workflow containing the node.
        node_id (str): The unique identifier of the node to execute within the workflow.

    Returns:
        IProject: The updated project configuration after node execution, with sample data.

    Raises:
        HTTPException: 404 if the workflow or node with the specified IDs is not found.
        HTTPException: 500 if there's an execution error or internal server error.
        
    Example:
        ```
        POST /workflows/execute_node/workflow-123/node-456
        ```
        
    Response:
        ```json
        {
            "id": "workflow-123",
            "name": "My Workflow",
            "schema": {
                "nodes": [...],
                "connections": [...],
                "revision": "1.0"
            },
            "updated_at": "2023-01-01T12:00:00"
        }
        ```
    """
    try:
        logger.info(f"User {current_user.username} executing node {node_id} in workflow {id}")
        workflow_data = await workflow_service.get_workflow(id, current_user)
        
        if node_id not in [node.id for node in workflow_data.pschema.nodes]:
            raise HTTPException(status_code=404, detail="Node not found in workflow")
        
        result = await import_and_execute_workflow(workflow_data, node_id=node_id, sample=True, current_user=current_user)
        logger.info(f"User {current_user.username} successfully executed node {node_id} in workflow {id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error executing node {node_id} in workflow {id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute node")

@router.post("/execute", status_code=status.HTTP_200_OK, response_model=IProject, responses=error_responses(500))
async def execute_workflow_json(current_user: CurrentUser, workflow_json: Annotated[IProject, Body(description="The workflow object to execute")]):
    """
    Execute a workflow from its JSON representation.

    This endpoint allows you to execute a workflow without storing it in the database first.
    Useful for testing workflows or one-time executions.

    Args:
        workflow_json (IProject): The complete workflow object to execute.
                                Must include valid schema with nodes and connections.

    Returns:
        IProject: The updated project configuration after execution, including any output data.

    Raises:
        HTTPException: 400 if the workflow data is invalid.
        HTTPException: 500 if there's an execution error or internal server error.
        
    Example:
        ```
        POST /workflows/execute
        Content-Type: application/json
        
        {
            "id": "temp-workflow",
            "name": "Temporary Workflow",
            "schema": {
                "nodes": [...],
                "connections": [...],
                "revision": "1.0"
            }
        }
        ```
        
    Response:
        ```json
        {
            "id": "temp-workflow",
            "name": "Temporary Workflow",
            "schema": {
                "nodes": [...],
                "connections": [...],
                "revision": "1.0"
            }
        }
        ```
    """
    try:
        logger.info(f"User {current_user.username} executing workflow from JSON: {workflow_json.name}")
        result = await import_and_execute_workflow(workflow_json, current_user=current_user)
        logger.info(f"User {current_user.username} successfully executed workflow from JSON: {workflow_json.name}")
        return result
    except Exception as e:
        logger.exception(f"Error executing workflow from JSON: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute workflow")

@router.post("/execute_node/{node_id}", status_code=status.HTTP_200_OK, response_model=IProject, responses=error_responses(404, 500))
async def execute_node_json(node_id: str, current_user: CurrentUser, workflow: Annotated[IProject, Body(description="The workflow object containing the node to execute")]):
    """
    Execute a specific node in a workflow from its JSON representation.

    This endpoint allows you to execute a specific node within a workflow without storing 
    the workflow in the database first. This operation works on a sample level 
    (limited to 20 items retrieved only) for performance reasons.

    Args:
        node_id (str): The unique identifier of the node to execute within the workflow.
        workflow (IProject): The complete workflow object containing the node to execute.

    Returns:
        IProject: The updated project configuration after node execution, with sample data.

    Raises:
        HTTPException: 404 if the specified node is not found in the workflow.
        HTTPException: 400 if the workflow data is invalid.
        HTTPException: 500 if there's an execution error or internal server error.
        
    Example:
        ```
        POST /workflows/execute_node/node-456
        Content-Type: application/json
        
        {
            "id": "temp-workflow",
            "name": "Temporary Workflow",
            "schema": {
                "nodes": [
                    {
                        "id": "node-456",
                        "type": "filter",
                        "label": "Filter Node",
                        ...
                    }
                ],
                "connections": [...],
                "revision": "1.0"
            }
        }
        ```
        
    Response:
        ```json
        {
            "id": "temp-workflow",
            "name": "Temporary Workflow",
            "schema": {
                "nodes": [...],
                "connections": [...],
                "revision": "1.0"
            }
        }
        ```
    """
    try:
        logger.info(f"User {current_user.username} executing node {node_id} from workflow JSON: {workflow.name}")
        
        if node_id not in [node.id for node in workflow.pschema.nodes]:
            raise HTTPException(status_code=404, detail="Node not found in workflow")
        
        result = await import_and_execute_workflow(workflow, node_id=node_id, sample=True, current_user=current_user)
        logger.info(f"User {current_user.username} successfully executed node {node_id} from workflow JSON")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error executing node from JSON: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute node")


async def import_and_execute_workflow(
    workflow_data: IProject, 
    node_id: Optional[str] = None, 
    sample: Optional[bool] = False,
    current_user: Optional[User] = None
) -> IProject:
    """
    Import and execute workflow.
    
    Helper function that handles the actual workflow execution logic.
    
    Args:
        workflow_data (IProject): The workflow to execute.
        node_id (Optional[str]): Specific node to execute (if None, executes all).
        sample (Optional[bool]): Whether to limit execution to sample data.
        current_user (Optional[User]): The user executing the workflow (for context).
        
    Returns:
        IProject: The updated workflow with execution results.
        
    Raises:
        HTTPException: 500 if execution fails.
    """
    try:
        # Set execution context
        if current_user:
            ExecutionContext.set_user(current_user)
            logger.info(f"Executing workflow: {workflow_data.name} by user {current_user.username} (Node: {node_id}, Sample: {sample})")
        else:
            logger.info(f"Executing workflow: {workflow_data.name} (Node: {node_id}, Sample: {sample})")
        
        ExecutionContext.set_workflow(workflow_data)
        
        workflow = Workflow()
        workflow.import_project(workflow_data)
        await workflow.execute_workflow(node_id=node_id, sample=sample)
        
        result = workflow.export_updated_project()
        logger.info(f"Successfully executed workflow: {workflow_data.name}")
        return result
    except Exception as e:
        logger.exception(f"Error executing workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")
    finally:
        # Clear execution context to prevent leakage
        ExecutionContext.clear()
        logger.debug("Execution context cleared")