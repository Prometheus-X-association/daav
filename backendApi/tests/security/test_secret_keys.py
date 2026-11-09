"""
Tests for the application secrets (JWT_SECRET_KEY, FIELD_ENCRYPTION_KEY):
no default value, temporary keys generated in SECRETS_DIR, error logged until configured.
"""
import logging
import os
import stat
from concurrent.futures import ThreadPoolExecutor

import pytest
from cryptography.fernet import Fernet

from app.config.secret_keys import (
    PUBLIC_DEFAULT_JWT_SECRETS,
    load_or_create_tmp_secret,
    log_temporary_secrets,
    tmp_secret_path,
)
from app.config.settings import Settings


@pytest.fixture
def no_configured_secrets(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.delenv("FIELD_ENCRYPTION_KEY", raising=False)


def test_tmp_secret_is_generated_once_and_owner_only(tmp_path):
    value = load_or_create_tmp_secret("JWT_SECRET_KEY", str(tmp_path))

    path = tmp_secret_path("JWT_SECRET_KEY", str(tmp_path))
    assert path.name == "JWT_SECRET_KEY_TMP"
    assert len(value) >= 32
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
    assert load_or_create_tmp_secret("JWT_SECRET_KEY", str(tmp_path)) == value
    # Only the published file remains (no leftover temp file)
    assert [p.name for p in tmp_path.iterdir()] == ["JWT_SECRET_KEY_TMP"]


def test_tmp_secret_is_shared_by_concurrent_workers(tmp_path):
    with ThreadPoolExecutor(max_workers=8) as executor:
        values = list(executor.map(
            lambda _: load_or_create_tmp_secret("FIELD_ENCRYPTION_KEY", str(tmp_path)), range(16)
        ))

    assert len(set(values)) == 1
    Fernet(values[0].encode())  # valid Fernet key


def test_tmp_secret_unwritable_dir_raises_explicit_error(tmp_path):
    blocker = tmp_path / "not_a_directory"
    blocker.write_text("")

    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY is not set"):
        load_or_create_tmp_secret("JWT_SECRET_KEY", str(blocker / "secrets"))


def test_settings_without_secrets_use_temporary_keys(tmp_path, no_configured_secrets):
    settings = Settings(_env_file=None, secrets_dir=str(tmp_path))

    assert set(settings.temporary_secrets) == {"JWT_SECRET_KEY", "FIELD_ENCRYPTION_KEY"}
    assert settings.jwt_secret_key == tmp_secret_path("JWT_SECRET_KEY", str(tmp_path)).read_text().strip()
    assert settings.field_encryption_key == tmp_secret_path("FIELD_ENCRYPTION_KEY", str(tmp_path)).read_text().strip()

    # Same keys after a restart
    restarted = Settings(_env_file=None, secrets_dir=str(tmp_path))
    assert restarted.jwt_secret_key == settings.jwt_secret_key
    assert restarted.field_encryption_key == settings.field_encryption_key


def test_settings_with_configured_secrets_generate_nothing(tmp_path, no_configured_secrets):
    key = Fernet.generate_key().decode()
    settings = Settings(
        _env_file=None,
        secrets_dir=str(tmp_path),
        jwt_secret_key="a-configured-jwt-secret-with-more-than-32-chars",
        field_encryption_key=key,
    )

    assert settings.temporary_secrets == {}
    assert settings.field_encryption_key == key
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("public_value", PUBLIC_DEFAULT_JWT_SECRETS)
def test_public_placeholder_jwt_secret_is_refused(tmp_path, no_configured_secrets, public_value):
    settings = Settings(_env_file=None, secrets_dir=str(tmp_path), jwt_secret_key=public_value)

    assert settings.jwt_secret_key != public_value
    assert "JWT_SECRET_KEY" in settings.temporary_secrets


def test_empty_secrets_are_treated_as_not_set(tmp_path, no_configured_secrets):
    settings = Settings(_env_file=None, secrets_dir=str(tmp_path), jwt_secret_key="", field_encryption_key="")

    assert set(settings.temporary_secrets) == {"JWT_SECRET_KEY", "FIELD_ENCRYPTION_KEY"}


def test_log_temporary_secrets_explains_what_to_do(caplog):
    with caplog.at_level(logging.ERROR, logger="app.config.secret_keys"):
        log_temporary_secrets({"FIELD_ENCRYPTION_KEY": "/app/secrets/FIELD_ENCRYPTION_KEY_TMP"})

    assert len(caplog.records) == 1
    message = caplog.records[0].getMessage()
    assert caplog.records[0].levelno == logging.ERROR
    assert "/app/secrets/FIELD_ENCRYPTION_KEY_TMP" in message
    assert "Copy this value to FIELD_ENCRYPTION_KEY" in message
    assert "secrets vault" in message
