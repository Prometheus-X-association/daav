"""
Tests for the re-encryption of sensitive dataset fields with the current FIELD_ENCRYPTION_KEY.
"""
import pytest
from cryptography.fernet import Fernet, InvalidToken

from app.config.secret_keys import PUBLIC_DEFAULT_JWT_SECRETS
from app.config.settings import settings
from app.models.interface.dataset_interface import Dataset, MysqlDataset
from app.services.reencryption_service import reencrypt_sensitive_fields
from app.utils import encryption
from app.utils.encryption import _derive_key_from_jwt, decrypt_field, reencrypt_field


def _encrypt_with(key: bytes, value: str) -> str:
    return "enc:" + Fernet(key).encrypt(value.encode()).decode()


def _decrypt_with_current_key(value: str) -> str:
    return Fernet(settings.field_encryption_key.encode()).decrypt(value[len("enc:"):].encode()).decode()


@pytest.fixture(autouse=True)
def clear_key_caches():
    encryption._read_tmp_field_key.cache_clear()
    encryption._build_fernets.cache_clear()
    yield
    encryption._read_tmp_field_key.cache_clear()
    encryption._build_fernets.cache_clear()


@pytest.mark.parametrize("previous_key", [
    _derive_key_from_jwt(PUBLIC_DEFAULT_JWT_SECRETS[1]),  # former docker-compose default
    _derive_key_from_jwt(settings.jwt_secret_key),  # former fallback when FIELD_ENCRYPTION_KEY was unset
])
def test_value_encrypted_with_previous_key_is_readable_and_reencrypted(previous_key):
    old_value = _encrypt_with(previous_key, "db-password")

    assert decrypt_field(old_value) == "db-password"
    new_value = reencrypt_field(old_value)
    assert _decrypt_with_current_key(new_value) == "db-password"


def test_value_encrypted_with_tmp_key_is_reencrypted_after_key_change(tmp_path, monkeypatch):
    tmp_key = Fernet.generate_key()
    (tmp_path / "FIELD_ENCRYPTION_KEY_TMP").write_text(tmp_key.decode() + "\n")
    monkeypatch.setattr(settings, "secrets_dir", str(tmp_path))

    new_value = reencrypt_field(_encrypt_with(tmp_key, "api-token"))

    assert _decrypt_with_current_key(new_value) == "api-token"


def test_value_already_using_current_key_is_left_unchanged():
    assert reencrypt_field(encryption.encrypt_field("secret")) is None


def test_plain_text_value_is_encrypted():
    assert _decrypt_with_current_key(reencrypt_field("plain-secret")) == "plain-secret"


def test_value_encrypted_with_unknown_key_raises():
    with pytest.raises(InvalidToken):
        reencrypt_field(_encrypt_with(Fernet.generate_key(), "lost"))


@pytest.mark.asyncio
async def test_reencrypt_sensitive_fields_migrates_stored_datasets():
    collection = Dataset.get_pymongo_collection()
    legacy_key = _derive_key_from_jwt(PUBLIC_DEFAULT_JWT_SECRETS[0])
    await collection.insert_many([
        {"_id": "legacy", "type": "mysql", "name": "legacy", "password": _encrypt_with(legacy_key, "pwd-1")},
        {"_id": "plain", "type": "mysql", "name": "plain", "password": "pwd-2"},
        {"_id": "lost", "type": "mysql", "name": "lost", "password": _encrypt_with(Fernet.generate_key(), "x")},
        {"_id": "elastic", "type": "elastic", "name": "elastic", "bearerToken": _encrypt_with(legacy_key, "tok")},
        {"_id": "file", "type": "file", "name": "file", "password": "not-a-sensitive-field-for-files"},
    ])

    counts = await reencrypt_sensitive_fields()

    assert counts == {"reencrypted": 3, "failed": 1}
    assert _decrypt_with_current_key((await collection.find_one({"_id": "legacy"}))["password"]) == "pwd-1"
    assert _decrypt_with_current_key((await collection.find_one({"_id": "plain"}))["password"]) == "pwd-2"
    assert _decrypt_with_current_key((await collection.find_one({"_id": "elastic"}))["bearerToken"]) == "tok"
    assert (await collection.find_one({"_id": "file"}))["password"] == "not-a-sensitive-field-for-files"
    assert (await MysqlDataset.get("legacy")).password == "pwd-1"

    # Idempotent: nothing left to re-encrypt
    assert await reencrypt_sensitive_fields() == {"reencrypted": 0, "failed": 1}
