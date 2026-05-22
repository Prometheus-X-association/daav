"""
Tests for UserService

This module tests all user management functionality including:
- User CRUD operations
- Permission checks
- Resource ownership and sharing
- Password management
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from fastapi import HTTPException

from app.services.user_service import UserService
from app.models.interface.user_interface import (
    User, UserCreate, UserUpdate, UserConfig, UserConfigUpdate
)
from app.models.interface.dataset_interface import Dataset
from app.models.interface.workflow_interface import IProject
from app.enums.user_role import UserRole


@pytest.fixture
def user_service_instance():
    """Get UserService instance (singleton)"""
    return UserService()


@pytest.fixture
def sample_user_create():
    """Sample user creation data"""
    return UserCreate(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        password="Test123!",
        role=UserRole.USER
    )


@pytest.fixture
def sample_user_update():
    """Sample user update data"""
    return UserUpdate(
        full_name="Updated Name",
        email="updated@example.com"
    )


# ============================================
# CREATE USER TESTS
# ============================================

@pytest.mark.asyncio
async def test_create_user_success(user_service_instance, sample_user_create):
    """Test successful user creation"""
    with patch('app.services.user_service.get_password_hash', return_value="hashed_password"):
        result = await user_service_instance.create_user(sample_user_create)
        
        assert result.username == sample_user_create.username.lower()
        assert result.email == sample_user_create.email
        assert result.full_name == sample_user_create.full_name
        assert result.role == sample_user_create.role
        assert result.id is not None


@pytest.mark.asyncio
async def test_create_user_duplicate_username(user_service_instance, sample_user_create):
    """Test user creation with duplicate username"""
    # First create a user
    with patch('app.services.user_service.get_password_hash', return_value="hashed_password"):
        await user_service_instance.create_user(sample_user_create)
        
        # Try to create another user with same username
        with pytest.raises(HTTPException) as exc_info:
            await user_service_instance.create_user(sample_user_create)
        
        assert exc_info.value.status_code == 400
        assert "Username already exists" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_user_duplicate_email(user_service_instance, sample_user_create):
    """Test user creation with duplicate email"""
    # First create a user
    with patch('app.services.user_service.get_password_hash', return_value="hashed_password"):
        await user_service_instance.create_user(sample_user_create)
        
        # Try to create another user with same email but different username
        duplicate_email = UserCreate(
            username="different_user",
            email=sample_user_create.email,  # Same email
            full_name="Different User",
            password="Test123!",
            role=UserRole.USER
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service_instance.create_user(duplicate_email)
        
        assert exc_info.value.status_code == 400
        assert "Email already exists" in str(exc_info.value.detail)


# ============================================
# GET USER TESTS
# ============================================

@pytest.mark.asyncio
async def test_get_user_by_id_success(user_service_instance, mock_user):
    """Test getting user by ID"""
    with patch.object(User, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_user
        
        result = await user_service_instance.get_user_by_id(str(mock_user.id))
        
        assert result == mock_user
        mock_get.assert_called_once_with(str(mock_user.id))


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(user_service_instance):
    """Test getting non-existent user by ID"""
    with patch.object(User, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        result = await user_service_instance.get_user_by_id("nonexistent_id")
        
        assert result is None


@pytest.mark.asyncio
async def test_get_user_by_username_success(user_service_instance, sample_user_create):
    """Test getting user by username"""
    # First create a user
    with patch('app.services.user_service.get_password_hash', return_value="hashed_password"):
        created_user = await user_service_instance.create_user(sample_user_create)
        
        # Now retrieve it by username
        result = await user_service_instance.get_user_by_username(created_user.username)
        
        assert result is not None
        assert result.username == created_user.username
        assert result.id == created_user.id


@pytest.mark.asyncio
async def test_get_user_by_email_success(user_service_instance, sample_user_create):
    """Test getting user by email"""
    # First create a user
    with patch('app.services.user_service.get_password_hash', return_value="hashed_password"):
        created_user = await user_service_instance.create_user(sample_user_create)
        
        # Now retrieve it by email
        result = await user_service_instance.get_user_by_email(created_user.email)
        
        assert result is not None
        assert result.email == created_user.email
        assert result.id == created_user.id


@pytest.mark.asyncio
async def test_get_user_by_username_or_email_username(user_service_instance, mock_user):
    """Test getting user by username or email (username found)"""
    with patch.object(user_service_instance, 'get_user_by_username', new_callable=AsyncMock) as mock_get_username:
        mock_get_username.return_value = mock_user
        
        result = await user_service_instance.get_user_by_username_or_email(mock_user.username)
        
        assert result == mock_user
        mock_get_username.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_username_or_email_email(user_service_instance, mock_user):
    """Test getting user by username or email (email found)"""
    with patch.object(user_service_instance, 'get_user_by_username', new_callable=AsyncMock) as mock_get_username, \
         patch.object(user_service_instance, 'get_user_by_email', new_callable=AsyncMock) as mock_get_email:
        mock_get_username.return_value = None
        mock_get_email.return_value = mock_user
        
        result = await user_service_instance.get_user_by_username_or_email(mock_user.email)
        
        assert result == mock_user
        mock_get_email.assert_called_once()


@pytest.mark.asyncio
async def test_get_all_users_success(user_service_instance, mock_user):
    """Test getting all users"""
    users_list = [mock_user, mock_user]
    
    with patch.object(User, 'find_all') as mock_find_all:
        mock_find_all.return_value.to_list = AsyncMock(return_value=users_list)
        
        result = await user_service_instance.get_all_users()
        
        assert result == users_list
        assert len(result) == 2


# ============================================
# UPDATE USER TESTS
# ============================================

@pytest.mark.asyncio
async def test_update_user_success_own_profile(user_service_instance, mock_user, sample_user_update):
    """Test user updating own profile"""
    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get, \
         patch.object(mock_user, 'save', new_callable=AsyncMock) as mock_save:
        mock_get.return_value = mock_user
        
        result = await user_service_instance.update_user(
            str(mock_user.id),
            sample_user_update,
            mock_user  # Current user is same as target
        )
        
        assert result.full_name == sample_user_update.full_name
        assert result.email == sample_user_update.email
        mock_save.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_success_admin(user_service_instance, mock_user, mock_admin_user, sample_user_update):
    """Test admin updating another user"""
    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get, \
         patch.object(mock_user, 'save', new_callable=AsyncMock) as mock_save:
        mock_get.return_value = mock_user
        
        result = await user_service_instance.update_user(
            str(mock_user.id),
            sample_user_update,
            mock_admin_user  # Admin user
        )
        
        assert result.full_name == sample_user_update.full_name
        mock_save.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_forbidden_non_admin(user_service_instance, mock_user):
    """Test non-admin trying to update another user"""
    other_user = Mock(spec=User)
    other_user.id = "other_user_id"
    other_user.role = UserRole.USER
    
    sample_update = UserUpdate(full_name="Hacker")
    
    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_user
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service_instance.update_user(
                str(mock_user.id),
                sample_update,
                other_user  # Different user, not admin
            )
        
        assert exc_info.value.status_code == 403
        assert "Not authorized" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_user_not_found(user_service_instance, mock_user, sample_user_update):
    """Test updating non-existent user"""
    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service_instance.update_user(
                "nonexistent_id",
                sample_user_update,
                mock_user
            )
        
        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_user_with_password(user_service_instance, mock_user):
    """Test updating user with password change"""
    update_data = UserUpdate(password="NewPassword123!")
    
    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get, \
         patch.object(mock_user, 'save', new_callable=AsyncMock) as mock_save, \
         patch('app.services.user_service.get_password_hash', return_value="new_hashed_password") as mock_hash:
        mock_get.return_value = mock_user
        
        result = await user_service_instance.update_user(
            str(mock_user.id),
            update_data,
            mock_user
        )
        
        assert result.hashed_password == "new_hashed_password"
        mock_hash.assert_called_once_with("NewPassword123!")
        mock_save.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_role_non_admin_denied(user_service_instance, mock_user):
    """Test non-admin cannot change role"""
    update_data = UserUpdate(role=UserRole.ADMIN)
    
    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get, \
         patch.object(mock_user, 'save', new_callable=AsyncMock) as mock_save:
        mock_get.return_value = mock_user
        
        result = await user_service_instance.update_user(
            str(mock_user.id),
            update_data,
            mock_user  # Non-admin user
        )
        
        # Role should not change
        assert result.role == UserRole.USER
        mock_save.assert_called_once()


# ============================================
# DELETE USER TESTS
# ============================================

@pytest.mark.asyncio
async def test_delete_user_success(user_service_instance, mock_user, mock_admin_user):
    """Test successful user deletion by admin"""
    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get, \
         patch.object(mock_user, 'delete', new_callable=AsyncMock) as mock_delete:
        mock_get.return_value = mock_user
        
        result = await user_service_instance.delete_user(
            str(mock_user.id),
            mock_admin_user
        )
        
        assert result is True
        mock_delete.assert_called_once()


@pytest.mark.asyncio
async def test_delete_user_forbidden_non_admin(user_service_instance, mock_user):
    """Test non-admin cannot delete users"""
    other_user = Mock(spec=User)
    other_user.id = "other_user_id"
    other_user.role = UserRole.USER
    
    with pytest.raises(HTTPException) as exc_info:
        await user_service_instance.delete_user(
            str(mock_user.id),
            other_user
        )
    
    assert exc_info.value.status_code == 403
    assert "Only admins can delete users" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_delete_user_not_found(user_service_instance, mock_admin_user):
    """Test deleting non-existent user"""
    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service_instance.delete_user(
                "nonexistent_id",
                mock_admin_user
            )
        
        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_delete_last_admin_forbidden(user_service_instance, sample_user_create):
    """Test cannot delete last admin user"""
    # Create an admin user in the database
    admin_create = UserCreate(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        password="Admin123!",
        role=UserRole.ADMIN
    )
    
    with patch('app.services.user_service.get_password_hash', return_value="hashed_password"):
        admin_user = await user_service_instance.create_user(admin_create)
        
        # Try to delete the only admin
        with pytest.raises(HTTPException) as exc_info:
            await user_service_instance.delete_user(str(admin_user.id), admin_user)
        
        assert exc_info.value.status_code == 400
        assert "Cannot delete the last admin user" in str(exc_info.value.detail)


# ============================================
# PASSWORD MANAGEMENT TESTS
# ============================================

@pytest.mark.asyncio
async def test_update_last_login_success(user_service_instance, mock_user):
    """Test updating user's last login timestamp"""
    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get, \
         patch.object(mock_user, 'save', new_callable=AsyncMock) as mock_save:
        mock_get.return_value = mock_user
        
        await user_service_instance.update_last_login(str(mock_user.id))
        
        assert mock_user.last_login is not None
        mock_save.assert_called_once()


