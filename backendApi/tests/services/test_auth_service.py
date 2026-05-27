"""
Tests for AuthService

This module tests all authentication functionality including:
- User authentication and login
- Token management (access and refresh tokens)
- Password reset flow
- Admin verification
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.models.interface.user_interface import User, UserCreate, PasswordResetToken
from app.models.interface.auth_interface import Token, TokenData
from app.enums.user_role import UserRole


@pytest.fixture
def auth_service_instance():
    """Get AuthService instance (singleton)"""
    return AuthService()


@pytest_asyncio.fixture
async def test_user(user_service_instance):
    """Create a test user in the database"""
    user_create = UserCreate(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        password="Test123!",
        role=UserRole.USER
    )
    
    with patch('app.services.user_service.get_password_hash', return_value="hashed_password"):
        user = await user_service_instance.create_user(user_create)
    
    return user


@pytest_asyncio.fixture
async def test_admin(user_service_instance):
    """Create a test admin user in the database"""
    admin_create = UserCreate(
        username="adminuser",
        email="admin@example.com",
        full_name="Admin User",
        password="Admin123!",
        role=UserRole.ADMIN
    )
    
    with patch('app.services.user_service.get_password_hash', return_value="hashed_password"):
        admin = await user_service_instance.create_user(admin_create)
    
    return admin


@pytest.fixture
def user_service_instance():
    """Get UserService instance"""
    return UserService()


# ============================================
# AUTHENTICATE USER TESTS
# ============================================

@pytest.mark.asyncio
async def test_authenticate_user_success(auth_service_instance, test_user):
    """Test successful user authentication"""
    with patch('app.services.auth_service.verify_password', return_value=True):
        result = await auth_service_instance.authenticate_user("testuser", "Test123!")
        
        assert result is not None
        assert result.username == test_user.username
        assert result.email == test_user.email


@pytest.mark.asyncio
async def test_authenticate_user_by_email(auth_service_instance, test_user):
    """Test authentication using email instead of username"""
    with patch('app.services.auth_service.verify_password', return_value=True):
        result = await auth_service_instance.authenticate_user("test@example.com", "Test123!")
        
        assert result is not None
        assert result.email == test_user.email


@pytest.mark.asyncio
async def test_authenticate_user_not_found(auth_service_instance):
    """Test authentication with non-existent user"""
    result = await auth_service_instance.authenticate_user("nonexistent", "password")
    
    assert result is None


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(auth_service_instance, test_user):
    """Test authentication with incorrect password"""
    with patch('app.services.auth_service.verify_password', return_value=False):
        result = await auth_service_instance.authenticate_user("testuser", "WrongPassword")
        
        assert result is None


@pytest.mark.asyncio
async def test_authenticate_user_inactive_account(auth_service_instance, test_user):
    """Test authentication with inactive account"""
    # Mark user as inactive
    test_user.is_active = False
    await test_user.save()
    
    with patch('app.services.auth_service.verify_password', return_value=True):
        result = await auth_service_instance.authenticate_user("testuser", "Test123!")
        
        assert result is None


# ============================================
# LOGIN TESTS
# ============================================

@pytest.mark.asyncio
async def test_login_success(auth_service_instance, test_user):
    """Test successful login"""
    with patch('app.services.auth_service.verify_password', return_value=True), \
         patch('app.services.auth_service.create_access_token', return_value="access_token_123"), \
         patch('app.services.auth_service.create_refresh_token', return_value="refresh_token_456"):
        
        result = await auth_service_instance.login("testuser", "Test123!")
        
        assert isinstance(result, Token)
        assert result.access_token == "access_token_123"
        assert result.refresh_token == "refresh_token_456"
        assert result.token_type == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(auth_service_instance):
    """Test login with invalid credentials"""
    with pytest.raises(HTTPException) as exc_info:
        await auth_service_instance.login("nonexistent", "password")
    
    assert exc_info.value.status_code == 401
    assert "Incorrect username or password" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_login_updates_last_login(auth_service_instance, test_user):
    """Test that login updates user's last_login timestamp"""
    original_last_login = test_user.last_login
    
    with patch('app.services.auth_service.verify_password', return_value=True), \
         patch('app.services.auth_service.create_access_token', return_value="access_token"), \
         patch('app.services.auth_service.create_refresh_token', return_value="refresh_token"):
        
        await auth_service_instance.login("testuser", "Test123!")
        
        # Refresh user from database
        updated_user = await User.get(test_user.id)
        assert updated_user.last_login is not None
        # last_login should be updated (different from original or None)


