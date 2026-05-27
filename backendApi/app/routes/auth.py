"""
Authentication and user management routes
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.models.interface.user_interface import (
    User, UserCreate, UserUpdate, UserResponse, UserConfigUpdate
)
from app.models.interface.auth_interface import (
    Token, LoginRequest, RefreshTokenRequest, ChangePasswordRequest,
    ShareResourceRequest, UnshareResourceRequest,
    ForgotPasswordRequest, ResetPasswordRequest
)
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.middleware.auth import (
    get_current_active_user, require_admin, CurrentUser, AdminUser, security
)
from app.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

auth_service = AuthService()
user_service = UserService()


async def conditional_admin_check(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """
    Conditional dependency that requires admin authentication only when public registration is disabled.
    
    Returns:
        - None if public registration is enabled (allow_public_registration=True)
        - Admin user if public registration is disabled (allow_public_registration=False)
    """
    if settings.allow_public_registration:
        return None
    
    # Public registration is disabled, require admin authentication
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get and verify user
    current_user = await auth_service.get_current_user(credentials.credentials)
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    admin_user: Optional[User] = Depends(conditional_admin_check)
):
    """
    Register a new user
    
    **Access Control:**
    - If `ALLOW_PUBLIC_REGISTRATION=true`: Anyone can register
    - If `ALLOW_PUBLIC_REGISTRATION=false` (default): Only admins can create users
    
    **Parameters:**
    - **username**: Unique username (3-50 characters, alphanumeric + _ -)
    - **email**: Valid email address
    - **full_name**: User's full name
    - **password**: Password (min 8 chars, must include uppercase, lowercase, and special character)
    - **role**: User role (admin or user) - default: user
    
    **Note:** Only admins can create users with admin role, regardless of public registration setting.
    """
    # Only admins can create admin users
    if user_data.role.value == "admin" and not admin_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create admin users"
        )
    
    try:
        user = await user_service.create_user(user_data)
        logger.info(f"New user registered: {user.username}")
        return UserResponse.model_validate(user)
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    """
    Login with username/email and password
    
    Returns access token (valid 60 minutes) and refresh token (valid 90 days)
    
    - **username**: Username or email
    - **password**: User password
    """
    try:
        token = await auth_service.login(login_data.username, login_data.password)
        logger.info(f"User logged in: {login_data.username}")
        return token
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_data: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    
    Returns new access token and refresh token
    
    - **refresh_token**: Valid refresh token
    """
    try:
        token = await auth_service.refresh_access_token(refresh_data.refresh_token)
        return token
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token"
        )


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(request: ForgotPasswordRequest):
    """
    Request password reset
    
    Sends a password reset email to the user if the email exists.
    Always returns success to prevent email enumeration.
    
    - **email**: User's email address
    
    **Response:** Always returns success message for security
    """
    try:
        await auth_service.forgot_password(request.email)
        return {
            "message": "If the email exists, a password reset link has been sent. Please check your inbox."
        }
    except Exception as e:
        logger.error(f"Forgot password error: {e}", exc_info=True)
        # Still return success to prevent email enumeration
        return {
            "message": "If the email exists, a password reset link has been sent. Please check your inbox."
        }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(request: ResetPasswordRequest):
    """
    Reset password using reset token
    
    Use the token received via email to set a new password.
    
    - **token**: Password reset token from email
    - **new_password**: New password (min 8 chars, must include uppercase, lowercase, and special character)
    
    **Raises:**
    - **400**: Invalid or expired token
    - **404**: User not found
    """
    try:
        success = await auth_service.reset_password(request.token, request.new_password)
        if success:
            return {
                "message": "Password has been reset successfully. You can now login with your new password."
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset password error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser):
    """
    Get current authenticated user information
    
    Requires valid access token
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: CurrentUser
):
    """
    Update current user information
    
    - **email**: New email address (optional)
    - **full_name**: New full name (optional)
    - **password**: New password (optional, must meet complexity requirements)
    """
    try:
        updated_user = await user_service.update_user(
            current_user.id,
            user_update,
            current_user
        )
        return UserResponse.model_validate(updated_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User update error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: CurrentUser
):
    """
    Change current user password
    
    - **current_password**: Current password for verification
    - **new_password**: New password (must meet complexity requirements)
    """
    try:
        await user_service.change_password(
            current_user.id,
            password_data.current_password,
            password_data.new_password
        )
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Password change error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.put("/me/config", response_model=UserResponse)
async def update_user_configuration(
    config_update: UserConfigUpdate,
    current_user: CurrentUser
):
    """
    Update user configuration (credentials and settings)
    
    - **credentials**: Key-value pairs for user credentials (optional)
    - **settings**: Key-value pairs for user settings (optional)
    """
    try:
        updated_user = await user_service.update_user_config(
            current_user.id,
            config_update
        )
        return UserResponse.model_validate(updated_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Config update error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration"
        )


# ==================== ADMIN ROUTES ====================

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(admin_user: AdminUser):
    """
    Get all users (Admin only)
    """
    try:
        users = await user_service.get_all_users()
        return [UserResponse.model_validate(user) for user in users]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get users error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: str, admin_user: AdminUser):
    """
    Get user by ID (Admin only)
    """
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserResponse.model_validate(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    admin_user: AdminUser
):
    """
    Update any user (Admin only)
    
    Admin can update any user's information including role
    """
    try:
        updated_user = await user_service.update_user(
            user_id,
            user_update,
            admin_user
        )
        return UserResponse.model_validate(updated_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin_user: AdminUser):
    """
    Delete a user (Admin only)
    
    Cannot delete the last admin user
    """
    try:
        await user_service.delete_user(user_id, admin_user)
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    admin_user: AdminUser,
    reason: Optional[str] = None
):
    """
    Deactivate a user account (Admin only)
    
    This prevents the user from logging in without deleting their data.
    The account can be reactivated later.
    
    **Parameters:**
    - **user_id**: ID of the user to deactivate
    - **reason**: Optional reason for deactivation
    
    **Note:** Cannot deactivate the last admin user
    """
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if already inactive
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already deactivated"
            )
        
        # Prevent deactivating the last admin
        if user.role.value == "admin":
            from app.enums.user_role import UserRole
            active_admin_count = await User.find(
                User.role == UserRole.ADMIN,
                User.is_active == True
            ).count()
            
            if active_admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot deactivate the last active admin user"
                )
        
        # Deactivate the user
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        
        # Store deactivation details in config if reason provided
        if reason:
            user.config.settings["deactivation_reason"] = reason
            user.config.settings["deactivated_at"] = datetime.now(timezone.utc).isoformat()
            user.config.settings["deactivated_by"] = admin_user.id
        
        await user.save()
        
        logger.info(f"User {user.username} deactivated by admin {admin_user.username}")
        return {
            "message": "User deactivated successfully",
            "user_id": user_id,
            "username": user.username
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deactivate user error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    admin_user: AdminUser
):
    """
    Activate a deactivated user account (Admin only)
    
    This allows a previously deactivated user to log in again.
    
    **Parameters:**
    - **user_id**: ID of the user to activate
    """
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if already active
        if user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already active"
            )
        
        # Activate the user
        user.is_active = True
        user.updated_at = datetime.now(timezone.utc)
        
        # Clear deactivation details from config
        if "deactivation_reason" in user.config.settings:
            del user.config.settings["deactivation_reason"]
        if "deactivated_at" in user.config.settings:
            del user.config.settings["deactivated_at"]
        if "deactivated_by" in user.config.settings:
            del user.config.settings["deactivated_by"]
        
        # Store activation details
        user.config.settings["reactivated_at"] = datetime.now(timezone.utc).isoformat()
        user.config.settings["reactivated_by"] = admin_user.id
        
        await user.save()
        
        logger.info(f"User {user.username} activated by admin {admin_user.username}")
        return {
            "message": "User activated successfully",
            "user_id": user_id,
            "username": user.username
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Activate user error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user"
        )


# ==================== SHARING ROUTES ====================

@router.post("/share")
async def share_resource(
    share_request: ShareResourceRequest,
    current_user: CurrentUser
):
    """
    Share a dataset or workflow with another user
    
    Only the owner can share resources
    
    - **resource_id**: ID of the dataset or workflow to share
    - **target_user_id**: ID of the user to share with
    - **resource_type**: "dataset" or "workflow"
    """
    try:
        if share_request.resource_type == "dataset":
            await user_service.share_dataset(
                current_user.id,
                share_request.resource_id,
                share_request.target_user_id
            )
        elif share_request.resource_type == "workflow":
            await user_service.share_workflow(
                current_user.id,
                share_request.resource_id,
                share_request.target_user_id
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid resource type"
            )
        
        return {"message": f"{share_request.resource_type.capitalize()} shared successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Share resource error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to share resource"
        )


@router.post("/unshare")
async def unshare_resource(
    unshare_request: UnshareResourceRequest,
    current_user: CurrentUser
):
    """
    Unshare a dataset or workflow from a user
    
    Only the owner can unshare resources
    
    - **resource_id**: ID of the dataset or workflow to unshare
    - **target_user_id**: ID of the user to unshare from
    - **resource_type**: "dataset" or "workflow"
    """
    try:
        if unshare_request.resource_type == "dataset":
            await user_service.unshare_dataset(
                current_user.id,
                unshare_request.resource_id,
                unshare_request.target_user_id
            )
        elif unshare_request.resource_type == "workflow":
            await user_service.unshare_workflow(
                current_user.id,
                unshare_request.resource_id,
                unshare_request.target_user_id
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid resource type"
            )
        
        return {"message": f"{unshare_request.resource_type.capitalize()} unshared successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unshare resource error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unshare resource"
        )
