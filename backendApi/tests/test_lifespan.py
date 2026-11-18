"""
Tests for the application startup and shutdown (database and services mocked).
"""
import logging
from contextlib import ExitStack
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app import main

pytestmark = pytest.mark.asyncio


class Startup:
    """Patches everything the lifespan calls; each attribute can be changed before running."""

    def __init__(self):
        self.connect = AsyncMock()
        self.disconnect = AsyncMock()
        self.count = AsyncMock(return_value=3)
        self.reencrypt = AsyncMock(return_value={"reencrypted": 0, "failed": 0})
        self.ensure_admin = AsyncMock(return_value=Mock(username="admin"))
        self.migrate = AsyncMock(return_value=True)
        self.config_ini = False

    async def run(self):
        with ExitStack() as stack:
            stack.enter_context(patch.object(main.db_config, "connect", self.connect))
            stack.enter_context(patch.object(main.db_config, "disconnect", self.disconnect))
            stack.enter_context(patch.object(main.Dataset, "count", self.count))
            stack.enter_context(patch.object(main, "reencrypt_sensitive_fields", self.reencrypt))
            stack.enter_context(patch.object(main, "UserService", Mock(return_value=Mock(ensure_admin_exists=self.ensure_admin))))
            stack.enter_context(patch.object(main.MigrationService, "migrate_from_config_ini", self.migrate))
            stack.enter_context(patch.object(main.os.path, "exists", Mock(return_value=self.config_ini)))
            stack.enter_context(patch.object(main, "log_temporary_secrets"))
            async with main.lifespan(main.app):
                pass


@pytest.fixture
def startup(caplog):
    caplog.set_level(logging.INFO)
    return Startup()


async def test_startup_connects_then_shutdown_disconnects(startup, caplog):
    await startup.run()
    startup.connect.assert_awaited_once()
    startup.disconnect.assert_awaited_once()
    startup.migrate.assert_not_awaited()
    assert "Beanie test after init: 3 datasets found" in caplog.text
    assert "Admin user available: admin" in caplog.text
    assert "No config.ini found, skipping migration" in caplog.text
    assert "startup completed successfully" in caplog.text
    assert "Application shutdown completed successfully" in caplog.text


async def test_failed_database_connection_stops_the_startup(startup, caplog):
    startup.connect.side_effect = RuntimeError("mongo is down")
    with pytest.raises(RuntimeError, match="mongo is down"):
        await startup.run()
    assert "Critical error during startup: mongo is down" in caplog.text
    startup.reencrypt.assert_not_awaited()
    startup.disconnect.assert_not_awaited()


async def test_failed_database_test_does_not_stop_the_startup(startup, caplog):
    startup.count.side_effect = RuntimeError("no collection")
    await startup.run()
    assert "Beanie test failed: no collection" in caplog.text
    startup.reencrypt.assert_awaited_once()
    assert "startup completed successfully" in caplog.text


async def test_reencryption_results_are_logged(startup, caplog):
    startup.reencrypt.return_value = {"reencrypted": 2, "failed": 1}
    await startup.run()
    assert "2 sensitive dataset field(s) re-encrypted" in caplog.text
    assert "1 sensitive dataset field(s) cannot be decrypted" in caplog.text


async def test_failed_reencryption_does_not_stop_the_startup(startup, caplog):
    startup.reencrypt.side_effect = RuntimeError("bad key")
    await startup.run()
    assert "Re-encryption of sensitive dataset fields failed: bad key" in caplog.text
    startup.ensure_admin.assert_awaited_once()
    assert "startup completed successfully" in caplog.text


async def test_config_ini_is_migrated_with_the_admin(startup, caplog):
    startup.config_ini = True
    await startup.run()
    startup.migrate.assert_awaited_once_with(startup.ensure_admin.return_value)
    assert "Migration completed successfully" in caplog.text


async def test_migration_with_warnings_is_reported(startup, caplog):
    startup.config_ini = True
    startup.migrate.return_value = False
    await startup.run()
    assert "Migration completed with warnings" in caplog.text


@pytest.mark.parametrize("ensure_admin", [AsyncMock(return_value=None), AsyncMock(side_effect=RuntimeError("no user"))])
async def test_config_ini_is_not_migrated_without_admin(startup, caplog, ensure_admin):
    startup.config_ini = True
    startup.ensure_admin = ensure_admin
    await startup.run()
    startup.migrate.assert_not_awaited()
    assert "Cannot run migration: Admin user not available" in caplog.text
    assert "startup completed successfully" in caplog.text


async def test_failed_admin_check_is_logged(startup, caplog):
    startup.ensure_admin.side_effect = RuntimeError("no user")
    await startup.run()
    assert "Failed to ensure admin exists: no user" in caplog.text


async def test_failed_migration_stops_the_startup(startup, caplog):
    startup.config_ini = True
    startup.migrate.side_effect = RuntimeError("bad config")
    with pytest.raises(RuntimeError, match="bad config"):
        await startup.run()
    assert "Critical error during startup: bad config" in caplog.text


async def test_failed_disconnection_is_logged(startup, caplog):
    startup.disconnect.side_effect = RuntimeError("already closed")
    await startup.run()
    assert "Error during shutdown: already closed" in caplog.text
