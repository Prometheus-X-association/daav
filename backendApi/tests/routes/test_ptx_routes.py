"""
Tests of the Prometheus-X routes (the HTTP calls to the PDC and the catalog are mocked).
"""
import threading
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException

from app.models.interface.dataset_interface import MongoDataset, PTXDataset
from app.routes import ptx


def ptx_connection():
    return PTXDataset.model_construct(id=None, type="ptx", name="p", url="https://pdc.example", token="token")


def http_response(status_code=200, json_data=None, content_type="application/json"):
    response = Mock(status_code=status_code, headers={"Content-Type": content_type}, text="")
    response.json.return_value = json_data
    return response


@pytest.mark.asyncio
async def test_pdc_get_request_runs_outside_event_loop_thread():
    """The synchronous requests call of pdc_get_request runs in a worker thread, not in the event loop thread"""
    request_threads = []

    def fake_get(*args, **kwargs):
        request_threads.append(threading.current_thread())
        return http_response(json_data={"content": {}})

    with patch.object(ptx.requests, "get", side_effect=fake_get):
        result = await ptx.pdc_get_request(ptx_connection(), "/", timeout_seconds=30)

    assert result == {"content": {}}
    assert request_threads and request_threads[0] is not threading.current_thread()


@pytest.mark.asyncio
async def test_data_resources_are_fetched_outside_event_loop_thread():
    """get_data_resources fetches each data resource in a worker thread"""
    request_threads = []

    def fake_get(*args, **kwargs):
        request_threads.append(threading.current_thread())
        return http_response(json_data={"@id": "resource-1"})

    pdc_data = {"content": {"ptx:catalog": [{"@type": "ptx:dataresources", "@id": "https://catalog/resource-1"}]}}
    with patch.object(ptx.dataset_service, "get_dataset", AsyncMock(return_value=ptx_connection())), \
         patch.object(ptx, "pdc_get_request", AsyncMock(return_value=pdc_data)), \
         patch.object(ptx.PdcDataResource, "model_validate", side_effect=lambda res: res), \
         patch.object(ptx.requests, "get", side_effect=fake_get):
        result = await ptx.get_data_resources("connection-id", Mock(username="alice"), timeout_seconds=30)

    assert result == {"dataResources": [{"@id": "resource-1"}]}
    assert request_threads and request_threads[0] is not threading.current_thread()


class _StopAfterDecoding(Exception):
    pass


@pytest.mark.asyncio
async def test_pdc_input_with_invalid_json_body_is_kept_as_raw_data():
    """A body announced as JSON but not parseable used to raise a NameError (data was never set)"""
    request = Mock()
    request.headers = {"Content-Type": "application/json"}
    request.json = AsyncMock(side_effect=ValueError("invalid JSON"))
    request.body = AsyncMock(return_value=b"not json")
    decoded = []

    def fake_decode(data):
        decoded.append(data)
        raise _StopAfterDecoding()

    with patch.object(ptx.user_service, "get_all_users", AsyncMock(return_value=[])), \
         patch.object(ptx, "authenticate_m2m_credentials", return_value=[{"user": Mock(), "matched_credentials": []}]), \
         patch.object(ptx, "decode_dictionary", side_effect=fake_decode):
        with pytest.raises(_StopAfterDecoding):
            await ptx.read_input(request, Mock(), Mock())

    assert decoded == [b"not json"]


def thread_recorder(threads, return_value=None):
    """Fake synchronous PDC service method recording the thread it runs in"""
    def fake(*args, **kwargs):
        threads.append(threading.current_thread())
        return return_value
    return fake


def assert_off_event_loop(threads, expected_calls=1):
    assert len(threads) == expected_calls
    assert all(thread is not threading.current_thread() for thread in threads)


PDC_CONFIG = {"catalogUri": "https://catalog/", "contractUri": "https://contract/", "endpoint": "https://pdc/"}


@pytest.mark.asyncio
async def test_update_data_resource_fetches_the_resource_outside_event_loop_thread():
    """update_data_resource fetches the data resource from the catalog in a worker thread"""
    threads = []
    representation = Mock(id="representation-1")
    representation.model_dump_json.return_value = "{}"
    request = Mock()
    request.json = AsyncMock(return_value={"dataResourceId": "resource-1", "newUrl": "https://new"})
    client = AsyncMock()
    client.put.return_value = http_response(json_data={"updated": True})
    async_client = MagicMock()
    async_client.return_value.__aenter__.return_value = client

    with patch.object(ptx.dataset_service, "get_dataset", AsyncMock(return_value=ptx_connection())), \
         patch.object(ptx, "get_private_configuration", AsyncMock(return_value=PDC_CONFIG)), \
         patch.object(ptx.pdc_service, "fetch_dataResource",
                      side_effect=thread_recorder(threads, Mock(representation=representation))), \
         patch.object(ptx.httpx, "AsyncClient", async_client):
        result = await ptx.update_data_resource("connection-id", request, Mock(username="alice"), timeout_seconds=30)

    assert result == {"response": {"updated": True}}
    assert representation.url == "https://new"
    assert_off_event_loop(threads)


