"""
Tests for PDCService

This module tests PDC (Prometheus Data Connector) service functionality including:
- Fetching PDC resources (contracts, participants, ecosystems, etc.)
- Service chain data management
- Error handling for HTTP requests
- Async fetch methods
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import requests
import httpx
from fastapi import HTTPException

from app.services.pdc_service import PdcService
from app.models.interface.pdc_chain_interface import ServiceChainData, PdcChainRequestData
from app.models.interface.pdc_interface import (
    PdcContract, 
    PdcEcosystem, 
    PdcParticipant, 
    PdcServiceOffering,
    PdcContractBilateral,
    PdcDataResource
)


@pytest.fixture
def pdc_service_instance():
    """Get PDCService instance (singleton)"""
    # Clear singleton instance for testing
    PdcService._instances = {}
    return PdcService()


@pytest.fixture
def mock_pdc_contract():
    """Mock PDC Contract data"""
    return {
        "_id": "contract_123",
        "ecosystem": "https://api.example.com/ecosystem/1",
        "dataProvider": "https://api.example.com/participant/1",
        "purpose": [{"purpose": "https://api.example.com/service/1"}],
        "serviceOffering": "https://api.example.com/service/1",
        "status": "active",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
        "__v": 0
    }


@pytest.fixture
def mock_pdc_ecosystem():
    """Mock PDC Ecosystem data"""
    return {
        "@context": "https://example.com",
        "@type": "Ecosystem",
        "_id": "ecosystem_1",
        "administrator": "admin_id",
        "orchestrator": "orchestrator_id",
        "name": "Test Ecosystem",
        "description": "Test Description",
        "detailedDescription": "Test Detailed Description",
        "participants": [],
        "contract": "contract_id",
        "businessLogic": {
            "businessModel": [],
            "roles": []
        },
        "status": "active",
        "schema_version": "1.0",
        "context": [],
        "logo": "https://example.com/logo.png",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
        "__v": 0
    }


@pytest.fixture
def mock_pdc_participant():
    """Mock PDC Participant data"""
    return {
        "@context": "https://example.com",
        "@type": "Participant",
        "_id": "participant_1",
        "legalName": "Test Participant",
        "legalPerson": {
            "headquartersAddress": {"countryCode": "FR"},
            "legalAddress": {"countryCode": "FR"}
        },
        "associatedOrganisation": "org_id",
        "schema_version": "1.0",
        "dataspaceConnectorAppKey": "app_key",
        "dataspaceEndpoint": "https://endpoint.com",
        "logo": "https://example.com/participant-logo.png",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
        "__v": 0
    }


@pytest.fixture
def mock_pdc_service_offering():
    """Mock PDC Service Offering data"""
    return {
        "@context": "https://example.com",
        "@type": "ServiceOffering",
        "_id": "service_1",
        "name": "Test Service",
        "providedBy": "provider_id",
        "image": "https://example.com/service-image.png",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
        "__v": 0
    }


@pytest.fixture
def mock_pdc_data_resource():
    """Mock PDC Data Resource data"""
    return {
        "@context": "https://example.com",
        "@type": "DataResource",
        "_id": "resource_1",
        "attributes": [],
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
        "__v": 0
    }


# ============================================
# MAKE REQUEST TESTS
# ============================================

@pytest.mark.asyncio
async def test_make_request_success(pdc_service_instance):
    """Test successful HTTP request"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"test": "data"}
    
    with patch('app.services.pdc_service.requests.get', return_value=mock_response):
        result = pdc_service_instance._make_request("https://api.example.com/test")
        
        assert result == {"test": "data"}


