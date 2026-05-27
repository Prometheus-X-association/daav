import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from fastapi import HTTPException, status

from app.models.interface.user_interface import User, PasswordResetToken
from app.models.interface.auth_interface import Token, TokenData, validate_password_complexity
from app.utils.auth_utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
    ensure_utc_aware
)
from app.services.user_service import UserService
from app.services.email_service import EmailService
from app.config.settings import settings
from app.utils.singleton import SingletonMeta

logger = logging.getLogger(__name__)


class AuthService(metaclass=SingletonMeta):
    """Service for authentication operations"""
    
    def __init__(self):
        self.user_service = UserService()
        self.email_service = EmailService()
        logger.info("AuthService initialized")
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user with username/email and password
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            User: Authenticated user or None
        """
        try:
            # Find user by username or email
            user = await self.user_service.get_user_by_username_or_email(username)
            
            if not user:
                logger.warning(f"Authentication failed: User not found - {username}")
                return None
            
            # Check if account is active
            if not user.is_active:
                logger.warning(f"Authentication failed: Account inactive - {username}")
                return None
            
            # Verify password
            if not verify_password(password, user.hashed_password):
                logger.warning(f"Authentication failed: Invalid password - {username}")
                return None
            
            logger.info(f"User authenticated successfully: {user.username}")
            return user
        
        except Exception as e:
            logger.error(f"Error during authentication: {e}", exc_info=True)
            return None
    
    async def login(self, username: str, password: str) -> Token:
        """
        Login user and return JWT tokens
        
        Args:
            username: Username or email
            password: Password
            
        Returns:
            Token: Access and refresh tokens
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            # Authenticate user
            user = await self.authenticate_user(username, password)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Update last login
            await self.user_service.update_last_login(user.id)
            
            # Create tokens
            token_data = {
                "sub": user.id,
                "username": user.username,
                "role": user.role.value
            }
            
            access_token = create_access_token(token_data)
            refresh_token = create_refresh_token(token_data)
            
            logger.info(f"Login successful: {user.username}")
            
            return Token(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer"
            )
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during login: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login failed"
            )
    
    async def refresh_access_token(self, refresh_token: str) -> Token:
        """
        Generate new access token using refresh token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Token: New access and refresh tokens
            
        Raises:
            HTTPException: If refresh token is invalid
        """
        try:
            # Verify it's a refresh token
            verify_token_type(refresh_token, "refresh")
            
            # Decode token
            token_data = decode_token(refresh_token)
            
            # Get user
            user = await self.user_service.get_user_by_id(token_data.user_id)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Create new tokens
            new_token_data = {
                "sub": user.id,
                "username": user.username,
                "role": user.role.value
            }
            
            new_access_token = create_access_token(new_token_data)
            new_refresh_token = create_refresh_token(new_token_data)
            
            logger.info(f"Token refreshed for user: {user.username}")
            
            return Token(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                token_type="bearer"
            )
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error refreshing token: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def get_current_user(self, token: str) -> User:
        """
        Get current user from access token
        
        Args:
            token: JWT access token
            
        Returns:
            User: Current authenticated user
            
        Raises:
            HTTPException: If token is invalid or user not found
        """
        try:
            # Verify it's an access token
            verify_token_type(token, "access")
            
            # Decode token
            token_data = decode_token(token)
            
            # Get user
            user = await self.user_service.get_user_by_id(token_data.user_id)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return user
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting current user: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def verify_admin(self, user: User) -> bool:
        """
        Verify if user is admin
        
        Args:
            user: User to verify
            
        Returns:
            bool: True if user is admin
            
        Raises:
            HTTPException: If user is not admin
        """
        from app.enums.user_role import UserRole
        
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        return True
    
    async def forgot_password(self, email: str) -> bool:
        """
        Initiate password reset process
        
        Args:
            email: User email address
            
        Returns:
            bool: True if reset email sent (always returns True to prevent email enumeration)
        """
        try:
            # Find user by email
            user = await self.user_service.get_user_by_email(email)
            
            if not user:
                # Don't reveal if email exists or not (security)
                logger.warning(f"Password reset requested for non-existent email: {email}")
                return True
            
            if not user.is_active:
                logger.warning(f"Password reset requested for inactive account: {email}")
                return True
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            
            # Hash token before storing
            hashed_token = get_password_hash(reset_token)
            
            # Calculate expiration
            expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.password_reset_token_expire_hours)
            
            # Delete any existing reset tokens for this user
            await PasswordResetToken.find(PasswordResetToken.user_id == user.id).delete()
            
            # Create new reset token record
            reset_token_doc = PasswordResetToken(
                user_id=user.id,
                token=hashed_token,
                expires_at=expires_at,
                used=False
            )
            await reset_token_doc.insert()
            
            # Send reset email
            email_sent = await self.email_service.send_password_reset_email(
                to_email=user.email,
                username=user.username,
                reset_token=reset_token  # Send plain token in email, not hashed
            )
            
            if email_sent:
                logger.info(f"Password reset email sent to: {email}")
            else:
                logger.error(f"Failed to send password reset email to: {email}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error in forgot_password: {e}", exc_info=True)
            # Always return True to prevent email enumeration
            return True
    
    async def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset user password using reset token
        
        Args:
            token: Password reset token from email
            new_password: New password
            
        Returns:
            bool: True if password reset successful
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Find all active (unused) reset tokens
            reset_tokens = await PasswordResetToken.find(
                PasswordResetToken.used == False
            ).to_list()
            
            # Find matching token (compare hashes)
            matching_token = None
            for token_doc in reset_tokens:
                if verify_password(token, token_doc.token):
                    matching_token = token_doc
                    break
            
            if not matching_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired reset token"
                )
            
            # Check if token is expired
            # Ensure both datetimes are timezone-aware for comparison
            expires_at_aware = ensure_utc_aware(matching_token.expires_at)
            if datetime.now(timezone.utc) > expires_at_aware:
                await matching_token.delete()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reset token has expired. Please request a new one."
                )
            
            # Get user
            user = await self.user_service.get_user_by_id(matching_token.user_id)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User account is inactive"
                )
            
            # Validate password complexity for all call paths (route and direct service use)
            validate_password_complexity(new_password)

            # Update password
            user.hashed_password = get_password_hash(new_password)
            user.updated_at = datetime.now(timezone.utc)
            await user.save()
            
            # Mark token as used
            matching_token.used = True
            await matching_token.save()
            
            logger.info(f"Password reset successful for user: {user.username}")
            
            return True
        
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error resetting password: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset password"
            )
