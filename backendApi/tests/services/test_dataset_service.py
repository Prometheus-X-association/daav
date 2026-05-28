import pytest
import pandas as pd
import tempfile
import os
import json
import shutil
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone
from contextvars import copy_context
import asyncio
import pytest_asyncio

from app.services.dataset_service import DatasetService, pdc_chain_data_var, pdc_chain_headers_var
from app.models.interface.dataset_interface import (
    Dataset, FileDataset, MongoDataset, MysqlDataset, 
    PTXDataset, ApiDataset, ElasticDataset, DatasetParams, Pagination
)
from app.models.interface.node_data import NodeDataPandasDf
from app.models.interface.pdc_chain_interface import PdcChainHeaders
from app.enums.status_node import StatusNode
from fastapi import HTTPException

# ===========================
# FIXTURES
# ===========================

@pytest.fixture
def dataset_service():
    return DatasetService()

@pytest_asyncio.fixture
async def sample_file_dataset():
    dataset = FileDataset(
        name="test_file",
        type="file",
        inputType="file",
        filePath="/path/to/test.csv",
        csvHeader="0",
        csvDelimiter=","
    )
    await dataset.insert()
    return dataset

@pytest_asyncio.fixture
async def sample_mysql_dataset():
    dataset = MysqlDataset(
        name="test_mysql",
        type="mysql",
        host="localhost",
        database="test_db",
        table="test_table",
        user="test_user",
        password="test_password"
    )
    await dataset.insert()
    return dataset

@pytest_asyncio.fixture
async def sample_mongo_dataset():
    dataset = MongoDataset(
        name="test_mongo",
        type="mongo",
        uri="mongodb://localhost:27017",
        database="test_db",
        collection="test_collection"
    )
    await dataset.insert()
    return dataset

@pytest_asyncio.fixture
async def sample_ptx_dataset():
    dataset = PTXDataset(
        name="test_ptx",
        type="ptx",
        url="https://api.example.com",
        service_key="test_service_key",
        secret_key="test_secret_key"
    )
    await dataset.insert()
    return dataset

@pytest.mark.asyncio
async def test_edit_ptx_dataset_preserves_sensitive_fields(dataset_service, monkeypatch):
    monkeypatch.setenv(
        "FIELD_ENCRYPTION_KEY",
        "2frZC2o4MLN2F1sSxJk7Y0Kj0I7j9N2G5Q7e4Wj7iNw=",
    )
    dataset = PTXDataset(
        id="dataset-ptx-preserve",
        name="test_ptx",
        type="ptx",
        url="https://pdc.example.com",
        token="secret-token",
        refreshToken="secret-refresh",
    )
    await dataset.insert()

    # Simulate frontend edit payload without sensitive PTX fields.
    updated_dataset = PTXDataset(
        id=dataset.id,
        name="test_ptx_updated",
        type="ptx",
        url="https://pdc.example.com",
    )

    with patch.object(dataset_service.user_service, 'can_modify_dataset', new=AsyncMock(return_value=True)):
        result = await dataset_service.edit_dataset(updated_dataset, Mock(username="testuser"))

    assert result is True

    saved = await PTXDataset.get(dataset.id)
    assert saved.name == "test_ptx_updated"
    assert saved.token == "secret-token"
    assert saved.refreshToken == "secret-refresh"
    assert saved.url == "https://pdc.example.com"


@pytest.mark.asyncio
async def test_edit_mysql_dataset_preserves_sensitive_password(dataset_service, monkeypatch):
    monkeypatch.setenv(
        "FIELD_ENCRYPTION_KEY",
        "2frZC2o4MLN2F1sSxJk7Y0Kj0I7j9N2G5Q7e4Wj7iNw=",
    )
    dataset = MysqlDataset(
        id="dataset-mysql-preserve",
        name="test_mysql",
        type="mysql",
        host="localhost",
        database="test_db",
        table="test_table",
        user="test_user",
        password="super-secret",
    )
    await dataset.insert()

    updated_dataset = MysqlDataset(
        id=dataset.id,
        name="test_mysql_updated",
        type="mysql",
        host="localhost",
        database="test_db",
        table="test_table",
        user="test_user",
    )

    with patch.object(dataset_service.user_service, 'can_modify_dataset', new=AsyncMock(return_value=True)):
        result = await dataset_service.edit_dataset(updated_dataset, Mock(username="testuser"))

    assert result is True

    saved = await MysqlDataset.get(dataset.id)
    assert saved.name == "test_mysql_updated"
    assert saved.password == "super-secret"


