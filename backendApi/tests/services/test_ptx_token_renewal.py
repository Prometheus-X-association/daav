"""
Tests for the renewal of the PTX tokens of a connection (PDC mocked).
"""
import threading
from unittest.mock import AsyncMock, Mock, patch

import pytest
import requests

from app.models.interface.dataset_interface import PTXDataset
from app.services.dataset_service import DatasetService

pytestmark = pytest.mark.asyncio

REFRESH_URL = "https://pdc.example.com/login/refresh"


@pytest.fixture
def service():
    return DatasetService()


def connection(**values):
    fields = {"id": "ds1", "type": "ptx", "name": "ptx", "url": "https://pdc.example.com/", "token": "old-token",
              "refreshToken": "old-refresh", "service_key": None, "secret_key": None, **values}
    dataset = PTXDataset.model_construct(**fields)
    object.__setattr__(dataset, "save", AsyncMock())
    return dataset


def pdc_response(status_code=200, content=None, content_type="application/json"):
    return Mock(status_code=status_code, headers={"Content-Type": content_type},
                json=Mock(return_value={"content": content}))


async def test_connection_without_url_is_not_renewed(service):
    dataset = connection(url=None)
    with patch("app.services.dataset_service.requests.post") as post:
        assert await service.ensure_runtime_ptx_tokens(dataset) is False
    post.assert_not_called()


async def test_refresh_token_gives_new_tokens(service):
    dataset = connection()
    refreshed = pdc_response(content={"token": "new-token", "refreshToken": "new-refresh"})
    with patch("app.services.dataset_service.requests.post", return_value=refreshed) as post:
        assert await service.ensure_runtime_ptx_tokens(dataset) is True
    post.assert_called_once_with(REFRESH_URL, json={"refreshToken": "old-refresh"}, timeout=30)
    assert dataset.token == "new-token"
    assert dataset.refreshToken == "new-refresh"
    dataset.save.assert_awaited_once()


async def test_refresh_runs_outside_the_event_loop_thread(service):
    dataset = connection()
    threads = []

    def fake_post(*args, **kwargs):
        threads.append(threading.current_thread())
        return pdc_response(content={"token": "new-token"})

    with patch("app.services.dataset_service.requests.post", side_effect=fake_post):
        assert await service.ensure_runtime_ptx_tokens(dataset) is True
    assert threads[0] is not threading.current_thread()


async def test_refresh_without_new_refresh_token_keeps_the_old_one(service):
    dataset = connection()
    with patch("app.services.dataset_service.requests.post", return_value=pdc_response(content={"token": "new-token"})):
        assert await service.ensure_runtime_ptx_tokens(dataset) is True
    assert dataset.token == "new-token"
    assert dataset.refreshToken == "old-refresh"


@pytest.mark.parametrize("refreshed", [
    pdc_response(status_code=401, content={"token": "ignored"}),
    pdc_response(content={"token": "ignored"}, content_type="text/html"),
    pdc_response(content=None),
    pdc_response(content={"refreshToken": "no-token"}),
    pdc_response(content="not a dict"),
])
async def test_refused_refresh_without_keys_is_not_renewed(service, refreshed):
    dataset = connection()
    with patch("app.services.dataset_service.requests.post", return_value=refreshed), \
         patch.object(service, "connect_pdc") as connect_pdc:
        assert await service.ensure_runtime_ptx_tokens(dataset) is False
    connect_pdc.assert_not_called()
    assert dataset.token == "old-token"
    dataset.save.assert_not_awaited()


async def test_refused_refresh_falls_back_to_a_login_with_the_keys(service):
    dataset = connection(service_key="service", secret_key="secret")
    login = {"content": {"token": "login-token", "refreshToken": "login-refresh"}}
    with patch("app.services.dataset_service.requests.post", return_value=pdc_response(status_code=401)), \
         patch.object(service, "connect_pdc", return_value=login) as connect_pdc:
        assert await service.ensure_runtime_ptx_tokens(dataset) is True
    connect_pdc.assert_called_once_with("https://pdc.example.com", "service", "secret")
    assert dataset.token == "login-token"
    assert dataset.refreshToken == "login-refresh"
    # The keys are only kept until they have given a token
    assert dataset.service_key is None
    assert dataset.secret_key is None


async def test_network_error_on_refresh_falls_back_to_a_login(service):
    dataset = connection(service_key="service", secret_key="secret")
    with patch("app.services.dataset_service.requests.post", side_effect=requests.ConnectionError("down")), \
         patch.object(service, "connect_pdc", return_value={"content": {"token": "login-token"}}):
        assert await service.ensure_runtime_ptx_tokens(dataset) is True
    assert dataset.token == "login-token"
    assert dataset.refreshToken == "old-refresh"


async def test_connection_without_refresh_token_logs_in_directly(service):
    dataset = connection(refreshToken=None, service_key="service", secret_key="secret")
    with patch("app.services.dataset_service.requests.post") as post, \
         patch.object(service, "connect_pdc", return_value={"content": {"token": "login-token"}}):
        assert await service.ensure_runtime_ptx_tokens(dataset) is True
    post.assert_not_called()


@pytest.mark.parametrize("login", [RuntimeError("down"), b"<html>", {"content": None}, {"content": {}}])
async def test_failed_login_is_not_renewed(service, login):
    dataset = connection(refreshToken=None, service_key="service", secret_key="secret")
    effect = {"side_effect": login} if isinstance(login, Exception) else {"return_value": login}
    with patch.object(service, "connect_pdc", **effect):
        assert await service.ensure_runtime_ptx_tokens(dataset) is False
    assert dataset.token == "old-token"
    # The keys stay for a later attempt
    assert dataset.service_key == "service"


async def test_tokens_that_cannot_be_saved_are_still_used(service):
    dataset = connection()
    dataset.save.side_effect = RuntimeError("database down")
    with patch("app.services.dataset_service.requests.post", return_value=pdc_response(content={"token": "new-token"})):
        assert await service.ensure_runtime_ptx_tokens(dataset) is True
    assert dataset.token == "new-token"
