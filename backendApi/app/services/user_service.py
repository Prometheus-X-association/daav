import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException, status
from beanie.operators import In

from app.models.interface.user_interface import (
    User, UserCreate, UserUpdate, UserResponse, UserConfig, UserConfigUpdate
)
from app.models.interface.dataset_interface import Dataset
from app.models.interface.workflow_interface import IProject
from app.utils.auth_utils import get_password_hash, verify_password
from app.utils.singleton import SingletonMeta
from app.enums.user_role import UserRole

logger = logging.getLogger(__name__)


class UserService(metaclass=SingletonMeta):
    """Service for managing users"""
    
    def __init__(self):
        logger.info("UserService initialized")
    
    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user
        
        Args:
            user_data: User creation data
            
        Returns:
            User: The created user
            
        Raises:
            HTTPException: If username or email already exists
        """
        try:
            # Check if username already exists
            existing_user = await User.find_one(User.username == user_data.username.lower())
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )
            
            # Check if email already exists
            existing_email = await User.find_one(User.email == user_data.email)
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
            
            # Hash password
            hashed_password = get_password_hash(user_data.password)
            
            # Create user
            user = User(
                username=user_data.username.lower(),
                email=user_data.email,
                full_name=user_data.full_name,
                hashed_password=hashed_password,
                role=user_data.role,
                config=UserConfig()
            )
            
            await user.insert()
            logger.info(f"User created: {user.username} (ID: {user.id})")
            return user
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            return await User.get(user_id)
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            return await User.find_one(User.username == username.lower())
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            return await User.find_one(User.email == email)
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    async def get_user_by_username_or_email(self, identifier: str) -> Optional[User]:
        """Get user by username or email"""
        try:
            # Try username first
            user = await self.get_user_by_username(identifier)
            if user:
                return user
            
            # Try email
            return await self.get_user_by_email(identifier)
        except Exception as e:
            logger.error(f"Error getting user by identifier {identifier}: {e}")
            return None
    
    async def get_all_users(self) -> List[User]:
        """Get all users"""
        try:
            return await User.find_all().to_list()
        except Exception as e:
            logger.error(f"Error getting all users: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve users"
            )
    
    async def update_user(self, user_id: str, user_data: UserUpdate, current_user: User) -> User:
        """
        Update user information
        
        Args:
            user_id: ID of user to update
            user_data: Update data
            current_user: User making the request
            
        Returns:
            User: Updated user
            
        Raises:
            HTTPException: If user not found or unauthorized
        """
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Only admin can update other users, users can only update themselves
            if current_user.role != UserRole.ADMIN and current_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this user"
                )
            
            # Update fields
            update_data = user_data.model_dump(exclude_unset=True)
            
            # Hash password if provided
            if "password" in update_data and update_data["password"]:
                update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
            
            # Only admin can change role
            if "role" in update_data and current_user.role != UserRole.ADMIN:
                del update_data["role"]
            
            # Update timestamp
            update_data["updated_at"] = datetime.now(timezone.utc)
            
            # Apply updates
            for key, value in update_data.items():
                setattr(user, key, value)
            
            await user.save()
            logger.info(f"User updated: {user.username} (ID: {user_id})")
            return user
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )
    
    async def delete_user(self, user_id: str, current_user: User) -> bool:
        """
        Delete a user (admin only)
        
        Args:
            user_id: ID of user to delete
            current_user: User making the request
            
        Returns:
            bool: True if deleted
            
        Raises:
            HTTPException: If unauthorized or user not found
        """
        try:
            if current_user.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins can delete users"
                )
            
            user = await self.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Don't allow deleting the last admin
            if user.role == UserRole.ADMIN:
                admin_count = await User.find(User.role == UserRole.ADMIN).count()
                if admin_count <= 1:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot delete the last admin user"
                    )
            
            await user.delete()
            logger.info(f"User deleted: {user.username} (ID: {user_id})")
            return True
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )
    
    async def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp"""
        try:
            user = await self.get_user_by_id(user_id)
            if user:
                user.last_login = datetime.now(timezone.utc)
                await user.save()
        except Exception as e:
            logger.error(f"Error updating last login for user {user_id}: {e}")
    
    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """
        Change user password
        
        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            bool: True if password changed successfully
            
        Raises:
            HTTPException: If current password is incorrect
        """
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Verify current password
            if not verify_password(current_password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
            
            # Hash and set new password
            user.hashed_password = get_password_hash(new_password)
            user.updated_at = datetime.now(timezone.utc)
            await user.save()
            
            logger.info(f"Password changed for user: {user.username}")
            return True
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error changing password for user {user_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password"
            )
    
    async def update_user_config(self, user_id: str, config_update: UserConfigUpdate) -> User:
        """
        Update user configuration (credentials and settings)
        
        Args:
            user_id: User ID
            config_update: Configuration updates
            
        Returns:
            User: Updated user
        """
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Update credentials if provided
            if config_update.credentials is not None:
                user.config.credentials.update(config_update.credentials)
            
            # Update settings if provided
            if config_update.settings is not None:
                user.config.settings.update(config_update.settings)
            
            user.updated_at = datetime.now(timezone.utc)
            await user.save()
            
            logger.info(f"Configuration updated for user: {user.username}")
            return user
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating config for user {user_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user configuration"
            )
    
    async def ensure_admin_exists(self) -> User:
        """
        Ensure at least one admin user exists
        Creates default admin if no users exist
        
        Returns:
            User: Admin user
        """
        try:
            # Check if any users exist
            user_count = await User.count()
            
            if user_count == 0:
                logger.info("No users found, creating default admin user")
                
                # Create default admin
                admin_data = UserCreate(
                    username="admin",
                    email="admin@example.com",
                    full_name="System Administrator",
                    password="Admin123!",  # Must be changed on first login
                    role=UserRole.ADMIN
                )
                
                admin = await self.create_user(admin_data)
                logger.warning("⚠️ DEFAULT ADMIN CREATED - Username: admin, Password: Admin123! - CHANGE THIS IMMEDIATELY!")
                return admin
            
            # Check if admin exists
            admin = await User.find_one(User.role == UserRole.ADMIN)
            if not admin:
                logger.warning("No admin user found but users exist - this shouldn't happen")
                # Find first user and make them admin
                first_user = await User.find_one()
                if first_user:
                    first_user.role = UserRole.ADMIN
                    await first_user.save()
                    logger.info(f"Made user {first_user.username} an admin")
                    return first_user
            
            return admin
        
        except Exception as e:
            logger.error(f"Error ensuring admin exists: {e}", exc_info=True)
            raise
    
    async def can_access_dataset(self, user: User, dataset_id: str) -> bool:
        """
        Check if user can access a dataset
        
        Args:
            user: The user
            dataset_id: Dataset ID
            
        Returns:
            bool: True if user can access
        """
        # Admin can access everything
        if user.role == UserRole.ADMIN:
            return True
        
        # User can access owned datasets
        if dataset_id in user.owned_datasets:
            return True
        
        # User can access shared datasets
        if dataset_id in user.shared_datasets:
            return True
        
        return False
    
    async def can_modify_dataset(self, user: User, dataset_id: str) -> bool:
        """
        Check if user can modify/delete a dataset
        Only owner can modify
        
        Args:
            user: The user
            dataset_id: Dataset ID
            
        Returns:
            bool: True if user can modify
        """
        # Admin can modify everything
        if user.role == UserRole.ADMIN:
            return True
        
        # Only owner can modify
        return dataset_id in user.owned_datasets
    
    async def can_access_workflow(self, user: User, workflow_id: str) -> bool:
        """
        Check if user can access a workflow
        
        Args:
            user: The user
            workflow_id: Workflow ID
            
        Returns:
            bool: True if user can access
        """
        # Admin can access everything
        if user.role == UserRole.ADMIN:
            return True
        
        # User can access owned workflows
        if workflow_id in user.owned_workflows:
            return True
        
        # User can access shared workflows
        if workflow_id in user.shared_workflows:
            return True
        
        return False
    
    async def can_modify_workflow(self, user: User, workflow_id: str) -> bool:
        """
        Check if user can modify/delete a workflow
        Only owner can modify
        
        Args:
            user: The user
            workflow_id: Workflow ID
            
        Returns:
            bool: True if user can modify
        """
        # Admin can modify everything
        if user.role == UserRole.ADMIN:
            return True
        
        # Only owner can modify
        return workflow_id in user.owned_workflows
    
    async def share_dataset(self, owner_id: str, dataset_id: str, target_user_id: str) -> bool:
        """Share a dataset with another user"""
        try:
            owner = await self.get_user_by_id(owner_id)
            target_user = await self.get_user_by_id(target_user_id)
            
            if not owner or not target_user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Check if owner owns the dataset
            if dataset_id not in owner.owned_datasets and owner.role != UserRole.ADMIN:
                raise HTTPException(status_code=403, detail="Not authorized to share this dataset")
            
            # Get the dataset
            dataset = await Dataset.get(dataset_id)
            if not dataset:
                raise HTTPException(status_code=404, detail="Dataset not found")
            
            # 1. Update User side
            if dataset_id not in target_user.shared_datasets:
                target_user.shared_datasets.append(dataset_id)
                await target_user.save()
            
            # 2. Update Dataset side
            if target_user_id not in dataset.shared_with:
                dataset.shared_with.append(target_user_id)
                await dataset.save()
            
            logger.info(f"Dataset {dataset_id} shared with user {target_user.username} (bidirectional)")
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error sharing dataset: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to share dataset")
    
    async def unshare_dataset(self, owner_id: str, dataset_id: str, target_user_id: str) -> bool:
        """Unshare a dataset from a user"""
        try:
            owner = await self.get_user_by_id(owner_id)
            target_user = await self.get_user_by_id(target_user_id)
            
            if not owner or not target_user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Check if owner owns the dataset
            if dataset_id not in owner.owned_datasets and owner.role != UserRole.ADMIN:
                raise HTTPException(status_code=403, detail="Not authorized to unshare this dataset")
            
            # Get the dataset
            dataset = await Dataset.get(dataset_id)
            if not dataset:
                raise HTTPException(status_code=404, detail="Dataset not found")
            
            # 1. Update User side
            if dataset_id in target_user.shared_datasets:
                target_user.shared_datasets.remove(dataset_id)
                await target_user.save()
            
            # 2. Update Dataset side
            if target_user_id in dataset.shared_with:
                dataset.shared_with.remove(target_user_id)
                await dataset.save()
            
            logger.info(f"Dataset {dataset_id} unshared from user {target_user.username} (bidirectional)")
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error unsharing dataset: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to unshare dataset")
    
    async def share_workflow(self, owner_id: str, workflow_id: str, target_user_id: str) -> bool:
        """Share a workflow with another user"""
        try:
            owner = await self.get_user_by_id(owner_id)
            target_user = await self.get_user_by_id(target_user_id)
            
            if not owner or not target_user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Check if owner owns the workflow
            if workflow_id not in owner.owned_workflows and owner.role != UserRole.ADMIN:
                raise HTTPException(status_code=403, detail="Not authorized to share this workflow")
            
            # Get the workflow
            workflow = await IProject.get(workflow_id)
            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            # 1. Update User side
            if workflow_id not in target_user.shared_workflows:
                target_user.shared_workflows.append(workflow_id)
                await target_user.save()
            
            # 2. Update Workflow side
            if target_user_id not in workflow.shared_with:
                workflow.shared_with.append(target_user_id)
                await workflow.save()
            
            logger.info(f"Workflow {workflow_id} shared with user {target_user.username} (bidirectional)")
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error sharing workflow: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to share workflow")
    
    async def unshare_workflow(self, owner_id: str, workflow_id: str, target_user_id: str) -> bool:
        """Unshare a workflow from a user"""
        try:
            owner = await self.get_user_by_id(owner_id)
            target_user = await self.get_user_by_id(target_user_id)
            
            if not owner or not target_user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Check if owner owns the workflow
            if workflow_id not in owner.owned_workflows and owner.role != UserRole.ADMIN:
                raise HTTPException(status_code=403, detail="Not authorized to unshare this workflow")
            
            # Get the workflow
            workflow = await IProject.get(workflow_id)
            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            # 1. Update User side
            if workflow_id in target_user.shared_workflows:
                target_user.shared_workflows.remove(workflow_id)
                await target_user.save()
            
            # 2. Update Workflow side
            if target_user_id in workflow.shared_with:
                workflow.shared_with.remove(target_user_id)
                await workflow.save()
            
            logger.info(f"Workflow {workflow_id} unshared from user {target_user.username} (bidirectional)")
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error unsharing workflow: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to unshare workflow")
    
    async def assign_dataset_ownership(self, user: User, dataset: Dataset) -> None:
        """
        Assign ownership of a dataset to a user - BIDIRECTIONAL
        Called when creating a new dataset
        """
        try:
            # 1. Update Dataset side
            dataset.owner_id = user.id
            await dataset.save()
            
            # 2. Update User side
            if dataset.id not in user.owned_datasets:
                user.owned_datasets.append(dataset.id)
                await user.save()
            
            logger.info(f"Dataset {dataset.id} ownership assigned to user {user.username}")
            
        except Exception as e:
            logger.error(f"Error assigning dataset ownership: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to assign dataset ownership")
    
    async def assign_workflow_ownership(self, user: User, workflow: IProject) -> None:
        """
        Assign ownership of a workflow to a user - BIDIRECTIONAL
        Called when creating a new workflow
        """
        try:
            # 1. Update Workflow side
            workflow.owner_id = user.id
            await workflow.save()
            
            # 2. Update User side
            if workflow.id not in user.owned_workflows:
                user.owned_workflows.append(workflow.id)
                await user.save()
            
            logger.info(f"Workflow {workflow.id} ownership assigned to user {user.username}")
            
        except Exception as e:
            logger.error(f"Error assigning workflow ownership: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to assign workflow ownership")
    
    async def remove_dataset_ownership(self, dataset_id: str) -> None:
        """
        Remove all ownership and sharing relations when deleting a dataset - BIDIRECTIONAL
        Called before deleting a dataset
        """
        try:
            # Get the dataset
            dataset = await Dataset.get(dataset_id)
            if not dataset:
                return  # Already deleted
            
            # 1. Remove from owner's owned_datasets
            if dataset.owner_id:
                owner = await self.get_user_by_id(dataset.owner_id)
                if owner and dataset_id in owner.owned_datasets:
                    owner.owned_datasets.remove(dataset_id)
                    await owner.save()
            
            # 2. Remove from all shared users' shared_datasets
            for user_id in dataset.shared_with:
                user = await self.get_user_by_id(user_id)
                if user and dataset_id in user.shared_datasets:
                    user.shared_datasets.remove(dataset_id)
                    await user.save()
            
            logger.info(f"Dataset {dataset_id} ownership and sharing removed (bidirectional)")
            
        except Exception as e:
            logger.error(f"Error removing dataset ownership: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to remove dataset ownership")
    
    async def remove_workflow_ownership(self, workflow_id: str) -> None:
        """
        Remove all ownership and sharing relations when deleting a workflow - BIDIRECTIONAL
        Called before deleting a workflow
        """
        try:
            # Get the workflow
            workflow = await IProject.get(workflow_id)
            if not workflow:
                return  # Already deleted
            
            # 1. Remove from owner's owned_workflows
            if workflow.owner_id:
                owner = await self.get_user_by_id(workflow.owner_id)
                if owner and workflow_id in owner.owned_workflows:
                    owner.owned_workflows.remove(workflow_id)
                    await owner.save()
            
            # 2. Remove from all shared users' shared_workflows
            for user_id in workflow.shared_with:
                user = await self.get_user_by_id(user_id)
                if user and workflow_id in user.shared_workflows:
                    user.shared_workflows.remove(workflow_id)
                    await user.save()
            
            logger.info(f"Workflow {workflow_id} ownership and sharing removed (bidirectional)")
            
        except Exception as e:
            logger.error(f"Error removing workflow ownership: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to remove workflow ownership")
        

    async def get_user_from_workflow(self, workflow: IProject) -> Optional[User]:
        """Get the owner user of a workflow.
        
        Returns None if the workflow has no owner (public workflow).
        Raises on DB/service errors so callers can handle them explicitly
        instead of silently treating the workflow as public.
        """
        if not workflow.owner_id:
            return None
        return await self.get_user_by_id(workflow.owner_id)