# ============================================
# REFRESH TOKEN TESTS
# ============================================

@pytest.mark.asyncio
async def test_refresh_access_token_success(auth_service_instance, test_user):
    """Test successful token refresh"""
    mock_token_data = Mock(spec=TokenData)
    mock_token_data.user_id = str(test_user.id)
    
    with patch('app.services.auth_service.verify_token_type'), \
         patch('app.services.auth_service.decode_token', return_value=mock_token_data), \
         patch('app.services.auth_service.create_access_token', return_value="new_access_token"), \
         patch('app.services.auth_service.create_refresh_token', return_value="new_refresh_token"):
        
        result = await auth_service_instance.refresh_access_token("old_refresh_token")
        
        assert isinstance(result, Token)
        assert result.access_token == "new_access_token"
        assert result.refresh_token == "new_refresh_token"
        assert result.token_type == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_user_not_found(auth_service_instance):
    """Test token refresh with non-existent user"""
    mock_token_data = Mock(spec=TokenData)
    mock_token_data.user_id = "nonexistent_user_id"
    
    with patch('app.services.auth_service.verify_token_type'), \
         patch('app.services.auth_service.decode_token', return_value=mock_token_data):
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_service_instance.refresh_access_token("refresh_token")
        
        assert exc_info.value.status_code == 401
        assert "User not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_refresh_token_inactive_user(auth_service_instance, test_user):
    """Test token refresh with inactive user account"""
    test_user.is_active = False
    await test_user.save()
    
    mock_token_data = Mock(spec=TokenData)
    mock_token_data.user_id = str(test_user.id)
    
    with patch('app.services.auth_service.verify_token_type'), \
         patch('app.services.auth_service.decode_token', return_value=mock_token_data):
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_service_instance.refresh_access_token("refresh_token")
        
        assert exc_info.value.status_code == 401
        assert "inactive" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_refresh_token_invalid_token(auth_service_instance):
    """Test token refresh with invalid token"""
    with patch('app.services.auth_service.verify_token_type', side_effect=HTTPException(status_code=401, detail="Invalid token")):
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_service_instance.refresh_access_token("invalid_token")
        
        assert exc_info.value.status_code == 401


# ============================================
# GET CURRENT USER TESTS
# ============================================

@pytest.mark.asyncio
async def test_get_current_user_success(auth_service_instance, test_user):
    """Test getting current user from valid token"""
    mock_token_data = Mock(spec=TokenData)
    mock_token_data.user_id = str(test_user.id)
    
    with patch('app.services.auth_service.verify_token_type'), \
         patch('app.services.auth_service.decode_token', return_value=mock_token_data):
        
        result = await auth_service_instance.get_current_user("access_token")
        
        assert result.id == test_user.id
        assert result.username == test_user.username


@pytest.mark.asyncio
async def test_get_current_user_not_found(auth_service_instance):
    """Test get current user with non-existent user ID in token"""
    mock_token_data = Mock(spec=TokenData)
    mock_token_data.user_id = "nonexistent_user_id"
    
    with patch('app.services.auth_service.verify_token_type'), \
         patch('app.services.auth_service.decode_token', return_value=mock_token_data):
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_service_instance.get_current_user("access_token")
        
        assert exc_info.value.status_code == 401
        assert "User not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_user_inactive(auth_service_instance, test_user):
    """Test get current user with inactive account"""
    test_user.is_active = False
    await test_user.save()
    
    mock_token_data = Mock(spec=TokenData)
    mock_token_data.user_id = str(test_user.id)
    
    with patch('app.services.auth_service.verify_token_type'), \
         patch('app.services.auth_service.decode_token', return_value=mock_token_data):
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_service_instance.get_current_user("access_token")
        
        assert exc_info.value.status_code == 401
        assert "inactive" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(auth_service_instance):
    """Test get current user with invalid token"""
    with patch('app.services.auth_service.verify_token_type', side_effect=Exception("Invalid token")):
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_service_instance.get_current_user("invalid_token")
        
        assert exc_info.value.status_code == 401


# ============================================
# ADMIN VERIFICATION TESTS
# ============================================

@pytest.mark.asyncio
async def test_verify_admin_success(auth_service_instance, test_admin):
    """Test admin verification with admin user"""
    result = await auth_service_instance.verify_admin(test_admin)
    
    assert result is True


@pytest.mark.asyncio
async def test_verify_admin_non_admin_user(auth_service_instance, test_user):
    """Test admin verification with regular user"""
    with pytest.raises(HTTPException) as exc_info:
        await auth_service_instance.verify_admin(test_user)
    
    assert exc_info.value.status_code == 403
    assert "Admin access required" in str(exc_info.value.detail)


