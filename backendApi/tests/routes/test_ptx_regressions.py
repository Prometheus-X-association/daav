"""
Regression tests for the PTX routes (PDC and Visions APIs mocked).
"""
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from app.routes import ptx

pytestmark = pytest.mark.asyncio

CONFIG = {"endpoint": "https://pdc.example.com/", "catalogUri": "https://catalog.example.com/"}


def response(status_code, payload):
    return Mock(status_code=status_code, json=Mock(return_value=payload), text="")


async def test_bilateral_contracts_of_a_missing_connection_is_a_404():
    with patch.object(ptx.dataset_service, "get_dataset", AsyncMock(return_value=None)):
        current_user = Mock()
        with pytest.raises(HTTPException) as error:
            await ptx.get_billateral_contract("unknown", current_user)
    assert error.value.status_code == 404


async def test_data_exchange_resource_without_producer_is_kept():
    exchanges = {"content": [{
        "_id": "ex1", "status": "IMPORT_SUCCESS", "contract": "c1", "providerEndpoint": "https://provider",
        "createdAt": "2026-01-01T00:00:00Z", "resources": [{"resource": "https://catalog.example.com/res1"}],
    }]}
    resource = {"_id": "res1", "name": "Resource 1", "description": "d", "attributes": [],
                "createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z"}

    def fake_get(url, **kwargs):
        return response(200, exchanges if url.endswith("dataexchanges") else resource)

    with patch.object(ptx.dataset_service, "get_dataset", AsyncMock(return_value=Mock(id="ds1"))), \
         patch.object(ptx, "get_private_configuration", AsyncMock(return_value=CONFIG)), \
         patch.object(ptx.requests, "get", side_effect=fake_get), \
         patch.object(ptx.pdc_service, "fetch_participant") as fetch_participant:
        result = await ptx.get_data_exchanges("ds1", Mock(), Mock())

    fetch_participant.assert_not_called()
    assert result["dataExchanges"][0]["resources"] == [{
        "id": "res1", "name": "Resource 1", "description": "d", "owner": {"id": None, "name": None},
    }]
