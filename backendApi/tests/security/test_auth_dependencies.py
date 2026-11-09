"""
Tests for the authentication dependencies (pending password change enforcement)
"""

import pytest
from fastapi import HTTPException

from app.middleware.auth import (
    get_current_active_user,
    get_current_active_user_pending_password_change,
    PASSWORD_CHANGE_REQUIRED_DETAIL,
)


@pytest.mark.asyncio
async def test_active_user_allowed(mock_user):
    """Test that an active user without pending password change is allowed"""
    result = await get_current_active_user(mock_user)

    assert result == mock_user


@pytest.mark.asyncio
async def test_pending_password_change_blocked(mock_user):
    """Test that a user who must change their password is blocked on regular endpoints"""
    mock_user.must_change_password = True

    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_user(mock_user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == PASSWORD_CHANGE_REQUIRED_DETAIL


@pytest.mark.asyncio
async def test_pending_password_change_allowed_on_password_change_endpoints(mock_user):
    """Test that a user who must change their password can still reach the password change endpoints"""
    mock_user.must_change_password = True

    result = await get_current_active_user_pending_password_change(mock_user)

    assert result == mock_user


@pytest.mark.asyncio
async def test_inactive_user_blocked_on_password_change_endpoints(mock_user):
    """Test that an inactive user is blocked even on the password change endpoints"""
    mock_user.is_active = False

    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_user_pending_password_change(mock_user)

    assert exc_info.value.status_code == 403


# ============================================
# FIRST LOGIN FLOW (API)
# ============================================

@pytest.mark.asyncio
async def test_default_admin_must_change_password_before_api_access():
    """Test the full flow: default admin login, blocked access, password change, access granted"""
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from app.middleware.auth import CurrentUser
    from app.routes.auth import router as auth_router
    from app.services.user_service import UserService, DEFAULT_ADMIN_PASSWORD

    await UserService().ensure_admin_exists()

    app = FastAPI()
    app.include_router(auth_router)

    @app.get("/protected")
    async def protected(current_user: CurrentUser):
        return {"username": current_user.username}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login = await client.post("/auth/login", json={"username": "admin", "password": DEFAULT_ADMIN_PASSWORD})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        me = await client.get("/auth/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["must_change_password"] is True

        blocked = await client.get("/protected", headers=headers)
        assert blocked.status_code == 403
        assert blocked.json()["detail"] == PASSWORD_CHANGE_REQUIRED_DETAIL

        changed = await client.post("/auth/change-password", headers=headers, json={
            "current_password": DEFAULT_ADMIN_PASSWORD,
            "new_password": "NewAdmin456!"
        })
        assert changed.status_code == 200

        # The tokens issued with the default password are revoked
        assert (await client.get("/protected", headers=headers)).status_code == 401
        refresh = await client.post("/auth/refresh", json={"refresh_token": login.json()["refresh_token"]})
        assert refresh.status_code == 401

        # The current session continues with the new tokens
        new_headers = {"Authorization": f"Bearer {changed.json()['access_token']}"}
        allowed = await client.get("/protected", headers=new_headers)
        assert allowed.status_code == 200
        assert (await client.get("/auth/me", headers=new_headers)).json()["must_change_password"] is False
        refresh = await client.post("/auth/refresh", json={"refresh_token": changed.json()["refresh_token"]})
        assert refresh.status_code == 200


# ============================================
# PROFILE UPDATE (API)
# ============================================

@pytest.mark.asyncio
async def test_profile_update_cannot_change_password():
    """Test that PUT /auth/me refuses a password change, which requires the current password"""
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from app.enums.user_role import UserRole
    from app.models.interface.user_interface import UserCreate
    from app.routes.auth import router as auth_router
    from app.services.user_service import UserService

    await UserService().create_user(UserCreate(
        username="profileuser",
        email="profile@example.com",
        full_name="Profile User",
        password="Initial123!",
        role=UserRole.USER
    ))

    app = FastAPI()
    app.include_router(auth_router)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login = await client.post("/auth/login", json={"username": "profileuser", "password": "Initial123!"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        refused = await client.put("/auth/me", headers=headers, json={"password": "Hijacked123!"})
        assert refused.status_code == 400
        assert "/auth/change-password" in refused.json()["detail"]

        # The password and the session are unchanged
        assert (await client.get("/auth/me", headers=headers)).status_code == 200
        relogin = await client.post("/auth/login", json={"username": "profileuser", "password": "Initial123!"})
        assert relogin.status_code == 200

        # The other profile fields can still be updated
        updated = await client.put("/auth/me", headers=headers, json={"full_name": "Renamed User"})
        assert updated.status_code == 200
        assert updated.json()["full_name"] == "Renamed User"