@pytest.mark.asyncio
async def test_make_request_with_custom_headers(pdc_service_instance):
    """Test request with custom headers"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"test": "data"}
    
    custom_headers = {"Authorization": "Bearer token123"}
    
    with patch('app.services.pdc_service.requests.get', return_value=mock_response) as mock_get:
        result = pdc_service_instance._make_request("https://api.example.com/test", custom_headers)
        
        # Verify headers were merged
        call_kwargs = mock_get.call_args[1]
        assert "Authorization" in call_kwargs["headers"]
        assert call_kwargs["headers"]["Authorization"] == "Bearer token123"


@pytest.mark.asyncio
async def test_make_request_http_error(pdc_service_instance):
    """Test request with HTTP error"""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
    
    with patch('app.services.pdc_service.requests.get', return_value=mock_response):
        with pytest.raises(HTTPException) as exc_info:
            pdc_service_instance._make_request("https://api.example.com/test")
        
        assert exc_info.value.status_code == 400
        assert "Failed to fetch data" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_make_request_timeout(pdc_service_instance):
    """Test request timeout"""
    with patch('app.services.pdc_service.requests.get', side_effect=requests.exceptions.Timeout()):
        with pytest.raises(HTTPException) as exc_info:
            pdc_service_instance._make_request("https://api.example.com/test")
        
        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_make_request_connection_error(pdc_service_instance):
    """Test request connection error"""
    with patch('app.services.pdc_service.requests.get', side_effect=requests.exceptions.ConnectionError()):
        with pytest.raises(HTTPException) as exc_info:
            pdc_service_instance._make_request("https://api.example.com/test")
        
        assert exc_info.value.status_code == 400


# ============================================
# FETCH RESOURCE TESTS
# ============================================

@pytest.mark.asyncio
async def test_fetch_data_resource(pdc_service_instance, mock_pdc_data_resource):
    """Test fetching PDC data resource"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_pdc_data_resource
    
    with patch('app.services.pdc_service.requests.get', return_value=mock_response):
        result = pdc_service_instance.fetch_dataResource("https://api.example.com/resource/1")
        
        assert isinstance(result, PdcDataResource)
        assert result.id == "resource_1"


@pytest.mark.asyncio
async def test_fetch_contract(pdc_service_instance, mock_pdc_contract):
    """Test fetching PDC contract"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_pdc_contract
    
    with patch('app.services.pdc_service.requests.get', return_value=mock_response):
        result = pdc_service_instance.fetch_contract("https://api.example.com/contract/1")
        
        assert isinstance(result, PdcContract)
        assert result.id == "contract_123"


@pytest.mark.asyncio
async def test_fetch_contract_bilateral(pdc_service_instance, mock_pdc_contract):
    """Test fetching PDC bilateral contract"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_pdc_contract
    
    with patch('app.services.pdc_service.requests.get', return_value=mock_response):
        result = pdc_service_instance.fetch_contract_bilateral("https://api.example.com/contract/1")
        
        assert isinstance(result, PdcContractBilateral)


@pytest.mark.asyncio
async def test_fetch_participant(pdc_service_instance, mock_pdc_participant):
    """Test fetching PDC participant"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_pdc_participant
    
    with patch('app.services.pdc_service.requests.get', return_value=mock_response):
        result = pdc_service_instance.fetch_participant("https://api.example.com/participant/1")
        
        assert isinstance(result, PdcParticipant)
        assert result.legalName == "Test Participant"


@pytest.mark.asyncio
async def test_fetch_ecosystem(pdc_service_instance, mock_pdc_ecosystem):
    """Test fetching PDC ecosystem"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_pdc_ecosystem
    
    with patch('app.services.pdc_service.requests.get', return_value=mock_response):
        result = pdc_service_instance.fetch_ecosystem("https://api.example.com/ecosystem/1")
        
        assert isinstance(result, PdcEcosystem)
        assert result.name == "Test Ecosystem"