@pytest.mark.asyncio
async def test_change_password_success(user_service_instance, mock_user):
    """Test successful password change"""
    current_password = "OldPassword123!"
    new_password = "NewPassword456!"
    original_hashed_password = mock_user.hashed_password
    
    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get, \
         patch.object(mock_user, 'save', new_callable=AsyncMock) as mock_save, \
         patch('app.services.user_service.verify_password', return_value=True) as mock_verify, \
         patch('app.services.user_service.get_password_hash', return_value="new_hashed") as mock_hash:
        mock_get.return_value = mock_user
        
        result = await user_service_instance.change_password(
            str(mock_user.id),
            current_password,
            new_password
        )
        
        assert result is True
        assert mock_user.hashed_password == "new_hashed"
        mock_verify.assert_called_once_with(current_password, original_hashed_password)
        mock_hash.assert_called_once_with(new_password)
        mock_save.assert_called_once()


@pytest.mark.asyncio
async def test_change_password_incorrect_current(user_service_instance, mock_user):
    """Test password change with incorrect current password"""
    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get, \
         patch('app.services.user_service.verify_password', return_value=False):
        mock_get.return_value = mock_user
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service_instance.change_password(
                str(mock_user.id),
                "WrongPassword",
                "NewPassword456!"
            )
        
        assert exc_info.value.status_code == 400
        assert "Current password is incorrect" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_change_password_user_not_found(user_service_instance):
    """Test password change for non-existent user"""
    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service_instance.change_password(
                "nonexistent_id",
                "OldPassword123!",
                "NewPassword456!"
            )
        
        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)