@pytest.fixture
def temp_csv_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("name,age,city\n")
        f.write("John,30,Paris\n")
        f.write("Jane,25,London\n")
        f.write("Bob,35,Berlin\n")
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def temp_unknow_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ukn', delete=False) as f:
        f.write("name,age,city\n")
        f.write("John,30,Paris\n")
        f.write("Jane,25,London\n")
        f.write("Bob,35,Berlin\n")
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def temp_json_file():
    data = [
        {"name": "John", "age": 30, "city": "Paris"},
        {"name": "Jane", "age": 25, "city": "London"},
        {"name": "Bob", "age": 35, "city": "Berlin"}
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def temp_directory():
    temp_dir = tempfile.mkdtemp()
    csv_file = os.path.join(temp_dir, "test.csv")
    with open(csv_file, 'w') as f:
        f.write("id,value\n1,test1\n2,test2\n")
    json_file = os.path.join(temp_dir, "test.json")
    with open(json_file, 'w') as f:
        json.dump([{"id": 1, "value": "test"}], f)
    yield temp_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

# ===========================
# HELPERS
# ===========================

def create_file_dataset(**kwargs):
    defaults = {
        'name': 'test_file',
        'type': 'file',
        'inputType': 'file',
        'filePath': '/tmp/test.csv',
        'csvHeader': '0',
        'csvDelimiter': ','
    }
    return FileDataset(**{**defaults, **kwargs})

def create_file_dataset_mock(**kwargs):
    from unittest.mock import Mock
    defaults = {
        'name': 'test_file',
        'type': 'file',
        'inputType': 'file',
        'filePath': '/tmp/test.csv',
        'csvHeader': '0',
        'csvDelimiter': ','
    }
    attributes = {**defaults, **kwargs}
    mock_dataset = Mock(spec=FileDataset)
    for key, value in attributes.items():
        if value is not None:
            setattr(mock_dataset, key, value)
    def mock_hasattr(name):
        return hasattr(mock_dataset, name) and getattr(mock_dataset, name, None) is not None
    original_getattribute = mock_dataset.__getattribute__
    def new_getattribute(name):
        if name == '__dict__':
            return {k: v for k, v in mock_dataset._mock_children.items() if not k.startswith('_')}
        return original_getattribute(name)
    mock_dataset.__getattribute__ = new_getattribute
    return mock_dataset

async def create_file_dataset_async(**kwargs):
    defaults = {
        'name': 'test_file',
        'type': 'file',
        'inputType': 'file',
        'filePath': '/tmp/test.csv',
        'csvHeader': '0',
        'csvDelimiter': ','
    }
    return FileDataset(**{**defaults, **kwargs})

# ===========================
# PROPERTY TESTS
# ===========================

def test_pdc_chain_data_property(dataset_service):
    test_data = {"key": "value"}
    dataset_service.pdcChainData = test_data
    assert dataset_service.pdcChainData == test_data
    assert pdc_chain_data_var.get() == test_data

def test_pdc_chain_headers_property(dataset_service):
    test_headers = PdcChainHeaders(
        Authorization="Bearer token",
        x_ptx_service_chain_id="chain_id",
        x_ptx_target_id="target_id"
    )
    dataset_service.pdcChainHeaders = test_headers
    assert dataset_service.pdcChainHeaders == test_headers
    assert pdc_chain_headers_var.get() == test_headers

@pytest.mark.asyncio
async def test_context_isolation(dataset_service):
    async def set_context_1():
        dataset_service.pdcChainData = {"context": "1"}
        await asyncio.sleep(0.1)
        return dataset_service.pdcChainData
    async def set_context_2():
        dataset_service.pdcChainData = {"context": "2"}
        await asyncio.sleep(0.1)
        return dataset_service.pdcChainData
    result1, result2 = await asyncio.gather(
        set_context_1(),
        set_context_2()
    )
    assert result1["context"] == "1"
    assert result2["context"] == "2"

# ===========================
# CRUD TESTS
# ===========================

@pytest.mark.asyncio
async def test_get_datasets_success(dataset_service, sample_file_dataset, sample_mysql_dataset, mock_user):
    file_ds = sample_file_dataset
    mysql_ds = sample_mysql_dataset
    # Assign ownership to mock_user
    file_ds.owner_id = mock_user.id
    mysql_ds.owner_id = mock_user.id
    mock_user.owned_datasets = [str(file_ds.id), str(mysql_ds.id)]
    await file_ds.save()
    await mysql_ds.save()
    
    result = await dataset_service.get_datasets(mock_user)
    assert len(result) == 2
    assert any(ds.name == "test_file" for ds in result)
    assert any(ds.name == "test_mysql" for ds in result)

@pytest.mark.asyncio
async def test_get_dataset_success(dataset_service, sample_file_dataset, mock_user):
    dataset = sample_file_dataset
    # Assign ownership to mock_user
    dataset.owner_id = mock_user.id
    mock_user.owned_datasets = [str(dataset.id)]
    await dataset.save()
    
    # Mock the permission check to return True
    with patch.object(dataset_service.user_service, 'can_access_dataset', return_value=True):
        result = await dataset_service.get_dataset(str(dataset.id), mock_user)
        assert result is not None
        assert result.name == "test_file"
        assert result.type == "file"

@pytest.mark.asyncio
async def test_delete_dataset_success(dataset_service, sample_file_dataset, mock_user):
    dataset = sample_file_dataset
    dataset_id = str(dataset.id)
    # Assign ownership to mock_user
    dataset.owner_id = mock_user.id
    await dataset.save()
    
    # Mock the permission check to return True
    with patch.object(dataset_service, '_cleanup_file_dataset'), \
         patch.object(dataset_service.user_service, 'can_modify_dataset', return_value=True):
        result = await dataset_service.delete_dataset(dataset_id, mock_user)
        assert result is True
        deleted_dataset = await Dataset.get(dataset.id)
        assert deleted_dataset is None

@pytest.mark.asyncio
async def test_add_connection_already_exists_old(dataset_service, sample_file_dataset, mock_user):
    existing_dataset = sample_file_dataset
    dataset = await create_file_dataset_async(
        name="test_file",
        filePath="/same/path.csv"
    )
    # Mock user owns the existing dataset
    mock_user.owned_datasets = [str(existing_dataset.id)]
    
    with patch.object(dataset_service, '_connection_exists', return_value=True):
        result = await dataset_service.add_connection(dataset, mock_user)
        assert result["status"] == "Dataset already exists"

@pytest.mark.asyncio
async def test_process_ptx_dataset(dataset_service, sample_ptx_dataset):
    dataset = sample_ptx_dataset
    with patch.object(dataset_service, 'connect_pdc') as mock_connect:
        mock_connect.return_value = {
            "content": {
                "token": "test_token",
                "refreshToken": "test_refresh_token"
            }
        }
        result = dataset_service._process_ptx_dataset(dataset)
        assert result.token == "test_token"
        assert result.refreshToken == "test_refresh_token"
        assert result.service_key is None
        assert result.secret_key is None
        mock_connect.assert_called_once()

@patch('app.services.dataset_service.create_engine')
@patch('pandas.read_sql')
@pytest.mark.asyncio
async def test_get_df_mysql_content(mock_read_sql, mock_create_engine, dataset_service, sample_mysql_dataset):
    dataset = sample_mysql_dataset
    mock_df = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['John', 'Jane', 'Bob']
    })
    mock_read_sql.return_value = mock_df
    mock_engine = Mock()
    mock_create_engine.return_value = mock_engine
    dataset_params = DatasetParams(database="test_db", table="test_table")
    result = dataset_service.getDfMysqlContent(dataset, dataset_params)
    assert isinstance(result, NodeDataPandasDf)
    assert isinstance(result.data, pd.DataFrame)
    assert len(result.data) == 3
    mock_create_engine.assert_called_once()
    mock_read_sql.assert_called_once()

