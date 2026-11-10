import logging
from typing import List, Optional, Union
from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.models.interface.workflow_interface import IProject
from app.models.interface.user_interface import User
from app.enums.user_role import UserRole
from app.services.user_service import UserService
from app.utils.singleton import SingletonMeta
import uuid

logger = logging.getLogger(__name__)

class WorkflowService(metaclass=SingletonMeta):
    
    def __init__(self):
        # Import user_service for permission checks        
        self.user_service = UserService()
        logger.info("WorkflowService initialized")

    async def get_workflows(self, user: Optional[User] = None) -> List[IProject]:
        """
        Retrieve workflows with optional permission filtering.
        
        Args:
            user: User requesting access. If None, returns all workflows (for M2M calls)
            
        Returns:
            List of IProject objects
            
        Raises:
            HTTPException: 500 on error
        """
        try:
            if user:
                logger.info(f"Getting workflows for user: {user.username}")

                # Admin can see all workflows
                if user.role == UserRole.ADMIN:
                    workflows = await IProject.find_all().to_list()
                    logger.info(f"Admin retrieved {len(workflows)} workflows")
                    return workflows
                
                # Regular user - filter by owned + shared
                workflow_ids = user.owned_workflows + user.shared_workflows
                if not workflow_ids:
                    logger.info(f"User {user.username} has no workflows")
                    return []
                
                workflows = await IProject.find({"_id": {"$in": workflow_ids}}).to_list()
                logger.info(f"User {user.username} retrieved {len(workflows)} workflows")
                return workflows
            else:
                # System call - return all workflows
                logger.info("System getting all workflows (no permission filtering)")
                workflows = await IProject.find_all().to_list()
                logger.info(f"System retrieved {len(workflows)} workflows")
                return workflows
            
        except Exception as e:
            logger.error(f"Error retrieving workflows: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to retrieve workflows")

    async def get_workflow(self, workflow_id: str, user: Optional[User] = None) -> IProject:
        """
        Retrieve a workflow by its ID with optional permission check.
        
        Args:
            workflow_id: Workflow ID to retrieve
            user: User requesting access. If None, permission check is skipped (for M2M calls)
            
        Returns:
            IProject object
            
        Raises:
            HTTPException: 404 if not found, 403 if access denied, 500 on error
        """
        try:
            if user:
                logger.info(f"User {user.username} fetching workflow with ID: {workflow_id}")
            else:
                logger.info(f"System fetching workflow with ID: {workflow_id} (no permission check)")
            
            # Get workflow
            workflow = await IProject.get(workflow_id)
            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            # Only check permissions if user is provided
            if user:
                can_access = self.user_service.can_access_workflow(user, workflow_id)
                if not can_access:
                    logger.warning(f"User {user.username} denied access to workflow {workflow_id}")
                    raise HTTPException(status_code=403, detail="Access denied")
                logger.info(f"User {user.username} successfully accessed workflow: {workflow.name}")
            else:
                logger.info(f"System successfully accessed workflow: {workflow.name}")
            
            return workflow
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving workflow {workflow_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")

    async def create_workflow(self, workflow_data: IProject, user: User) -> IProject:
        """Create a new workflow with ownership assignment"""
        try:
            logger.info(f"User {user.username} creating new workflow: {workflow_data.name}")
            
            # Use the provided workflow instance directly (already validated by FastAPI)
            workflow = workflow_data
            
            # Generate UUID if not provided
            if not workflow.id:
                import uuid
                workflow.id = str(uuid.uuid4())
            
            workflow.created_at = datetime.now(timezone.utc)
            workflow.updated_at = datetime.now(timezone.utc)
            
            # Save to MongoDB first
            await workflow.insert()
            
            # Assign ownership (bidirectional)
            await self.user_service.assign_workflow_ownership(user, workflow)
            
            logger.info(f"User {user.username} successfully created workflow: {workflow.name} (ID: {workflow.id})")
            return workflow
            
        except Exception as e:
            logger.error(f"Error creating workflow: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to create workflow")

    async def update_workflow(self, workflow_updates: IProject, user: User) -> IProject:
        """
        Update an existing workflow with permission check.
        
        Only updates fields that were explicitly provided in the original request.
        System fields (id, created_at, owner_id) are never overwritten.
        
        Args:
            workflow_updates: IProject with only the fields to update (from FastAPI validation)
            user: User performing the update
            
        Returns:
            Updated IProject object
        """
        try:
            workflow_id = workflow_updates.id
            if not workflow_id:
                raise HTTPException(status_code=400, detail="Workflow ID is required")
            
            logger.info(f"User {user.username} updating workflow with ID: {workflow_id}")
            
            # Check permission using user_service
            can_modify = self.user_service.can_modify_workflow(user, workflow_id)
            if not can_modify:
                logger.warning(f"User {user.username} denied permission to update workflow {workflow_id}")
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Find existing workflow
            existing_workflow = await IProject.get(workflow_id)
            if not existing_workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            # Get only the fields that were explicitly set in the request
            # exclude_unset=True means only fields present in original JSON are included
            updated_fields = workflow_updates.model_dump(exclude_unset=True)
            
            # System fields are never overwritten during updates
            system_fields = {'id', 'created_at', 'owner_id'}
            
            for key, value in updated_fields.items():
                if (hasattr(existing_workflow, key) and 
                    key not in system_fields):
                    setattr(existing_workflow, key, value)
            
            existing_workflow.updated_at = datetime.now(timezone.utc)
            
            # Save changes
            await existing_workflow.replace()
            logger.info(f"User {user.username} successfully updated workflow: {existing_workflow.name} (ID: {workflow_id})")
            return existing_workflow
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating workflow {workflow_updates.id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to update workflow")

    async def delete_workflow(self, workflow_id: str, user: User) -> bool:
        """Delete a workflow with permission check"""
        try:
            logger.info(f"User {user.username} attempting to delete workflow with ID: {workflow_id}")
            
            # Check permission using user_service
            can_modify = self.user_service.can_modify_workflow(user, workflow_id)
            if not can_modify:
                logger.warning(f"User {user.username} denied permission to delete workflow {workflow_id}")
                raise HTTPException(status_code=403, detail="Access denied")
            
            workflow = await IProject.get(workflow_id)
            if not workflow:
                logger.warning(f"Attempted to delete non-existent workflow: {workflow_id}")
                return False
            
            workflow_name = workflow.name
            
            # Remove ownership relations BEFORE deleting
            await self.user_service.remove_workflow_ownership(workflow_id)
            
            await workflow.delete()
            
            logger.info(f"User {user.username} successfully deleted workflow: {workflow_name} (ID: {workflow_id})")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting workflow {workflow_id}: {e}", exc_info=True)
            return False

    async def workflow_exists(self, workflow_id: str) -> bool:
        """Check if a workflow exists"""
        try:
            workflow = await IProject.get(workflow_id)
            return workflow is not None
        except Exception:
            return False

# Singleton instance
workflow_service = WorkflowService()