# ============================================
# USER CONFIG TESTS
# ============================================

@pytest.mark.asyncio
async def test_update_user_config_success(user_service_instance, mock_user):
    """Test updating user configuration"""
    # Properly setup mock_user.config
    mock_user.config = Mock(spec=UserConfig)
    mock_user.config.credentials = {}
    mock_user.config.settings = {}
    
    config_update = UserConfigUpdate(
        credentials={"api_key": "new_key"},
        settings={"theme": "dark"}
    )
    
    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get, \
         patch.object(mock_user, 'save', new_callable=AsyncMock) as mock_save:
        mock_get.return_value = mock_user
        
        result = await user_service_instance.update_user_config(
            str(mock_user.id),
            config_update
        )
        
        assert result.config.credentials["api_key"] == "new_key"
        assert result.config.settings["theme"] == "dark"
        mock_save.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_config_user_not_found(user_service_instance):
    """Test updating config for non-existent user"""
    config_update = UserConfigUpdate(credentials={"test": "value"})
    
    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service_instance.update_user_config(
                "nonexistent_id",
                config_update
            )
        
        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)


# ============================================
# PERMISSION TESTS
# ============================================

@pytest.mark.asyncio
async def test_can_access_dataset_owner(user_service_instance, mock_user):
    """Test owner can access their dataset"""
    dataset_id = "dataset_123"
    mock_user.owned_datasets = [dataset_id]
    
    result = await user_service_instance.can_access_dataset(mock_user, dataset_id)
    
    assert result is True