@pytest.mark.asyncio
async def test_fetch_service_offering(pdc_service_instance, mock_pdc_service_offering):
    """Test fetching PDC service offering"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_pdc_service_offering
    
    with patch('app.services.pdc_service.requests.get', return_value=mock_response):
        result = pdc_service_instance.fetch_service_offering("https://api.example.com/service/1")
        
        assert isinstance(result, PdcServiceOffering)
        assert result.name == "Test Service"


# ============================================
# EXTRACT INFORMATION FROM CONTRACT TESTS
# ============================================

@pytest.mark.asyncio
async def test_get_ecosystem_name_from_contract(pdc_service_instance, mock_pdc_contract, mock_pdc_ecosystem):
    """Test extracting ecosystem name from contract"""
    mock_response = Mock()
    mock_response.status_code = 200
    
    def side_effect_json():
        # First call returns contract, second returns ecosystem
        if mock_response.call_count == 1:
            return mock_pdc_ecosystem
        return mock_pdc_contract
    
    mock_response.json.side_effect = side_effect_json
    mock_response.call_count = 0
    
    def increment_count(*args, **kwargs):
        mock_response.call_count += 1
        return mock_response
    
    with patch('app.services.pdc_service.requests.get', side_effect=increment_count):
        contract = PdcContract.model_validate(mock_pdc_contract)
        
        # Mock the fetch_ecosystem call
        with patch.object(pdc_service_instance, 'fetch_ecosystem') as mock_fetch:
            ecosystem = PdcEcosystem.model_validate(mock_pdc_ecosystem)
            mock_fetch.return_value = ecosystem
            
            result = pdc_service_instance.get_ecosystem_name_from_contract(contract)
            
            assert result == "Test Ecosystem"


@pytest.mark.asyncio
async def test_get_ecosystem_name_from_contract_no_ecosystem(pdc_service_instance):
    """Test extracting ecosystem name when contract has no ecosystem"""
    contract_data = {
        "_id": "contract_123",
        "status": "active",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
        "__v": 0
    }
    contract = PdcContract.model_validate(contract_data)
    
    result = pdc_service_instance.get_ecosystem_name_from_contract(contract)
    
    assert result is None


@pytest.mark.asyncio
async def test_get_provider_name_from_contract_with_purpose(pdc_service_instance, mock_pdc_contract, mock_pdc_service_offering):
    """Test extracting provider name from contract with purpose"""
    contract = PdcContract.model_validate(mock_pdc_contract)
    
    with patch.object(pdc_service_instance, 'fetch_service_offering') as mock_fetch:
        service = PdcServiceOffering.model_validate(mock_pdc_service_offering)
        mock_fetch.return_value = service
        
        result = pdc_service_instance.get_provider_name_from_contract(contract)
        
        assert result == "Test Service"


@pytest.mark.asyncio
async def test_get_provider_name_from_contract_with_data_provider(pdc_service_instance, mock_pdc_participant):
    """Test extracting provider name from contract with dataProvider"""
    contract_data = {
        "_id": "contract_123",
        "dataProvider": "https://api.example.com/participant/1",
        "status": "active",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
        "__v": 0
    }
    contract = PdcContract.model_validate(contract_data)
    
    with patch.object(pdc_service_instance, 'fetch_participant') as mock_fetch:
        participant = PdcParticipant.model_validate(mock_pdc_participant)
        mock_fetch.return_value = participant
        
        result = pdc_service_instance.get_provider_name_from_contract(contract)
        
        assert result == "Test Participant"


@pytest.mark.asyncio
async def test_get_provider_name_and_img_from_contract(pdc_service_instance, mock_pdc_service_offering):
    """Test extracting provider name and image from bilateral contract"""
    contract_data = {
        "_id": "contract_123",
        "serviceOffering": "https://api.example.com/service/1",
        "purpose": [{"purpose": "https://api.example.com/service/1"}],
        "status": "active",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
        "__v": 0
    }
    contract = PdcContractBilateral.model_validate(contract_data)
    
    with patch.object(pdc_service_instance, 'fetch_service_offering') as mock_fetch:
        service = PdcServiceOffering.model_validate(mock_pdc_service_offering)
        mock_fetch.return_value = service
        
        result = pdc_service_instance.get_provider_name_and_img_from_contract(contract)
        
        assert result["name"] == "Test Service"
        assert result["img"] == "https://example.com/service-image.png"


# ============================================
# SERVICE CHAIN DATA MANAGEMENT TESTS
# ============================================

USER_ID = "user_1"
OTHER_USER_ID = "user_2"


@pytest.mark.asyncio
async def test_store_servicechain_data(pdc_service_instance):
    """Test storing service chain data"""
    service_chain_id = "chain_123"
    data = {"key": "value", "nested": {"data": "test"}}
    
    result = await pdc_service_instance.store_servicechain_data(service_chain_id, data, [USER_ID])
    
    assert result is True
    assert await ServiceChainData.get(ServiceChainData.document_id(service_chain_id, USER_ID)) is not None


@pytest.mark.asyncio
async def test_get_servicechain_data(pdc_service_instance):
    """Test retrieving service chain data"""
    service_chain_id = "chain_456"
    data = {"test": "data"}
    
    await pdc_service_instance.store_servicechain_data(service_chain_id, data, [USER_ID])
    result = await pdc_service_instance.get_servicechain_data(service_chain_id, USER_ID)
    
    assert result is not None
    assert result["service_chain_id"] == service_chain_id
    assert result["data"] == data


@pytest.mark.asyncio
async def test_get_servicechain_data_not_found(pdc_service_instance):
    """Test retrieving non-existent service chain data"""
    result = await pdc_service_instance.get_servicechain_data("nonexistent_chain", USER_ID)
    
    assert result is None


@pytest.mark.asyncio
async def test_delete_servicechain_data(pdc_service_instance):
    """Test deleting service chain data"""
    service_chain_id = "chain_789"
    data = {"test": "data"}
    
    await pdc_service_instance.store_servicechain_data(service_chain_id, data, [USER_ID])
    result = await pdc_service_instance.delete_servicechain_data(service_chain_id, USER_ID)
    
    assert result is True
    assert await ServiceChainData.get(ServiceChainData.document_id(service_chain_id, USER_ID)) is None


@pytest.mark.asyncio
async def test_delete_servicechain_data_not_found(pdc_service_instance):
    """Test deleting non-existent service chain data"""
    result = await pdc_service_instance.delete_servicechain_data("nonexistent_chain", USER_ID)
    
    assert result is False


@pytest.mark.asyncio
async def test_servicechain_data_overwrite(pdc_service_instance):
    """Test overwriting existing service chain data"""
    service_chain_id = "chain_overwrite"
    data1 = {"version": 1}
    data2 = {"version": 2}
    
    await pdc_service_instance.store_servicechain_data(service_chain_id, data1, [USER_ID])
    await pdc_service_instance.store_servicechain_data(service_chain_id, data2, [USER_ID])
    
    result = await pdc_service_instance.get_servicechain_data(service_chain_id, USER_ID)
    assert result["data"]["version"] == 2


@pytest.mark.asyncio
async def test_servicechain_data_shared_between_instances(pdc_service_instance):
    """Data stored by one worker must be readable by another (no per-process storage)"""
    await pdc_service_instance.store_servicechain_data("chain_shared", {"value": 42}, [USER_ID])

    # Simulate another worker process with its own PdcService instance
    PdcService._instances = {}
    other_worker = PdcService()
    assert other_worker is not pdc_service_instance

    result = await other_worker.get_servicechain_data("chain_shared", USER_ID)
    assert result == {"service_chain_id": "chain_shared", "data": {"value": 42}}


@pytest.mark.asyncio
async def test_store_servicechain_data_pydantic_model(pdc_service_instance):
    """Pydantic payloads are stored as plain JSON"""
    data = PdcChainRequestData(origin={"source": "pdc"})

    await pdc_service_instance.store_servicechain_data("chain_model", data, [USER_ID])

    result = await pdc_service_instance.get_servicechain_data("chain_model", USER_ID)
    assert result["data"] == {"additionalData": None, "origin": {"source": "pdc"}}


@pytest.mark.asyncio
async def test_servicechain_data_not_readable_by_other_users(pdc_service_instance):
    """Data is only readable and deletable by the users the PDC request authenticated"""
    await pdc_service_instance.store_servicechain_data("chain_private", {"secret": 1}, [USER_ID])

    assert await pdc_service_instance.get_servicechain_data("chain_private", OTHER_USER_ID) is None
    assert await pdc_service_instance.delete_servicechain_data("chain_private", OTHER_USER_ID) is False
    assert (await pdc_service_instance.get_servicechain_data("chain_private", USER_ID))["data"] == {"secret": 1}


@pytest.mark.asyncio
async def test_servicechain_data_stored_for_each_user(pdc_service_instance):
    """Each authenticated user gets their own copy, deleted independently"""
    await pdc_service_instance.store_servicechain_data("chain_multi", {"v": 1}, [USER_ID, OTHER_USER_ID])

    assert await pdc_service_instance.delete_servicechain_data("chain_multi", USER_ID) is True
    assert await pdc_service_instance.get_servicechain_data("chain_multi", USER_ID) is None
    assert (await pdc_service_instance.get_servicechain_data("chain_multi", OTHER_USER_ID))["data"] == {"v": 1}


def test_servicechain_data_has_ttl_index():
    """Service chain data not deleted by the frontend must expire"""
    ttl_indexes = [
        index.document for index in ServiceChainData.Settings.indexes
        if "expireAfterSeconds" in index.document
    ]
    assert len(ttl_indexes) == 1
    assert ttl_indexes[0]["key"] == {"created_at": 1}


# ============================================
# ASYNC FETCH METHODS TESTS
# ============================================

@pytest.mark.asyncio
async def test_fetch_service_offering_async(pdc_service_instance, mock_pdc_service_offering):
    """Test async service offering fetch"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_pdc_service_offering
    
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    
    result = await pdc_service_instance.fetch_service_offering_async(
        mock_client, 
        "https://api.example.com/service/1"
    )
    
    assert isinstance(result, PdcServiceOffering)
    assert result.name == "Test Service"


