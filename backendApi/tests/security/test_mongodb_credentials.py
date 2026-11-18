"""
Tests for the MongoDB credentials read from MONGODB_PASSWORD_FILE (Docker secret)
"""

from types import SimpleNamespace

import pytest

from app.config.database import mongodb_credentials


def make_settings(username=None, password_file=None):
    return SimpleNamespace(mongodb_username=username, mongodb_password_file=password_file)


def test_no_password_file_uses_url_only():
    """Without MONGODB_PASSWORD_FILE, the credentials (if any) come from MONGODB_URL"""
    assert mongodb_credentials(make_settings()) == {}


def test_password_read_from_file(tmp_path):
    """The password is read from the file, without the trailing newline"""
    password_file = tmp_path / "mongo_root_password"
    password_file.write_text("s3cret_from-file\n")

    credentials = mongodb_credentials(make_settings("admin", str(password_file)))

    assert credentials == {"username": "admin", "password": "s3cret_from-file"}


def test_missing_password_file(tmp_path):
    """A missing file stops the connection with an explicit error"""
    settings = make_settings("admin", str(tmp_path / "missing"))
    with pytest.raises(RuntimeError, match="Cannot read the MongoDB password"):
        mongodb_credentials(settings)


def test_empty_password_file(tmp_path):
    """An empty file stops the connection with an explicit error"""
    password_file = tmp_path / "mongo_root_password"
    password_file.write_text("\n")

    settings = make_settings("admin", str(password_file))
    with pytest.raises(RuntimeError, match="is empty"):
        mongodb_credentials(settings)


def test_password_file_requires_username(tmp_path):
    """MONGODB_USERNAME is required with MONGODB_PASSWORD_FILE"""
    password_file = tmp_path / "mongo_root_password"
    password_file.write_text("s3cret")

    settings = make_settings(None, str(password_file))
    with pytest.raises(RuntimeError, match="MONGODB_USERNAME must be set"):
        mongodb_credentials(settings)


def test_client_accepts_separate_credentials():
    """The MongoDB client accepts credentials outside the URL (no connection is opened)"""
    from pymongo import AsyncMongoClient

    client = AsyncMongoClient(
        "mongodb://mongodb:27017/daav_datasets?authSource=admin",
        username="admin", password="s3cret", connect=False
    )
    options = client.options.pool_options._credentials
    assert options.username == "admin"
    assert options.source == "admin"