@pytest.mark.asyncio
async def test_can_access_dataset_shared(user_service_instance, mock_user):
    """Test user can access shared dataset"""
    dataset_id = "dataset_123"
    mock_user.owned_datasets = []
    mock_user.shared_datasets = [dataset_id]
    
    result = await user_service_instance.can_access_dataset(mock_user, dataset_id)
    
    assert result is True


@pytest.mark.asyncio
async def test_can_access_dataset_admin(user_service_instance, mock_admin_user):
    """Test admin can access any dataset"""
    dataset_id = "dataset_123"
    mock_admin_user.owned_datasets = []
    mock_admin_user.shared_datasets = []
    
    result = await user_service_instance.can_access_dataset(mock_admin_user, dataset_id)
    
    assert result is True


@pytest.mark.asyncio
async def test_can_access_dataset_denied(user_service_instance, mock_user):
    """Test user cannot access unrelated dataset"""
    dataset_id = "dataset_123"
    mock_user.owned_datasets = []
    mock_user.shared_datasets = []
    mock_user.role = UserRole.USER
    
    result = await user_service_instance.can_access_dataset(mock_user, dataset_id)
    
    assert result is False


@pytest.mark.asyncio
async def test_can_modify_dataset_owner(user_service_instance, mock_user):
    """Test owner can modify their dataset"""
    dataset_id = "dataset_123"
    mock_user.owned_datasets = [dataset_id]
    
    result = await user_service_instance.can_modify_dataset(mock_user, dataset_id)
    
    assert result is True


@pytest.mark.asyncio
async def test_can_modify_dataset_shared_denied(user_service_instance, mock_user):
    """Test shared user cannot modify dataset"""
    dataset_id = "dataset_123"
    mock_user.owned_datasets = []
    mock_user.shared_datasets = [dataset_id]
    mock_user.role = UserRole.USER
    
    result = await user_service_instance.can_modify_dataset(mock_user, dataset_id)
    
    assert result is False


@pytest.mark.asyncio
async def test_can_access_workflow_owner(user_service_instance, mock_user):
    """Test owner can access their workflow"""
    workflow_id = "workflow_123"
    mock_user.owned_workflows = [workflow_id]
    
    result = await user_service_instance.can_access_workflow(mock_user, workflow_id)
    
    assert result is True


@pytest.mark.asyncio
async def test_can_modify_workflow_admin(user_service_instance, mock_admin_user):
    """Test admin can modify any workflow"""
    workflow_id = "workflow_123"
    mock_admin_user.owned_workflows = []
    
    result = await user_service_instance.can_modify_workflow(mock_admin_user, workflow_id)
    
    assert result is True


# ============================================
# SHARING TESTS - DATASETS
# ============================================

