import os
from pathlib import Path
from typing import List, Optional, Union
from pydantic import field_validator, ConfigDict, Field

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

class Settings(BaseSettings):
    # Nouvelle configuration Pydantic V2
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Ignore les champs non définis
    )
    
    # Application
    app_name: str = "DAAV Backend API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # External API timeouts (Visions/PDC)
    vision_api_timeout_seconds: int = Field(
        default=30,
        ge=30,
        description="Default timeout in seconds for Visions/PDC HTTP calls"
    )
    
    # Database
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "daav_datasets"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "app.log"
    log_max_size: str = "10MB"
    log_backup_count: int = 5

    # Security logging (configurable)
    security_log_file: str = "security.log"
    security_log_level: str = "INFO"
    security_log_max_size: str = "10MB"
    security_log_backup_count: int = 5
    
    # CORS - peut être une string ou une liste
    cors_origins: Union[List[str], str] = ["http://localhost:4200", "http://127.0.0.1:4200"]
    
    # Security middleware settings
    security_rate_limit: int = Field(default=100, description="Max requests per time window")
    security_time_window: int = Field(default=60, description="Time window in seconds")
    security_enabled: bool = Field(default=True, description="Enable security middleware")
    
    # Authentication & Authorization
    allow_public_registration: bool = Field(
        default=False, 
        description="Allow public user registration. If False, only admins can create users"
    )
    
    # JWT Configuration
    jwt_secret_key: str = Field(
        default="your-secret-key-change-this-in-production-please-min-32-chars",
        description="Secret key for JWT token encoding/decoding. CHANGE THIS IN PRODUCTION!"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="Algorithm used for JWT token encoding"
    )
    jwt_access_token_expire_minutes: int = Field(
        default=60,
        description="Access token expiration time in minutes"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=90,
        description="Refresh token expiration time in days"
    )

    # Field Encryption Configuration
    field_encryption_key: Optional[str] = Field(
        default=None,
        description=(
            "Fernet key for encrypting sensitive dataset fields (passwords, tokens) at rest in MongoDB. "
            "Generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    )

    # Email Configuration (SMTP)
    smtp_host: str = Field(
        default="smtp.gmail.com",
        description="SMTP server host"
    )
    smtp_port: int = Field(
        default=587,
        description="SMTP server port"
    )
    smtp_username: Optional[str] = Field(
        default=None,
        description="SMTP username (email address)"
    )
    smtp_password: Optional[str] = Field(
        default=None,
        description="SMTP password or app password"
    )
    smtp_from_email: Optional[str] = Field(
        default=None,
        description="Email address to send from"
    )
    smtp_from_name: str = Field(
        default="DAAV Application",
        description="Sender name for emails"
    )
    smtp_use_tls: bool = Field(
        default=True,
        description="Use TLS for SMTP connection"
    )
    
    # Password Reset Configuration
    password_reset_token_expire_hours: int = Field(
        default=1,
        description="Password reset token expiration time in hours"
    )
    frontend_url: str = Field(
        default="http://localhost:4200",
        description="Frontend URL for password reset links"
    )
    
    # File uploads
    upload_dir: str = "uploads"
    max_file_size: Union[int, str] = 100 * 1024 * 1024  # 100MB

    directory_white_list : Union[List[str], str] = []
    
    # Route Access Control - Domain whitelist only
    domain_whitelist: Union[List[str], str] = Field(
        default=[],
        description="List of whitelisted domains that can access routes without authentication"
    )

    @field_validator('directory_white_list', 'cors_origins', 'domain_whitelist', mode='before')
    @classmethod
    def parse_str_list_tolist(cls, v):
        """Parse from string or list to list"""
        if isinstance(v, str):
            # Si c'est une string séparée par des virgules
            if ',' in v and not v.startswith('['):
                return [origin.strip() for origin in v.split(',')]
            # Si c'est déjà du JSON
            elif v.startswith('['):
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    return [v]  # Fallback sur une seule origine
            else:
                return [v] if v else []  # Une seule origine ou liste vide
        return v  # Déjà une liste

    @field_validator('max_file_size', mode='before')
    @classmethod
    def parse_max_file_size(cls, v):
        """Parse max file size from string like '100MB' to bytes"""
        if isinstance(v, str):
            v = v.upper()
            if v.endswith('MB'):
                return int(v[:-2]) * 1024 * 1024
            elif v.endswith('KB'):
                return int(v[:-2]) * 1024
            elif v.endswith('GB'):
                return int(v[:-2]) * 1024 * 1024 * 1024
            elif v.isdigit():
                return int(v)
            else:
                # Fallback
                return 100 * 1024 * 1024
        return v

    @field_validator('port', mode='before')
    @classmethod
    def parse_port(cls, v):
        """Parse port from string to int"""
        if isinstance(v, str):
            return int(v)
        return v

    @field_validator('log_backup_count', mode='before')
    @classmethod
    def parse_log_backup_count(cls, v):
        """Parse log backup count from string to int"""
        if isinstance(v, str):
            return int(v)
        return v
    
    @field_validator('jwt_secret_key')
    @classmethod
    def validate_jwt_secret_key(cls, v):
        """Validate JWT secret key length for security"""
        if v == "your-secret-key-change-this-in-production-please-min-32-chars":
            import logging
            logging.warning("⚠️  Using default JWT_SECRET_KEY - CHANGE THIS IN PRODUCTION!")
        elif len(v) < 32:
            raise ValueError('JWT_SECRET_KEY must be at least 32 characters long for security')
        return v

    @field_validator('field_encryption_key')
    @classmethod
    def validate_field_encryption_key(cls, v):
        """Validate Fernet key format. If not set, key is derived from JWT_SECRET_KEY at runtime."""
        if v is None:
            return v  # _get_fernet() will derive from JWT_SECRET_KEY automatically
        from cryptography.fernet import Fernet
        try:
            Fernet(v.encode())
        except Exception:
            raise ValueError(
                "FIELD_ENCRYPTION_KEY must be a valid Fernet key. "
                "Generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        return v

    @classmethod
    def parse_jwt_expiration(cls, v):
        """Parse JWT expiration times from string to int"""
        if isinstance(v, str):
            return int(v)
        return v

    @field_validator('upload_dir', mode='before')
    @classmethod
    def resolve_upload_dir(cls, v):
        """Resolve upload directory  from absolute or relative path"""
        if not v:
            return "uploads"
        #already an absolute path    
        if os.path.isabs(v):
            return v
        
        # build the path from app root
        app_dir = Path(__file__).parent.parent 
        upload_path = app_dir / v
        return str(upload_path.resolve())

# Global settings instance
settings = Settings()