# ===========================
# FILE OPERATIONS TESTS
# ===========================

def test_cleanup_file_dataset_folder(dataset_service, temp_directory):
    dataset = create_file_dataset_mock(
        name="test",
        folder=temp_directory,
        filePath="",
    )
    assert os.path.exists(temp_directory)
    dataset_service._cleanup_file_dataset(dataset)
    assert not os.path.exists(temp_directory)

def test_cleanup_file_dataset_single_file(dataset_service, temp_csv_file):
    dataset = create_file_dataset_mock(
        name="test",
        filePath=temp_csv_file,
        folder=""
    )
    assert os.path.exists(temp_csv_file)
    dataset_service._cleanup_file_dataset(dataset)
    assert not os.path.exists(temp_csv_file)

def test_process_file_dataset_csv(dataset_service, temp_csv_file):
    dataset = create_file_dataset_mock(
        name="test_csv",
        filePath=temp_csv_file,
        csvHeader="0",
        csvDelimiter=","
    )
    result = dataset_service._process_file_dataset(dataset)
    assert result.metadata is not None
    assert result.metadata.fileType == "csv"
    assert result.metadata.columnCount == "3"
    assert result.metadata.rowCount == "3"

def test_process_file_dataset_json(dataset_service, temp_json_file):
    dataset = create_file_dataset_mock(
        name="test_json",
        filePath=temp_json_file
    )
    result = dataset_service._process_file_dataset(dataset)
    assert result.metadata is not None
    assert result.metadata.fileType == "json"
    assert result.metadata.columnCount == "3"
    assert result.metadata.rowCount == "3"

