"""
Tests of the MySQL dashboard routes (dataset access and MySQL mocked).
"""
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.middleware.auth import get_current_active_user
from app.models.interface.dataset_interface import MongoDataset, MysqlDataset
from app.routes import mysql
from app.services.mysql_service import MysqlServiceError


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(mysql.router)

    @app.exception_handler(MysqlServiceError)
    async def handler(request, exc):
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

    app.dependency_overrides[get_current_active_user] = lambda: Mock(username="alice")
    return TestClient(app)


def _patch_dataset(ds):
    return patch.object(mysql.dataset_service, "get_dataset", AsyncMock(return_value=ds))


@pytest.fixture
def dataset():
    ds = MysqlDataset.model_construct(id="ds1", type="mysql", name="db", host="localhost")
    with _patch_dataset(ds) as get_dataset:
        get_dataset.dataset = ds
        yield get_dataset


@pytest.fixture
def service():
    with patch.object(mysql, "mysql_service") as service:
        yield service


def test_info(client, dataset, service):
    service.info.return_value = {"version": "8.4.0", "databases": []}
    response = client.get("/datasets/ds1/mysql/info")
    assert response.status_code == 200
    assert response.json()["version"] == "8.4.0"
    assert dataset.call_args.args[0] == "ds1"
    assert dataset.call_args.args[1].username == "alice"


def test_not_a_mysql_dataset(client, service):
    with _patch_dataset(MongoDataset.model_construct(id="ds1", type="mongo", name="m")):
        response = client.get("/datasets/ds1/mysql/info")
    assert response.status_code == 400
    service.info.assert_not_called()


def test_access_denied_is_kept(client, service):
    with patch.object(mysql.dataset_service, "get_dataset",
                      AsyncMock(side_effect=HTTPException(status_code=403, detail="Access denied"))):
        response = client.get("/datasets/ds1/mysql/databases/shop/tables")
    assert response.status_code == 403
    service.list_tables.assert_not_called()


def test_list_tables(client, dataset, service):
    service.list_tables.return_value = [{"name": "orders"}]
    response = client.get("/datasets/ds1/mysql/databases/shop/tables")
    assert response.status_code == 200
    assert response.json() == [{"name": "orders"}]
    assert service.list_tables.call_args.args[1] == "shop"


def test_database_outside_the_dataset_is_refused(client, service):
    ds = MysqlDataset.model_construct(id="ds1", type="mysql", name="db", host="h", database="shop")
    with _patch_dataset(ds):
        response = client.get("/datasets/ds1/mysql/databases/other/tables/users/columns")
    assert response.status_code == 403
    service.list_columns.assert_not_called()


def test_list_columns(client, dataset, service):
    service.list_columns.return_value = [{"name": "id", "type": "int"}]
    response = client.get("/datasets/ds1/mysql/databases/shop/tables/orders/columns")
    assert response.status_code == 200
    assert service.list_columns.call_args.args[1:] == ("shop", "orders")


def test_service_error_status(client, dataset, service):
    service.info.side_effect = MysqlServiceError("MySQL refused the credentials")
    response = client.get("/datasets/ds1/mysql/info")
    assert response.status_code == 502
    assert "credentials" in response.json()["detail"]


def test_table_outside_the_dataset_is_refused(client, service):
    ds = MysqlDataset.model_construct(id="ds1", type="mysql", name="db", host="h", database="shop", table="orders")
    with _patch_dataset(ds):
        refused = client.get("/datasets/ds1/mysql/databases/shop/tables/users/columns")
        allowed = client.get("/datasets/ds1/mysql/databases/shop/tables/orders/columns")
    assert refused.status_code == 403
    assert allowed.status_code == 200
    service.list_columns.assert_called_once()
