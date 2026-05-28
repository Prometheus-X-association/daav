import pytest

from app.models.interface.dataset_interface import (
    MysqlDataset, MongoDataset, ElasticDataset, ApiDataset, PTXDataset
)


@pytest.mark.asyncio
async def test_replace_encrypts_sensitive_fields_and_restores_plaintext(monkeypatch):
    monkeypatch.setenv(
        "FIELD_ENCRYPTION_KEY",
        "2frZC2o4MLN2F1sSxJk7Y0Kj0I7j9N2G5Q7e4Wj7iNw=",
    )

    dataset = MysqlDataset(
        id="dataset-replace-encryption",
        name="test_mysql",
        type="mysql",
        host="db.example.com",
        database="test_db",
        table="test_table",
        user="test_user",
        password="plain-secret",
    )
    await dataset.insert()

    dataset.password = "updated-secret"
    await dataset.replace()

    assert dataset.password == "updated-secret"

    raw_document = await MysqlDataset.get_pymongo_collection().find_one({"_id": dataset.id})
    assert raw_document is not None
    assert raw_document["password"] != "updated-secret"
    assert raw_document["password"].startswith("enc:")

    reloaded_dataset = await MysqlDataset.get(dataset.id)
    assert reloaded_dataset is not None
    assert reloaded_dataset.password == "updated-secret"


@pytest.mark.parametrize(
    "dataset_class,kwargs,sensitive_fields",
    [
        (
            MysqlDataset,
            {
                "id": "dataset-mysql-serialization",
                "name": "test_mysql",
                "type": "mysql",
                "host": "db.example.com",
                "database": "test_db",
                "table": "test_table",
                "user": "test_user",
                "password": "plain-secret",
            },
            ["password"],
        ),
        (
            MongoDataset,
            {
                "id": "dataset-mongo-serialization",
                "name": "test_mongo",
                "type": "mongo",
                "uri": "mongodb://localhost:27017",
                "database": "test_db",
                "collection": "test_collection",
            },
            ["uri"],
        ),
        (
            ElasticDataset,
            {
                "id": "dataset-elastic-serialization",
                "name": "test_elastic",
                "type": "elastic",
                "url": "https://elastic.example.com",
                "user": "elastic_user",
                "password": "elastic-password",
                "index": "test-index",
                "key": "elastic-api-key",
                "bearerToken": "elastic-bearer-token",
            },
            ["password", "key", "bearerToken"],
        ),
        (
            ApiDataset,
            {
                "id": "dataset-api-serialization",
                "name": "test_api",
                "type": "api",
                "url": "https://api.example.com",
                "apiAuth": "bearer",
                "bearerToken": "api-bearer-token",
                "basicToken": "api-basic-token",
                "clientId": "client-id",
                "clientSecret": "api-client-secret",
            },
            ["bearerToken", "basicToken", "clientSecret"],
        ),
        (
            PTXDataset,
            {
                "id": "dataset-ptx-serialization",
                "name": "test_ptx",
                "type": "ptx",
                "url": "https://pdc.example.com",
                "token": "secret-token",
                "refreshToken": "secret-refresh",
                "service_key": "service-key",
                "secret_key": "secret-key",
            },
            ["token", "refreshToken", "service_key", "secret_key"],
        ),
    ],
)
def test_sensitive_fields_are_excluded_from_serialization(dataset_class, kwargs, sensitive_fields):
    dataset = dataset_class(**kwargs)
    dumped = dataset.model_dump()

    assert dumped["id"] == kwargs["id"]
    assert dumped["name"] == kwargs["name"]

    for field in sensitive_fields:
        assert field not in dumped


def test_sensitive_fields_are_excluded_from_serialization():
    from app.models.interface.dataset_interface import PTXDataset

    dataset = PTXDataset(
        id="dataset-ptx-serialization",
        name="test_ptx",
        type="ptx",
        url="https://pdc.example.com",
        token="secret-token",
        refreshToken="secret-refresh",
        service_key="service-key",
        secret_key="secret-key",
    )

    assert dataset.token == "secret-token"
    assert dataset.refreshToken == "secret-refresh"
    assert dataset.service_key == "service-key"
    assert dataset.secret_key == "secret-key"

    dumped = dataset.model_dump()

    assert dumped["id"] == "dataset-ptx-serialization"
    assert dumped["name"] == "test_ptx"
    assert dumped["url"] == "https://pdc.example.com"

    assert "token" not in dumped
    assert "refreshToken" not in dumped
    assert "service_key" not in dumped
    assert "secret_key" not in dumped