# ===========================
# DATA RETRIEVAL TESTS
# ===========================

def test_get_df_file_content_csv(dataset_service, temp_csv_file):
    dataset = create_file_dataset(
        name="test_csv",
        filePath=temp_csv_file,
        csvHeader="0",
        csvDelimiter=","
    )
    result = dataset_service.getDfFileContentData(dataset)
    assert isinstance(result, NodeDataPandasDf)
    assert result.name == "test_csv"
    assert isinstance(result.data, pd.DataFrame)
    assert len(result.data) == 3
    assert list(result.data.columns) == ["name", "age", "city"]

def test_get_df_file_content_csv_with_pagination(dataset_service, temp_csv_file):
    dataset = create_file_dataset(
        name="test_csv",
        filePath=temp_csv_file,
        csvHeader="0",
        csvDelimiter=","
    )
    pagination = Pagination(page=1, perPage=2)
    result = dataset_service.getDfFileContentData(dataset, pagination)
    assert isinstance(result, NodeDataPandasDf)
    assert isinstance(result.dataExample, pd.DataFrame)
    assert len(result.dataExample) == 2

def test_get_df_file_content_json(dataset_service, temp_json_file):
    dataset = create_file_dataset(
        name="test_json",
        filePath=temp_json_file
    )
    result = dataset_service.getDfFileContentData(dataset)
    assert isinstance(result, NodeDataPandasDf)
    assert result.name == "test_json"
    assert isinstance(result.data, pd.DataFrame)
    assert len(result.data) == 3
    assert list(result.data.columns) == ["name", "age", "city"]

def test_get_df_file_content_file_not_found(dataset_service):
    dataset = create_file_dataset(
        name="test_nonexistent",
        filePath="/nonexistent/path.csv"
    )
    with pytest.raises(HTTPException) as exc_info:
        dataset_service.getDfFileContentData(dataset)
    assert exc_info.value.status_code == 404

@patch('app.services.dataset_service.folder')
def test_get_df_file_content_folder(mock_folder, dataset_service, temp_directory):
    mock_folder.return_value = [
        {"file": "test1.txt", "content": "content1"},
        {"file": "test2.txt", "content": "content2"}
    ]
    dataset = create_file_dataset(
        name="test_folder",
        folder=temp_directory
    )
    result = dataset_service.getDfFileContentData(dataset)
    assert isinstance(result, NodeDataPandasDf)
    mock_folder.assert_called_once_with(temp_directory, None)

# ===========================
# CONNECTION TESTS
# ===========================

