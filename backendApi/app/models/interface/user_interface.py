from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict, model_serializer
from beanie import Document, before_event, Insert
from app.enums.user_role import UserRole


class UserConfig(BaseModel):
    """User configuration with key-value credentials"""
    credentials: Dict[str, str] = Field(default_factory=dict, description="Key-value pairs for user credentials")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Additional user settings")
    
    model_config = ConfigDict(extra="allow")


class User(Document):
    """User model for authentication and authorization"""
    id: Optional[str] = Field(default=None, alias="_id")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    hashed_password: str = Field(..., description="Argon2 hashed password")
    role: UserRole = Field(default=UserRole.USER, description="User role (admin or user)")
    is_active: bool = Field(default=True, description="Account active status")
    must_change_password: bool = Field(default=False, description="User must change password before accessing the application")
    token_version: int = Field(default=0, description="Incremented on each password change: tokens issued with a previous version are refused")
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Configuration per user
    config: UserConfig = Field(default_factory=UserConfig, description="User-specific configuration")
    
    # Relations - IDs of owned resources
    owned_datasets: List[str] = Field(default_factory=list, description="List of owned dataset IDs")
    owned_workflows: List[str] = Field(default_factory=list, description="List of owned workflow IDs")
    
    # Shared resources - IDs of resources shared with this user
    shared_datasets: List[str] = Field(default_factory=list, description="List of dataset IDs shared with user")
    shared_workflows: List[str] = Field(default_factory=list, description="List of workflow IDs shared with user")
    
    # Deactivation fields
    deactivation_reason: Optional[str] = Field(default=None, description="Reason for deactivation")
    deactivated_at: Optional[datetime] = Field(default=None, description="Deactivation timestamp")
    deactivated_by: Optional[str] = Field(default=None, description="Admin user ID who deactivated the account")
    
    @before_event(Insert)
    async def generate_string_id(self):
        """Generate string ID before insertion"""
        if not self.id:
            self.id = str(ObjectId())
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must contain only letters, numbers, underscores and hyphens')
        return v.lower()
    
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        validate_assignment=True
    )
    
    class Settings:
        name = "users"
        use_state_management = True
        indexes = [
            [("username", 1)],  # Unique index
            [("email", 1)],     # Unique index
            [("role", 1)],
            [("created_at", -1)],
            [("is_active", 1)]
        ]
    
    @model_serializer(mode='wrap')
    def serialize_model(self, serializer, info) -> Dict[str, Any]:
        """Custom serializer to handle _id conversion"""
        data = serializer(self)
        if '_id' in data:
            data['id'] = str(data.pop('_id'))
        elif 'id' in data and data['id']:
            data['id'] = str(data['id'])
        
        # Never expose hashed_password in serialization
        data.pop('hashed_password', None)
        
        return data


class UserCreate(BaseModel):
    """Schema for user creation"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = Field(default=UserRole.USER)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserUpdate(BaseModel):
    """Schema for user update"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    config: Optional[UserConfig] = None
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        """Validate password complexity if provided"""
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)"""
    id: str
    username: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    must_change_password: bool = False
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    config: UserConfig = Field(default_factory=UserConfig)
    owned_datasets: List[str] = Field(default_factory=list)
    owned_workflows: List[str] = Field(default_factory=list)
    shared_datasets: List[str] = Field(default_factory=list)
    shared_workflows: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class UserConfigUpdate(BaseModel):
    """Schema for updating user configuration"""
    credentials: Optional[Dict[str, str]] = None
    settings: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(extra="allow")


class PasswordResetToken(Document):
    """Password reset token model"""
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str = Field(..., description="User ID this token belongs to")
    token: str = Field(..., description="Reset token (hashed)")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(..., description="Token expiration timestamp")
    used: bool = Field(default=False, description="Whether token has been used")
    
    @field_validator('expires_at', mode='before')
    @classmethod
    def ensure_expires_at_timezone_aware(cls, v):
        """Ensure expires_at is timezone-aware (UTC)"""
        if v is None:
            return v
        if isinstance(v, datetime) and v.tzinfo is None:
            # If naive, assume UTC and add timezone info
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @before_event(Insert)
    async def generate_string_id(self):
        """Generate string ID before insertion"""
        if not self.id:
            self.id = str(ObjectId())
    
    class Settings:
        name = "password_reset_tokens"
        indexes = [
            "user_id",
            "token",
            "expires_at"
        ]