@pytest.mark.asyncio
async def test_pdc_input_fetches_the_contract_outside_event_loop_thread():
    """The PDC input endpoint fetches the contract and the provider name in worker threads"""
    threads = []
    request = Mock()
    request.headers = {"Content-Type": "application/json"}
    request.json = AsyncMock(return_value={"a": 1})
    contract = Mock(id="contract-1")

    with patch.object(ptx.user_service, "get_all_users", AsyncMock(return_value=[])), \
         patch.object(ptx, "authenticate_m2m_credentials", return_value=[{"user": Mock(), "matched_credentials": []}]), \
         patch.object(ptx.pdc_service, "fetch_contract", side_effect=thread_recorder(threads, contract)), \
         patch.object(ptx.pdc_service, "get_provider_name_from_contract", side_effect=thread_recorder(threads, "provider")), \
         patch.object(ptx, "serialize_data", side_effect=_StopAfterDecoding()):
        with pytest.raises(_StopAfterDecoding):
            await ptx.read_input(request, Mock(), Mock(x_ptx_contracturl="https://contract/contracts/1"))

    assert_off_event_loop(threads, expected_calls=2)


@pytest.mark.asyncio
async def test_service_chain_fetches_the_ecosystem_outside_event_loop_thread():
    """get_service_chain fetches the ecosystem of each contract in a worker thread"""
    threads = []
    ecosystem = Mock(orchestrator="participant-1", serviceChains=["chain-1"])

    with patch.object(ptx.dataset_service, "get_dataset", AsyncMock(return_value=ptx_connection())), \
         patch.object(ptx, "get_private_configuration", AsyncMock(return_value=PDC_CONFIG)), \
         patch.object(ptx, "get_participants_id_from_connection", AsyncMock(return_value=["participant-1"])), \
         patch.object(ptx.requests, "get", return_value=http_response(json_data={"contracts": [{}]})), \
         patch.object(ptx.PdcContract, "model_validate", return_value=Mock(id="contract-1", ecosystem="https://eco")), \
         patch.object(ptx.pdc_service, "fetch_ecosystem", side_effect=thread_recorder(threads, ecosystem)):
        result = await ptx.get_service_chain("connection-id", Mock(username="alice"), timeout_seconds=30)

    assert result == [{"contract_id": "contract-1", "service_chains": ["chain-1"]}]
    assert_off_event_loop(threads)


@pytest.mark.asyncio
async def test_bilateral_contracts_fetch_the_provider_outside_event_loop_thread():
    """get_billateral_contract fetches the provider name and image of each contract in a worker thread"""
    threads = []
    contract = Mock()

    with patch.object(ptx.dataset_service, "get_dataset", AsyncMock(return_value=ptx_connection())), \
         patch.object(ptx, "get_private_configuration", AsyncMock(return_value=PDC_CONFIG)), \
         patch.object(ptx, "get_participants_id_from_connection", AsyncMock(return_value=["participant-1"])), \
         patch.object(ptx.requests, "get", return_value=http_response(json_data={"contracts": [{}]})), \
         patch.object(ptx.PdcContractBilateral, "model_validate", return_value=contract), \
         patch.object(ptx.pdc_service, "get_provider_name_and_img_from_contract",
                      side_effect=thread_recorder(threads, {"name": "Provider", "img": "logo.png"})):
        result = await ptx.get_billateral_contract("connection-id", Mock(username="alice"), timeout_seconds=30)

    assert result["contracts"] == [contract]
    assert (contract.name, contract.img) == ("Provider", "logo.png")
    assert_off_event_loop(threads)


@pytest.mark.asyncio
async def test_service_offering_is_fetched_outside_event_loop_thread():
    threads = []
    offering = Mock()

    with patch.object(ptx, "get_private_configuration", AsyncMock(return_value=PDC_CONFIG)), \
         patch.object(ptx.pdc_service, "fetch_service_offering", side_effect=thread_recorder(threads, offering)) as fetch:
        result = await ptx.get_serviceoffering_by_id("offering-1", ptx_connection())

    assert result is offering
    fetch.assert_called_once_with("https://catalog/catalog/serviceofferings/offering-1")
    assert_off_event_loop(threads)


