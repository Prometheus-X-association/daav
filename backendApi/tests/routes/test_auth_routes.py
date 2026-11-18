"""
Tests of the authentication routes (the user service is mocked).
"""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException, status

from app.models.interface.user_interface import UserCreate
from app.routes import auth


def new_user():
    return UserCreate(username="alice", email="alice@example.com", full_name="Alice", password="Passw0rd!")


@pytest.mark.asyncio
async def test_register_with_an_existing_username_is_a_400():
    """The 400 of the user service used to be turned into a 500 (Registration failed)"""
    duplicate = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    with patch.object(auth.user_service, "create_user", AsyncMock(side_effect=duplicate)):
        user_data = new_user()
        with pytest.raises(HTTPException) as error:
            await auth.register(user_data, admin_user=None)

    assert (error.value.status_code, error.value.detail) == (400, "Username already exists")


@pytest.mark.asyncio
async def test_register_unexpected_error_is_a_500():
    with patch.object(auth.user_service, "create_user", AsyncMock(side_effect=RuntimeError("db down"))):
        user_data = new_user()
        with pytest.raises(HTTPException) as error:
            await auth.register(user_data, admin_user=None)

    assert (error.value.status_code, error.value.detail) == (500, "Registration failed")