@pytest.mark.asyncio
async def test_fetch_service_offering_async_not_found(pdc_service_instance):
    """Test async service offering fetch with 404"""
    mock_response = Mock()
    mock_response.status_code = 404
    
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    
    result = await pdc_service_instance.fetch_service_offering_async(
        mock_client, 
        "https://api.example.com/service/1"
    )
    
    assert result is None


@pytest.mark.asyncio
async def test_fetch_ecosystem_async(pdc_service_instance, mock_pdc_ecosystem):
    """Test async ecosystem fetch"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_pdc_ecosystem
    
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    
    result = await pdc_service_instance.fetch_ecosystem_async(
        mock_client, 
        "https://api.example.com/ecosystem/1"
    )
    
    assert isinstance(result, PdcEcosystem)
    assert result.name == "Test Ecosystem"


@pytest.mark.asyncio
async def test_fetch_participant_async(pdc_service_instance, mock_pdc_participant):
    """Test async participant fetch"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_pdc_participant
    
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    
    result = await pdc_service_instance.fetch_participant_async(
        mock_client, 
        "https://api.example.com/participant/1"
    )
    
    assert result == mock_pdc_participant


@pytest.mark.asyncio
async def test_fetch_participant_async_not_found(pdc_service_instance):
    """Test async participant fetch with 404"""
    mock_response = Mock()
    mock_response.status_code = 404
    
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    
    result = await pdc_service_instance.fetch_participant_async(
        mock_client, 
        "https://api.example.com/participant/1"
    )
    
    assert result is None