@pytest.mark.asyncio
async def test_add_connection_file_dataset(dataset_service, temp_csv_file, mock_user):
    dataset = await create_file_dataset_async(
        name="test_file_connection",
        filePath=temp_csv_file
    )
    with patch.object(dataset_service, '_process_file_dataset') as mock_process, \
         patch.object(dataset_service, '_connection_exists', return_value=False) as mock_exists, \
         patch.object(dataset_service.user_service, 'assign_dataset_ownership') as mock_assign:
        mock_process.return_value = dataset
        result = await dataset_service.add_connection(dataset, mock_user)
        assert result["status"] == "Connection added"
        mock_exists.assert_called_once()
        mock_process.assert_called_once()
        mock_assign.assert_called_once_with(mock_user, dataset)

@pytest.mark.asyncio
async def test_add_connection_already_exists(dataset_service, sample_file_dataset, mock_user):
    existing_dataset = sample_file_dataset
    dataset = await create_file_dataset_async(
        name="test_file",
        filePath="/same/path.csv"
    )
    with patch.object(dataset_service, '_connection_exists', return_value=True):
        result = await dataset_service.add_connection(dataset, mock_user)
        assert result["status"] == "Dataset already exists"

@pytest.mark.asyncio
async def test_connection_exists_file_dataset(dataset_service, sample_file_dataset, mock_user):
    existing_dataset = sample_file_dataset
    # Mock user owns this dataset
    mock_user.owned_datasets = [str(existing_dataset.id)]
    
    dataset = create_file_dataset_mock(
        name="test_file",
        filePath="/path/to/test.csv"
    )
    result = await dataset_service._connection_exists(dataset, mock_user)
    assert result is True

@pytest.mark.asyncio
async def test_connection_exists_mysql_dataset_not_found(dataset_service, mock_user):
    # User has no datasets
    mock_user.owned_datasets = []
    
    dataset = MysqlDataset(
        name="nonexistent_mysql",
        type="mysql",
        host="localhost",
        database="nonexistent_db",
        table="nonexistent_table",
        user="test_user",
        password="test_password"
    )
    result = await dataset_service._connection_exists(dataset, mock_user)
    assert result is False

@pytest.mark.asyncio
async def test_connection_exists_different_users_same_path(dataset_service, sample_file_dataset, mock_user):
    """Test that same file path can exist for different users"""
    # User 1 owns the dataset
    user1 = Mock()
    user1.id = "user1_id"
    user1.username = "user1"
    user1.owned_datasets = [str(sample_file_dataset.id)]
    
    # User 2 doesn't own it
    user2 = Mock()
    user2.id = "user2_id"
    user2.username = "user2"
    user2.owned_datasets = []
    
    # Check same dataset - user1 should see it exists
    dataset = create_file_dataset_mock(
        name="test_file",
        filePath="/path/to/test.csv"
    )
    result_user1 = await dataset_service._connection_exists(dataset, user1)
    assert result_user1 is True, "User1 should see the dataset exists"
    
    # User2 should NOT see it exists (user isolation)
    result_user2 = await dataset_service._connection_exists(dataset, user2)
    assert result_user2 is False, "User2 should not see user1's dataset"

@pytest.mark.asyncio
async def test_add_connection_user_isolation(dataset_service, temp_csv_file, mock_user):
    """Test that users can add connections with same path independently"""
    # User 1
    user1 = Mock()
    user1.id = "user1_id"
    user1.username = "user1"
    user1.owned_datasets = []
    
    # User 2
    user2 = Mock()
    user2.id = "user2_id"
    user2.username = "user2"
    user2.owned_datasets = []
    
    # Both users add dataset with same path
    dataset1 = await create_file_dataset_async(
        name="user1_dataset",
        filePath=temp_csv_file
    )
    dataset2 = await create_file_dataset_async(
        name="user2_dataset",
        filePath=temp_csv_file
    )
    
    with patch.object(dataset_service, '_process_file_dataset', side_effect=lambda x: x), \
         patch.object(dataset_service.user_service, 'assign_dataset_ownership'):
        
        # User1 adds first
        result1 = await dataset_service.add_connection(dataset1, user1)
        assert result1["status"] == "Connection added"
        
        # User2 can also add (different user scope)
        result2 = await dataset_service.add_connection(dataset2, user2)
        assert result2["status"] == "Connection added"

# ===========================
# PTX TESTS
# ===========================

