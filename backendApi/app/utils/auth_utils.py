import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, TypedDict
from fastapi.datastructures import Headers
import jwt
from jwt import PyJWTError as JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.models.interface.auth_interface import TokenData
from app.models.interface.user_interface import User
from app.config.settings import settings

# Type definitions
class AuthenticatedUser(TypedDict):
    """Type for authenticated user with matched credentials"""
    user: User
    matched_credentials: Dict[str, str]

# Password hashing context using Argon2id (OWASP recommended 2025)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# JWT settings from application settings
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.jwt_refresh_token_expire_days


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password
    
    Args:
        plain_password: The plain text password
        hashed_password: The Argon2 hashed password
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using Argon2id
    
    Args:
        password: The plain text password to hash
        
    Returns:
        str: The Argon2 hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        str: The encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token with longer expiration
    
    Args:
        data: The data to encode in the token
        
    Returns:
        str: The encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """
    Decode and verify a JWT token
    
    Args:
        token: The JWT token to decode
        
    Returns:
        TokenData: The decoded token data
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        role: str = payload.get("role")
        token_version: int = payload.get("tv", 0)

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenData(user_id=user_id, username=username, role=role, token_version=token_version)
    
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_token_type(token: str, expected_type: str) -> bool:
    """
    Verify that a token is of the expected type (access or refresh)
    
    Args:
        token: The JWT token
        expected_type: The expected type ("access" or "refresh")
        
    Returns:
        bool: True if token type matches
        
    Raises:
        HTTPException: If token type doesn't match
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_type = payload.get("type")
        
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}, got {token_type}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return True
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token type",
            headers={"WWW-Authenticate": "Bearer"},
        )


def validate_password_strength(password: str) -> bool:
    """
    Validate password meets complexity requirements
    
    Args:
        password: The password to validate
        
    Returns:
        bool: True if password is valid
        
    Raises:
        ValueError: If password doesn't meet requirements
    """
    if len(password) < 8:
        raise ValueError('Password must be at least 8 characters long')
    if not any(c.isupper() for c in password):
        raise ValueError('Password must contain at least one uppercase letter')
    if not any(c.islower() for c in password):
        raise ValueError('Password must contain at least one lowercase letter')
    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/' for c in password):
        raise ValueError('Password must contain at least one special character')
    return True


def ensure_utc_aware(dt: datetime) -> datetime:
    """
    Ensure datetime is UTC timezone-aware.
    
    This function handles the common issue of comparing timezone-naive and 
    timezone-aware datetimes. If the datetime is naive (no timezone info),
    it assumes it's in UTC and adds the timezone information.
    
    Args:
        dt: The datetime to convert
        
    Returns:
        datetime: A timezone-aware datetime in UTC
        
    Example:
        >>> naive_dt = datetime(2025, 1, 1, 12, 0, 0)
        >>> aware_dt = ensure_utc_aware(naive_dt)
        >>> aware_dt.tzinfo
        datetime.timezone.utc
    """
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # Datetime is naive, assume it's UTC and add timezone info
        return dt.replace(tzinfo=timezone.utc)
    
    # Datetime is already aware, convert to UTC if needed
    return dt.astimezone(timezone.utc)


async def authenticate_m2m_credentials(request_headers: Headers, users: List[User]) -> List[AuthenticatedUser]:
    """
    Authenticate M2M requests by matching request headers against user credentials.
    
    Args:
        request_headers: HTTP request headers to check against user credentials
        users: List of User objects to check credentials against
    
    Returns:
        List of authenticated users (with their credentials that matched)
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        authenticated_users = []
        
        for user in users:
            # Deactivated accounts must not be usable through their M2M credentials either
            if not user.is_active:
                continue

            # Check if user has credentials configured
            if not user.config or not user.config.credentials:
                continue
                
            user_credentials = user.config.credentials
            user_matched_credentials = {}
            
            # Check if any of the user's credentials match request headers
            for cred_key, cred_value in user_credentials.items():
                # Look for the credential key in request headers (case-insensitive)
                header_value = None
                for header_name, header_val in request_headers.items():
                    if header_name.lower() == cred_key.lower():
                        header_value = header_val
                        break
                
                # If header matches credential value (constant-time comparison)
                if header_value and cred_value and hmac.compare_digest(header_value.encode(), cred_value.encode()):
                    user_matched_credentials[cred_key] = cred_value
            
            # If user has at least one matching credential, add to authenticated list
            if user_matched_credentials:
                authenticated_users.append({
                    'user': user,
                    'matched_credentials': user_matched_credentials
                })
                logger.info(f"User {user.username} authenticated via M2M credentials: {list(user_matched_credentials.keys())}")
        
        return authenticated_users
        
    except Exception as e:
        logger.error(f"Error during M2M authentication: {str(e)}")
        return []