# ============================================
# PASSWORD RESET TESTS
# ============================================

@pytest.mark.asyncio
async def test_forgot_password_success(auth_service_instance, test_user):
    """Test forgot password initiates reset process"""
    with patch.object(auth_service_instance.email_service, 'send_password_reset_email', new_callable=AsyncMock) as mock_send_email:
        mock_send_email.return_value = True
        
        result = await auth_service_instance.forgot_password(test_user.email)
        
        assert result is True
        mock_send_email.assert_called_once()
        
        # Verify reset token was created
        reset_tokens = await PasswordResetToken.find(
            PasswordResetToken.user_id == test_user.id
        ).to_list()
        assert len(reset_tokens) == 1
        assert reset_tokens[0].used is False


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_email(auth_service_instance):
    """Test forgot password with non-existent email (should not reveal)"""
    with patch.object(auth_service_instance.email_service, 'send_password_reset_email', new_callable=AsyncMock) as mock_send_email:
        result = await auth_service_instance.forgot_password("nonexistent@example.com")
        
        # Always returns True to prevent email enumeration
        assert result is True
        # Email should not be sent
        mock_send_email.assert_not_called()


@pytest.mark.asyncio
async def test_forgot_password_inactive_user(auth_service_instance, test_user):
    """Test forgot password with inactive user (should not reveal)"""
    test_user.is_active = False
    await test_user.save()
    
    with patch.object(auth_service_instance.email_service, 'send_password_reset_email', new_callable=AsyncMock) as mock_send_email:
        result = await auth_service_instance.forgot_password(test_user.email)
        
        # Returns True to prevent account status enumeration
        assert result is True
        # Email should not be sent
        mock_send_email.assert_not_called()


@pytest.mark.asyncio
async def test_forgot_password_replaces_old_tokens(auth_service_instance, test_user):
    """Test forgot password deletes old reset tokens"""
    # Create first reset token
    with patch.object(auth_service_instance.email_service, 'send_password_reset_email', new_callable=AsyncMock) as mock_send_email:
        mock_send_email.return_value = True
        await auth_service_instance.forgot_password(test_user.email)
        
        # Request another reset
        await auth_service_instance.forgot_password(test_user.email)
        
        # Should only have 1 token (old one deleted)
        reset_tokens = await PasswordResetToken.find(
            PasswordResetToken.user_id == test_user.id
        ).to_list()
        assert len(reset_tokens) == 1


@pytest.mark.asyncio
async def test_reset_password_success(auth_service_instance, test_user):
    """Test successful password reset"""
    # Generate reset token
    with patch.object(auth_service_instance.email_service, 'send_password_reset_email', new_callable=AsyncMock) as mock_send_email, \
         patch('app.services.auth_service.get_password_hash') as mock_hash, \
         patch('app.services.auth_service.verify_password') as mock_verify:
        
        mock_send_email.return_value = True
        mock_hash.return_value = "hashed_token"
        mock_verify.return_value = True  # Token matches
        
        await auth_service_instance.forgot_password(test_user.email)
        
        # Now reset password
        new_password = "NewPassword123!"
        mock_hash.return_value = "new_hashed_password"
        
        result = await auth_service_instance.reset_password("plain_token", new_password)
        
        assert result is True
        
        # Verify token is marked as used
        reset_tokens = await PasswordResetToken.find(
            PasswordResetToken.user_id == test_user.id
        ).to_list()
        assert len(reset_tokens) == 1
        assert reset_tokens[0].used is True


