import pytest
import pytest_asyncio
import asyncio
import os
from typing import get_origin, ClassVar
from unittest.mock import Mock
import mongomock
import beanie.odm.utils.parsing as _beanie_parsing
from mongomock_motor import AsyncMongoMockClient
from beanie import init_beanie

# ── Compatibility patches for Beanie 2.x + mongomock ──────────────────────────
# 1. Beanie 2.x calls list_collection_names(authorizedCollections=True, nameOnly=True)
#    but mongomock's Database.list_collection_names only accepts (filter, session).
_orig_lcn = mongomock.Database.list_collection_names
def _patched_lcn(self, filter=None, session=None, **_kwargs):
    return _orig_lcn(self, filter=filter, session=session)
mongomock.Database.list_collection_names = _patched_lcn

# 2. Beanie 2.x always writes _class_id to MongoDB documents. When read back,
#    merge_models() tries to set it on instances — but Pydantic rejects setting
#    ClassVar values on instances. Skip ClassVar fields silently.
_orig_safe_setattr = _beanie_parsing._safe_setattr
def _patched_safe_setattr(model, field_name, value):
    for cls in type(model).__mro__:
        ann = cls.__dict__.get('__annotations__', {}).get(field_name)
        if ann is not None:
            if get_origin(ann) is ClassVar:
                return
            break
    _orig_safe_setattr(model, field_name, value)
_beanie_parsing._safe_setattr = _patched_safe_setattr
# ──────────────────────────────────────────────────────────────────────────────
from app.models.interface.dataset_interface import (
    Dataset, FileDataset, MongoDataset, MysqlDataset, 
    PTXDataset, ApiDataset, ElasticDataset
)
from app.models.interface.workflow_interface import IProject
from app.models.interface.user_interface import User, PasswordResetToken
from app.enums.user_role import UserRole

_test_database = None

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Setup test database once for all tests."""
    global _test_database
    
    if _test_database is None:
        client = AsyncMongoMockClient()
        _test_database = client.get_database("test_db")
        
        # Initialize Beanie with mock database
        await init_beanie(
            database=_test_database,
            document_models=[
                User,
                PasswordResetToken,
                Dataset,
                FileDataset,
                MongoDataset,
                MysqlDataset,
                PTXDataset,
                ApiDataset,
                ElasticDataset,
                IProject
            ]
        )
    
    yield _test_database

@pytest_asyncio.fixture(autouse=True)
async def clean_collections():
    """Clean all collections before each test."""
    if _test_database is not None:
        # Clean collections
        for model in [User, PasswordResetToken, Dataset, FileDataset, MongoDataset, MysqlDataset, PTXDataset, ApiDataset, ElasticDataset, IProject]:
            try:
                await model.delete_all()
            except Exception:
                pass
    yield


@pytest.fixture
def mock_user():
    """Create a mock user for testing with permission management.
    
    This fixture provides a standard test user with:
    - Basic user information (id, username, email)
    - Active status
    - USER role (not admin)
    - Empty owned/shared resources lists
    
    Usage:
        def test_something(mock_user):
            result = await service.get_datasets(mock_user)
    """
    user = Mock()
    user.id = "test_user_id_123"
    user.username = "test_user"
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.role = UserRole.USER
    user.is_active = True
    user.owned_datasets = []
    user.owned_workflows = []
    user.shared_datasets = []
    user.shared_workflows = []
    user.hashed_password = "hashed_password"
    return user


@pytest.fixture
def mock_admin_user():
    """Create a mock admin user for testing admin-specific functionality.
    
    This fixture provides a test admin user with:
    - ADMIN role
    - All standard user attributes
    
    Usage:
        def test_admin_operation(mock_admin_user):
            result = await service.delete_user(user_id, mock_admin_user)
    """
    user = Mock()
    user.id = "admin_user_id_456"
    user.username = "admin_user"
    user.email = "admin@example.com"
    user.full_name = "Admin User"
    user.role = UserRole.ADMIN
    user.is_active = True
    user.owned_datasets = []
    user.owned_workflows = []
    user.shared_datasets = []
    user.shared_workflows = []
    user.hashed_password = "hashed_password"
    return user


@pytest.fixture
def mock_user_with_datasets():
    """Create a mock user with pre-populated owned datasets.
    
    Useful for testing scenarios where user already owns resources.
    
    Usage:
        def test_user_datasets(mock_user_with_datasets):
            assert len(mock_user_with_datasets.owned_datasets) > 0
    """
    user = Mock()
    user.id = "user_with_data_789"
    user.username = "data_user"
    user.email = "data@example.com"
    user.full_name = "Data User"
    user.role = UserRole.USER
    user.is_active = True
    user.owned_datasets = ["dataset_1", "dataset_2", "dataset_3"]
    user.owned_workflows = ["workflow_1", "workflow_2"]
    user.shared_datasets = []
    user.shared_workflows = []
    user.hashed_password = "hashed_password"
    return user