# ============================================
# INTEGRATION TESTS
# ============================================

@pytest.mark.asyncio
async def test_pdc_service_singleton_pattern(pdc_service_instance):
    """Test PDCService follows singleton pattern"""
    another_instance = PdcService()
    
    # Should be the same instance
    assert pdc_service_instance is another_instance


@pytest.mark.asyncio
async def test_full_service_chain_workflow(pdc_service_instance):
    """Test complete service chain data workflow"""
    service_chain_id = "workflow_test"
    data = {"step": 1, "status": "active"}
    
    # Store
    stored = await pdc_service_instance.store_servicechain_data(service_chain_id, data, [USER_ID])
    assert stored is True
    
    # Retrieve
    retrieved = await pdc_service_instance.get_servicechain_data(service_chain_id, USER_ID)
    assert retrieved["data"] == data
    
    # Update
    updated_data = {"step": 2, "status": "completed"}
    await pdc_service_instance.store_servicechain_data(service_chain_id, updated_data, [USER_ID])
    
    # Verify update
    updated = await pdc_service_instance.get_servicechain_data(service_chain_id, USER_ID)
    assert updated["data"]["step"] == 2
    
    # Delete
    deleted = await pdc_service_instance.delete_servicechain_data(service_chain_id, USER_ID)
    assert deleted is True
    
    # Verify deletion
    after_delete = await pdc_service_instance.get_servicechain_data(service_chain_id, USER_ID)
    assert after_delete is None