@pytest.mark.asyncio
async def test_reset_password_invalid_token(auth_service_instance):
    """Test password reset with invalid token"""
    with patch('app.services.auth_service.verify_password', return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await auth_service_instance.reset_password("invalid_token", "NewPassword123!")
        
        assert exc_info.value.status_code == 400
        assert "Invalid or expired" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_reset_password_expired_token(auth_service_instance, test_user):
    """Test password reset with expired token"""
    # Create an expired token
    reset_token = PasswordResetToken(
        user_id=test_user.id,
        token="hashed_token",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),  # Expired 1 hour ago
        used=False
    )
    await reset_token.insert()
    
    with patch('app.services.auth_service.verify_password', return_value=True):
        with pytest.raises(HTTPException) as exc_info:
            await auth_service_instance.reset_password("plain_token", "NewPassword123!")
        
        assert exc_info.value.status_code == 400
        assert "expired" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_reset_password_inactive_user(auth_service_instance, test_user):
    """Test password reset with inactive user account"""
    # Mark user as inactive
    test_user.is_active = False
    await test_user.save()
    
    # Create valid reset token
    reset_token = PasswordResetToken(
        user_id=test_user.id,
        token="hashed_token",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        used=False
    )
    await reset_token.insert()
    
    with patch('app.services.auth_service.verify_password', return_value=True):
        with pytest.raises(HTTPException) as exc_info:
            await auth_service_instance.reset_password("plain_token", "NewPassword123!")
        
        assert exc_info.value.status_code == 400
        assert "inactive" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_reset_password_rejects_weak_password(auth_service_instance, test_user):
    """Test password reset rejects weak password complexity."""
    reset_token = PasswordResetToken(
        user_id=test_user.id,
        token="hashed_token",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        used=False
    )
    await reset_token.insert()

    with patch('app.services.auth_service.verify_password', return_value=True):
        with pytest.raises(HTTPException) as exc_info:
            await auth_service_instance.reset_password("plain_token", "weakpass")

        assert exc_info.value.status_code == 400
        assert "uppercase" in str(exc_info.value.detail).lower()


# ============================================
# INTEGRATION TESTS
# ============================================

@pytest.mark.asyncio
async def test_full_password_reset_flow(auth_service_instance, test_user):
    """Test complete password reset flow from request to completion"""
    original_password_hash = test_user.hashed_password
    
    # Step 1: Request password reset
    with patch.object(auth_service_instance.email_service, 'send_password_reset_email', new_callable=AsyncMock) as mock_send_email, \
         patch('app.services.auth_service.get_password_hash') as mock_hash, \
         patch('app.services.auth_service.verify_password') as mock_verify:
        
        mock_send_email.return_value = True
        mock_hash.return_value = "hashed_token"
        
        result = await auth_service_instance.forgot_password(test_user.email)
        assert result is True
        
        # Step 2: Reset password using token
        mock_verify.return_value = True  # Token matches
        mock_hash.return_value = "new_hashed_password"
        
        reset_result = await auth_service_instance.reset_password("plain_token", "NewPassword123!")
        assert reset_result is True
        
        # Step 3: Verify password was changed
        updated_user = await User.get(test_user.id)
        assert updated_user.hashed_password == "new_hashed_password"
        assert updated_user.hashed_password != original_password_hash


@pytest.mark.asyncio
async def test_login_after_password_reset(auth_service_instance, test_user):
    """Test user can login after password reset"""
    # Reset password
    with patch.object(auth_service_instance.email_service, 'send_password_reset_email', new_callable=AsyncMock), \
         patch('app.services.auth_service.get_password_hash') as mock_hash, \
         patch('app.services.auth_service.verify_password') as mock_verify:
        
        mock_hash.return_value = "hashed_token"
        await auth_service_instance.forgot_password(test_user.email)
        
        mock_verify.return_value = True
        mock_hash.return_value = "new_hashed_password"
        await auth_service_instance.reset_password("plain_token", "NewPassword123!")
        
        # Now try to login with new password
        mock_verify.return_value = True  # New password verification
        
        with patch('app.services.auth_service.create_access_token', return_value="access_token"), \
             patch('app.services.auth_service.create_refresh_token', return_value="refresh_token"):
            
            token = await auth_service_instance.login(test_user.username, "NewPassword123!")
            assert token is not None
            assert token.access_token == "access_token"


@pytest.mark.asyncio
async def test_token_refresh_cycle(auth_service_instance, test_user):
    """Test multiple token refresh cycles"""
    mock_token_data = Mock(spec=TokenData)
    mock_token_data.user_id = str(test_user.id)
    
    with patch('app.services.auth_service.verify_token_type'), \
         patch('app.services.auth_service.decode_token', return_value=mock_token_data), \
         patch('app.services.auth_service.create_access_token') as mock_access, \
         patch('app.services.auth_service.create_refresh_token') as mock_refresh:
        
        # First refresh
        mock_access.return_value = "access_token_1"
        mock_refresh.return_value = "refresh_token_1"
        token1 = await auth_service_instance.refresh_access_token("old_refresh_token")
        
        # Second refresh
        mock_access.return_value = "access_token_2"
        mock_refresh.return_value = "refresh_token_2"
        token2 = await auth_service_instance.refresh_access_token("refresh_token_1")
        
        assert token1.access_token == "access_token_1"
        assert token2.access_token == "access_token_2"
        assert token1.access_token != token2.access_token