# Client errors raised inside the try blocks of the routes used to be turned into 500


def pdc_unauthorized():
    return HTTPException(status_code=401, detail="PTX token invalid or expired for this connection.")


@pytest.mark.asyncio
async def test_update_data_resource_of_a_non_ptx_connection_is_a_400():
    connection = MongoDataset.model_construct(id=None, type="mongo", name="m")

    with patch.object(ptx.dataset_service, "get_dataset", AsyncMock(return_value=connection)):
        with pytest.raises(HTTPException) as error:
            await ptx.update_data_resource("connection-id", Mock(), Mock(username="alice"), timeout_seconds=30)

    assert error.value.status_code == 400
    assert error.value.detail == "Invalid connection type. Expected PTXDataset."


@pytest.mark.asyncio
async def test_data_resources_with_an_expired_pdc_token_is_a_401():
    with patch.object(ptx.dataset_service, "get_dataset", AsyncMock(return_value=ptx_connection())), \
         patch.object(ptx, "pdc_get_request", AsyncMock(side_effect=pdc_unauthorized())):
        with pytest.raises(HTTPException) as error:
            await ptx.get_data_resources("connection-id", Mock(username="alice"), timeout_seconds=30)

    assert error.value.status_code == 401
    assert error.value.detail.startswith("PTX token invalid")


@pytest.mark.asyncio
async def test_data_resources_of_a_missing_connection_is_a_404():
    with patch.object(ptx.dataset_service, "get_dataset",
                      AsyncMock(side_effect=HTTPException(status_code=404, detail="Dataset not found"))):
        with pytest.raises(HTTPException) as error:
            await ptx.get_data_resources("connection-id", Mock(username="alice"), timeout_seconds=30)

    assert (error.value.status_code, error.value.detail) == (404, "Dataset not found")


@pytest.mark.asyncio
@pytest.mark.parametrize("route", [ptx.trigger_data_exchange, ptx.trigger_service_chain])
async def test_rejected_exchange_keeps_the_pdc_status_code(route):
    """The status code of a PDC exchange failure is returned (it used to become a 500)"""
    request = Mock()
    request.json = AsyncMock(return_value={"contract": "contract-1", "contractId": "contract-1"})
    client = AsyncMock()
    client.post.return_value = Mock(status_code=409, text="already running")
    async_client = MagicMock()
    async_client.return_value.__aenter__.return_value = client

    with patch.object(ptx.dataset_service, "get_dataset", AsyncMock(return_value=ptx_connection())), \
         patch.object(ptx, "get_private_configuration", AsyncMock(return_value=PDC_CONFIG)), \
         patch.object(ptx.httpx, "AsyncClient", async_client):
        with pytest.raises(HTTPException) as error:
            await route("connection-id", request, Mock(username="alice"), timeout_seconds=30)

    assert (error.value.status_code, error.value.detail) == (409, "Data exchange failed: already running")


@pytest.mark.asyncio
async def test_bilateral_contracts_with_an_expired_pdc_token_is_a_401():
    with patch.object(ptx.dataset_service, "get_dataset", AsyncMock(return_value=ptx_connection())), \
         patch.object(ptx, "get_private_configuration", AsyncMock(side_effect=pdc_unauthorized())):
        with pytest.raises(HTTPException) as error:
            await ptx.get_billateral_contract("connection-id", Mock(username="alice"), timeout_seconds=30)

    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_bilateral_contracts_keep_the_client_error_of_the_participants_lookup():
    with patch.object(ptx.dataset_service, "get_dataset", AsyncMock(return_value=ptx_connection())), \
         patch.object(ptx, "get_private_configuration", AsyncMock(return_value=PDC_CONFIG)), \
         patch.object(ptx, "get_participants_id_from_connection", AsyncMock(side_effect=pdc_unauthorized())):
        with pytest.raises(HTTPException) as error:
            await ptx.get_billateral_contract("connection-id", Mock(username="alice"), timeout_seconds=30)

    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_bilateral_contracts_without_participants_is_still_a_500():
    """Unexpected errors keep their 500 response"""
    with patch.object(ptx.dataset_service, "get_dataset", AsyncMock(return_value=ptx_connection())), \
         patch.object(ptx, "get_private_configuration", AsyncMock(return_value=PDC_CONFIG)), \
         patch.object(ptx, "get_participants_id_from_connection", AsyncMock(return_value=None)):
        with pytest.raises(HTTPException) as error:
            await ptx.get_billateral_contract("connection-id", Mock(username="alice"), timeout_seconds=30)

    assert error.value.status_code == 500
    assert error.value.detail == "Error retrieving participants: No participants found for this connection"