@pytest.mark.asyncio
async def test_process_ptx_dataset(dataset_service, sample_ptx_dataset):
    dataset = sample_ptx_dataset
    with patch.object(dataset_service, 'connect_pdc') as mock_connect:
        mock_connect.return_value = {
            "content": {
                "token": "test_token",
                "refreshToken": "test_refresh_token"
            }
        }
        result = dataset_service._process_ptx_dataset(dataset)
        assert result.token == "test_token"
        assert result.refreshToken == "test_refresh_token"
        assert result.service_key is None
        assert result.secret_key is None
        mock_connect.assert_called_once()

# ===========================
# DATABASE TESTS
# ===========================

@patch('app.services.dataset_service.create_engine')
@patch('pandas.read_sql')
@pytest.mark.asyncio
async def test_get_df_mysql_content(mock_read_sql, mock_create_engine, dataset_service, sample_mysql_dataset):
    dataset = sample_mysql_dataset
    mock_df = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['John', 'Jane', 'Bob']
    })
    mock_read_sql.return_value = mock_df
    mock_engine = Mock()
    mock_create_engine.return_value = mock_engine
    dataset_params = DatasetParams(database="test_db", table="test_table")
    result = dataset_service.getDfMysqlContent(dataset, dataset_params)
    assert isinstance(result, NodeDataPandasDf)
    assert isinstance(result.data, pd.DataFrame)
    assert len(result.data) == 3
    mock_create_engine.assert_called_once()
    mock_read_sql.assert_called_once()

# ===========================
# ERROR HANDLING TESTS
# ===========================

def test_get_df_file_content_permission_error(dataset_service):
    dataset = create_file_dataset_mock(
        name="test_permission",
        filePath="/root/restricted.csv",
        folder=""
    )
    with patch('os.path.exists', return_value=True), \
         patch('os.path.getsize', side_effect=PermissionError("Permission denied")):
        with pytest.raises(HTTPException) as exc_info:
            dataset_service.getDfFileContentData(dataset)
        assert exc_info.value.status_code == 403

def test_get_df_file_content_unsupported_file_format(dataset_service, temp_unknow_file):
    dataset = create_file_dataset_mock(
        name="test_invalid",
        inputType="invalid_type",
        filePath=temp_unknow_file,
        folder=""
    )
    with pytest.raises(HTTPException) as exc_info:
        dataset_service.getDfFileContentData(dataset)
    assert exc_info.value.status_code == 400
    assert "Unsupported file format" in str(exc_info.value.detail)

if __name__ == "__main__":
    pytest.main([__file__])

# ============================================================================
# M2M (Machine-to-Machine) Tests - Optional User Parameter
# ============================================================================

@pytest.mark.asyncio
async def test_get_datasets_without_user():
    """Test that get_datasets works without user (returns all datasets for M2M calls)"""
    dataset_service = DatasetService()
    
    # Create test datasets
    dataset1 = FileDataset(
        id="test-dataset-m2m-1",
        name="M2M Dataset 1",
        type="file",
        inputType="file",
        path="/tmp/test_m2m_1.csv"
    )
    dataset2 = FileDataset(
        id="test-dataset-m2m-2",
        name="M2M Dataset 2",
        type="file",
        inputType="file",
        path="/tmp/test_m2m_2.csv"
    )
    await dataset1.insert()
    await dataset2.insert()
    
    # Call without user parameter (M2M style)
    datasets = await dataset_service.get_datasets()
    
    # Should get all datasets without permission filtering
    assert len(datasets) >= 2
    assert any(d.id == "test-dataset-m2m-1" for d in datasets)
    assert any(d.id == "test-dataset-m2m-2" for d in datasets)


@pytest.mark.asyncio
async def test_get_dataset_without_user():
    """Test that get_dataset works without user (no permission check for M2M calls)"""
    dataset_service = DatasetService()
    
    # Create test dataset
    dataset = FileDataset(
        id="test-dataset-m2m-3",
        name="M2M Dataset 3",
        type="file",
        inputType="file",
        path="/tmp/test_m2m_3.csv"
    )
    await dataset.insert()
    
    # Call without user parameter (M2M style)
    result = await dataset_service.get_dataset("test-dataset-m2m-3")
    
    # Should get dataset without permission check
    assert result is not None
    assert result.id == "test-dataset-m2m-3"
    assert result.name == "M2M Dataset 3"
