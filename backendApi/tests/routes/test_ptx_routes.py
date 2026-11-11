"""
Tests of the Prometheus-X routes (the HTTP calls to the PDC and the catalog are mocked).
"""
import threading
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.models.interface.dataset_interface import PTXDataset
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
