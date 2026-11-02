"""
Tests of the Elasticsearch routes (dataset access and Elasticsearch mocked).
"""
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.middleware.auth import get_current_active_user
from app.models.interface.dataset_interface import ElasticDataset, MongoDataset
from app.routes import elastic
from app.services.elastic_service import ElasticServiceError


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(elastic.router)

    @app.exception_handler(ElasticServiceError)
    async def handler(request, exc):
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

    app.dependency_overrides[get_current_active_user] = lambda: Mock(username="alice")
    return TestClient(app)


@pytest.fixture
def dataset():
    ds = ElasticDataset.model_construct(id="ds1", type="elastic", name="es", url="https://es.example.com")
    with patch.object(elastic.dataset_service, "get_dataset", AsyncMock(return_value=ds)) as get_dataset:
        get_dataset.dataset = ds
        yield get_dataset


@pytest.fixture
def es():
    with patch.object(elastic, "elastic_service") as service:
        yield service


def test_info(client, dataset, es):
    es.info.return_value = {"clusterName": "c", "version": "8.15.5"}
    response = client.get("/datasets/ds1/elastic/info")
    assert response.status_code == 200
    assert response.json()["version"] == "8.15.5"
    assert dataset.call_args.args[0] == "ds1"
    assert dataset.call_args.args[1].username == "alice"


def test_access_denied_is_kept(client, es):
    with patch.object(elastic.dataset_service, "get_dataset",
                      AsyncMock(side_effect=HTTPException(status_code=403, detail="Access denied"))):
        response = client.get("/datasets/ds1/elastic/indices")
    assert response.status_code == 403
    es.list_indices.assert_not_called()


def test_not_an_elastic_dataset(client, es):
    mongo = MongoDataset.model_construct(id="ds1", type="mongo", name="m")
    with patch.object(elastic.dataset_service, "get_dataset", AsyncMock(return_value=mongo)):
        response = client.get("/datasets/ds1/elastic/info")
    assert response.status_code == 400


def test_list_indices_hidden(client, dataset, es):
    es.list_indices.return_value = [{"index": "products"}]
    response = client.get("/datasets/ds1/elastic/indices", params={"includeHidden": "true"})
    assert response.status_code == 200
    assert es.list_indices.call_args.args[1] is True


@pytest.mark.parametrize("index", ["*", "UPPER", "_all"])
def test_mapping_invalid_index(client, dataset, es, index):
    response = client.get(f"/datasets/ds1/elastic/indices/{index}/mapping")
    assert response.status_code == 422
    es.get_mapping.assert_not_called()


def test_elastic_error_status_is_returned(client, dataset, es):
    es.get_mapping.side_effect = ElasticServiceError("Not found: no such index", 404)
    response = client.get("/datasets/ds1/elastic/indices/nope/mapping")
    assert response.status_code == 404
    assert response.json()["detail"] == "Not found: no such index"


def test_create_index_owner_only(client, dataset, es):
    with patch.object(elastic.user_service, "can_modify_dataset", AsyncMock(return_value=False)):
        response = client.post("/datasets/ds1/elastic/indices", json={"index": "new"})
    assert response.status_code == 403
    es.create_index.assert_not_called()


def test_create_index(client, dataset, es):
    with patch.object(elastic.user_service, "can_modify_dataset", AsyncMock(return_value=True)):
        response = client.post("/datasets/ds1/elastic/indices",
                               json={"index": "new", "mappings": {"properties": {}}})
    assert response.status_code == 201
    assert es.create_index.call_args.args[1:] == ("new", {"properties": {}}, None)


def test_no_index_deletion_route(client, dataset, es):
    assert client.delete("/datasets/ds1/elastic/indices/products").status_code in (404, 405)


def test_query(client, dataset, es):
    es.search_page.return_value = ([{"_id": "1"}], 42)
    response = client.post("/datasets/ds1/elastic/query",
                           json={"index": "products", "query": "a:1", "page": 2, "size": 10, "fields": ["a"]})
    assert response.status_code == 200
    assert response.json() == {"total": 42, "data": [{"_id": "1"}]}
    assert es.search_page.call_args.args[1:] == ("products", 2, 10, "a:1", True, ["a"])


@pytest.mark.parametrize("body", [{"index": "products", "size": 101}, {"index": "products", "page": 0}, {"index": ""}])
def test_query_validation(client, dataset, es, body):
    assert client.post("/datasets/ds1/elastic/query", json=body).status_code == 422


def test_sample(client, dataset, es):
    es.sample_dataframe.return_value = pd.DataFrame([{"_id": "1", "a": 1}])
    response = client.post("/datasets/ds1/elastic/sample", json={"index": "products", "size": 5, "includeId": False})
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "products"
    assert body["dataExample"] == {"_id": {"0": "1"}, "a": {"0": 1}}
    assert es.sample_dataframe.call_args.args[1:] == ("products", 5, None, None, False)