@pytest.mark.asyncio
async def test_share_dataset_success(user_service_instance, mock_user):
    """Test successfully sharing a dataset"""
    owner_id = "owner_123"
    dataset_id = "dataset_123"
    target_user_id = "target_456"
    
    owner = Mock(spec=User)
    owner.id = owner_id
    owner.role = UserRole.USER
    owner.owned_datasets = [dataset_id]
    
    target_user = Mock(spec=User)
    target_user.id = target_user_id
    target_user.username = "target_user"
    target_user.shared_datasets = []
    target_user.save = AsyncMock()
    
    dataset = Mock(spec=Dataset)
    dataset.id = dataset_id
    dataset.shared_with = []
    dataset.save = AsyncMock()
    
    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get_user, \
         patch.object(Dataset, 'get', new_callable=AsyncMock) as mock_get_dataset:
        mock_get_user.side_effect = [owner, target_user]
        mock_get_dataset.return_value = dataset
        
        result = await user_service_instance.share_dataset(owner_id, dataset_id, target_user_id)
        
        assert result is True
        assert dataset_id in target_user.shared_datasets
        assert target_user_id in dataset.shared_with
        target_user.save.assert_called_once()
        dataset.save.assert_called_once()


@pytest.mark.asyncio
async def test_share_dataset_unauthorized(user_service_instance):
    """Test sharing dataset without ownership"""
    owner_id = "owner_123"
    dataset_id = "dataset_123"
    target_user_id = "target_456"
    
    owner = Mock(spec=User)
    owner.id = owner_id
    owner.role = UserRole.USER
    owner.owned_datasets = []  # Doesn't own the dataset
    
    target_user = Mock(spec=User)
    target_user.id = target_user_id
    
    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get_user:
        mock_get_user.side_effect = [owner, target_user]
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service_instance.share_dataset(owner_id, dataset_id, target_user_id)
        
        assert exc_info.value.status_code == 403
        assert "Not authorized to share this dataset" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_unshare_dataset_success(user_service_instance):
    """Test successfully unsharing a dataset"""
    owner_id = "owner_123"
    dataset_id = "dataset_123"
    target_user_id = "target_456"
    
    owner = Mock(spec=User)
    owner.id = owner_id
    owner.role = UserRole.USER
    owner.owned_datasets = [dataset_id]
    
    target_user = Mock(spec=User)
    target_user.id = target_user_id
    target_user.username = "target_user"
    target_user.shared_datasets = [dataset_id]
    target_user.save = AsyncMock()
    
    dataset = Mock(spec=Dataset)
    dataset.id = dataset_id
    dataset.shared_with = [target_user_id]
    dataset.save = AsyncMock()
    
    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get_user, \
         patch.object(Dataset, 'get', new_callable=AsyncMock) as mock_get_dataset:
        mock_get_user.side_effect = [owner, target_user]
        mock_get_dataset.return_value = dataset
        
        result = await user_service_instance.unshare_dataset(owner_id, dataset_id, target_user_id)
        
        assert result is True
        assert dataset_id not in target_user.shared_datasets
        assert target_user_id not in dataset.shared_with
        target_user.save.assert_called_once()
        dataset.save.assert_called_once()


# ============================================
# SHARING TESTS - WORKFLOWS
# ============================================

@pytest.mark.asyncio
async def test_share_workflow_success(user_service_instance):
    """Test successfully sharing a workflow"""
    owner_id = "owner_123"
    workflow_id = "workflow_123"
    target_user_id = "target_456"
    
    owner = Mock(spec=User)
    owner.id = owner_id
    owner.role = UserRole.USER
    owner.owned_workflows = [workflow_id]
    
    target_user = Mock(spec=User)
    target_user.id = target_user_id
    target_user.username = "target_user"
    target_user.shared_workflows = []
    target_user.save = AsyncMock()
    
    workflow = Mock(spec=IProject)
    workflow.id = workflow_id
    workflow.shared_with = []
    workflow.save = AsyncMock()
    
    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get_user, \
         patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get_workflow:
        mock_get_user.side_effect = [owner, target_user]
        mock_get_workflow.return_value = workflow
        
        result = await user_service_instance.share_workflow(owner_id, workflow_id, target_user_id)
        
        assert result is True
        assert workflow_id in target_user.shared_workflows
        assert target_user_id in workflow.shared_with


