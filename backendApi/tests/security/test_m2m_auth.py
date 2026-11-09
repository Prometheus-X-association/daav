"""
Tests for the M2M authentication of PDC requests (credentials matched against request headers)
"""

import pytest
from fastapi.datastructures import Headers

from app.models.interface.user_interface import UserConfig
from app.utils.auth_utils import authenticate_m2m_credentials


@pytest.fixture
def m2m_user(mock_user):
    mock_user.config = UserConfig(credentials={"x-api-key": "secret-value"})
    return mock_user


@pytest.mark.asyncio
async def test_matching_credentials_authenticate(m2m_user):
    """Test that a header matching a configured credential authenticates the user"""
    result = await authenticate_m2m_credentials(Headers({"X-Api-Key": "secret-value"}), [m2m_user])

    assert len(result) == 1
    assert result[0]["user"] is m2m_user
    assert result[0]["matched_credentials"] == {"x-api-key": "secret-value"}


@pytest.mark.asyncio
@pytest.mark.parametrize("headers", [{"x-api-key": "wrong"}, {"x-api-key": ""}, {}])
async def test_wrong_or_missing_credentials_rejected(m2m_user, headers):
    """Test that a wrong, empty or missing header does not authenticate the user"""
    assert await authenticate_m2m_credentials(Headers(headers), [m2m_user]) == []


@pytest.mark.asyncio
async def test_inactive_user_rejected(m2m_user):
    """Test that a deactivated account cannot be used through its M2M credentials"""
    m2m_user.is_active = False

    assert await authenticate_m2m_credentials(Headers({"x-api-key": "secret-value"}), [m2m_user]) == []
