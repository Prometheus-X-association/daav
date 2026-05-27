import pytest

from app.models.interface.dataset_interface import MysqlDataset


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