@pytest.mark.asyncio
async def test_unshare_workflow_success(user_service_instance):
    """Test successfully unsharing a workflow"""
    owner_id = "owner_123"
    workflow_id = "workflow_123"
    target_user_id = "target_456"
    
    owner = Mock(spec=User)
    owner.id = owner_id
    owner.role = UserRole.USER
    owner.owned_workflows = [workflow_id]
    
    target_user = Mock(spec=User)
    target_user.id = target_user_id
    target_user.username = "target_user"
    target_user.shared_workflows = [workflow_id]
    target_user.save = AsyncMock()
    
    workflow = Mock(spec=IProject)
    workflow.id = workflow_id
    workflow.shared_with = [target_user_id]
    workflow.save = AsyncMock()
    
    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get_user, \
         patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get_workflow:
        mock_get_user.side_effect = [owner, target_user]
        mock_get_workflow.return_value = workflow
        
        result = await user_service_instance.unshare_workflow(owner_id, workflow_id, target_user_id)
        
        assert result is True
        assert workflow_id not in target_user.shared_workflows
        assert target_user_id not in workflow.shared_with


# ============================================
# OWNERSHIP ASSIGNMENT TESTS
# ============================================

@pytest.mark.asyncio
async def test_assign_dataset_ownership_success(user_service_instance, mock_user):
    """Test assigning dataset ownership to user"""
    dataset = Mock(spec=Dataset)
    dataset.id = "dataset_123"
    dataset.save = AsyncMock()
    
    mock_user.owned_datasets = []
    mock_user.save = AsyncMock()
    
    await user_service_instance.assign_dataset_ownership(mock_user, dataset)
    
    assert dataset.owner_id == mock_user.id
    assert dataset.id in mock_user.owned_datasets
    dataset.save.assert_called_once()
    mock_user.save.assert_called_once()


@pytest.mark.asyncio
async def test_assign_workflow_ownership_success(user_service_instance, mock_user):
    """Test assigning workflow ownership to user"""
    workflow = Mock(spec=IProject)
    workflow.id = "workflow_123"
    workflow.save = AsyncMock()
    
    mock_user.owned_workflows = []
    mock_user.save = AsyncMock()
    
    await user_service_instance.assign_workflow_ownership(mock_user, workflow)
    
    assert workflow.owner_id == mock_user.id
    assert workflow.id in mock_user.owned_workflows
    workflow.save.assert_called_once()
    mock_user.save.assert_called_once()


# ============================================
# OWNERSHIP REMOVAL TESTS
# ============================================

@pytest.mark.asyncio
async def test_remove_dataset_ownership_success(user_service_instance):
    """Test removing dataset ownership bidirectionally"""
    dataset_id = "dataset_123"
    owner_id = "owner_123"
    shared_user_id = "shared_456"
    
    owner = Mock(spec=User)
    owner.id = owner_id
    owner.owned_datasets = [dataset_id]
    owner.save = AsyncMock()
    
    shared_user = Mock(spec=User)
    shared_user.id = shared_user_id
    shared_user.shared_datasets = [dataset_id]
    shared_user.save = AsyncMock()
    
    dataset = Mock(spec=Dataset)
    dataset.id = dataset_id
    dataset.owner_id = owner_id
    dataset.shared_with = [shared_user_id]
    
    with patch.object(Dataset, 'get', new_callable=AsyncMock) as mock_get_dataset, \
         patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get_user:
        mock_get_dataset.return_value = dataset
        mock_get_user.side_effect = [owner, shared_user]
        
        await user_service_instance.remove_dataset_ownership(dataset_id)
        
        assert dataset_id not in owner.owned_datasets
        assert dataset_id not in shared_user.shared_datasets
        owner.save.assert_called_once()
        shared_user.save.assert_called_once()


@pytest.mark.asyncio
async def test_remove_workflow_ownership_success(user_service_instance):
    """Test removing workflow ownership bidirectionally"""
    workflow_id = "workflow_123"
    owner_id = "owner_123"
    shared_user_id = "shared_456"
    
    owner = Mock(spec=User)
    owner.id = owner_id
    owner.owned_workflows = [workflow_id]
    owner.save = AsyncMock()
    
    shared_user = Mock(spec=User)
    shared_user.id = shared_user_id
    shared_user.shared_workflows = [workflow_id]
    shared_user.save = AsyncMock()
    
    workflow = Mock(spec=IProject)
    workflow.id = workflow_id
    workflow.owner_id = owner_id
    workflow.shared_with = [shared_user_id]
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get_workflow, \
         patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get_user:
        mock_get_workflow.return_value = workflow
        mock_get_user.side_effect = [owner, shared_user]
        
        await user_service_instance.remove_workflow_ownership(workflow_id)
        
        assert workflow_id not in owner.owned_workflows
        assert workflow_id not in shared_user.shared_workflows
        owner.save.assert_called_once()
        shared_user.save.assert_called_once()


# ============================================
# ADMIN MANAGEMENT TESTS
# ============================================

@pytest.mark.asyncio
async def test_ensure_admin_exists_creates_default(user_service_instance):
    """Test creating default admin when no users exist"""
    with patch.object(User, 'count', new_callable=AsyncMock) as mock_count, \
         patch.object(user_service_instance, 'create_user', new_callable=AsyncMock) as mock_create:
        mock_count.return_value = 0
        mock_create.return_value = Mock(spec=User, username="admin", role=UserRole.ADMIN)
        
        result = await user_service_instance.ensure_admin_exists()
        
        assert result.role == UserRole.ADMIN
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_ensure_admin_exists_admin_present(user_service_instance, sample_user_create):
    """Test ensure_admin_exists when admin already exists"""
    # Create an admin user
    admin_create = UserCreate(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        password="Admin123!",
        role=UserRole.ADMIN
    )
    
    with patch('app.services.user_service.get_password_hash', return_value="hashed_password"):
        admin_user = await user_service_instance.create_user(admin_create)
        
        result = await user_service_instance.ensure_admin_exists()
        
        assert result is not None
        assert result.role == UserRole.ADMIN
        # Should return the existing admin (could be the same or another admin)


@pytest.mark.asyncio
async def test_ensure_admin_exists_promotes_first_user(user_service_instance, sample_user_create):
    """Test promoting first user to admin when no admin exists"""
    # Create a regular user (no admin exists)
    with patch('app.services.user_service.get_password_hash', return_value="hashed_password"):
        regular_user = await user_service_instance.create_user(sample_user_create)
        
        # Ensure admin exists should promote this user
        result = await user_service_instance.ensure_admin_exists()
        
        assert result is not None
        assert result.role == UserRole.ADMIN
        # The regular user should now be an admin
        updated_user = await user_service_instance.get_user_by_id(str(regular_user.id))
        assert updated_user.role == UserRole.ADMIN


# ============================================
# GET USER FROM WORKFLOW TESTS
# ============================================

@pytest.mark.asyncio
async def test_get_user_from_workflow_no_owner(user_service_instance):
    """Workflow without owner_id returns None (public workflow — no exception)"""
    workflow = Mock(spec=IProject)
    workflow.owner_id = None

    result = await user_service_instance.get_user_from_workflow(workflow)

    assert result is None


@pytest.mark.asyncio
async def test_get_user_from_workflow_with_owner(user_service_instance, mock_user):
    """Workflow with a valid owner_id returns the corresponding user"""
    workflow = Mock(spec=IProject)
    workflow.owner_id = mock_user.id

    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_user

        result = await user_service_instance.get_user_from_workflow(workflow)

        assert result == mock_user
        mock_get.assert_called_once_with(mock_user.id)


@pytest.mark.asyncio
async def test_get_user_from_workflow_db_error_propagates(user_service_instance):
    """DB error must propagate — callers must return 503, not silently bypass auth"""
    workflow = Mock(spec=IProject)
    workflow.owner_id = "existing_owner_id"
    workflow.id = "wf_123"

    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("DB connection lost")

        with pytest.raises(Exception, match="DB connection lost"):
            await user_service_instance.get_user_from_workflow(workflow)


@pytest.mark.asyncio
async def test_get_user_from_workflow_deleted_user_propagates(user_service_instance):
    """get_user_by_id returning None (deleted user) must not silently make workflow public"""
    workflow = Mock(spec=IProject)
    workflow.owner_id = "deleted_user_id"

    with patch.object(user_service_instance, 'get_user_by_id', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None

        result = await user_service_instance.get_user_from_workflow(workflow)

        # Returns None from get_user_by_id — caller must handle this case
        assert result is None
