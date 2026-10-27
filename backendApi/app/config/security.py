"""
Security configuration for the DAAV application.
"""
import os
from pathlib import Path
from typing import List


class SecurityConfig:
    """Centralized security configuration."""
    
    # Static allowed base directories
    _STATIC_ALLOWED_DIRECTORIES = [
        "ptx",
        "inputs"
    ]
    
    # Allowed file extensions
    ALLOWED_FILE_EXTENSIONS = {
        '.csv', '.json', '.parquet', '.xlsx', '.xls',
        '.tsv', '.avro', '.feather', '.orc', '.txt',
        '.yml', '.yaml', '.xml', '.log', '.md',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg',
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma',
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'
    }
    
    
    # Dangerous patterns for path traversal
    DANGEROUS_PATH_PATTERNS = [
    r'\.\.',   # Any .. sequence
    r'~/',     # Home directory
    r'/etc/',  # Unix system
    r'/proc/', # Unix system
    r'/sys/',  # Unix system
    r'/var/',  # Unix system
    r'C:',     # Windows drive
    r'\\\\',   # UNC paths
    r'\$',     # Environment variables
    r'%2e%2e', # URL encoded .. (case insensitive)
    r'%252e',  # Double URL encoded
    r'%c0%af', # Unicode encoding attacks
    r'\.{3,}', # Multiple dots like ....
    r'\.\./',  # Relative up
    r'\.\.\\', # Relative up (Windows)
    ]

    # Suspicious patterns in HTTP request URLs and headers (regex, case insensitive).
    # Narrower than DANGEROUS_PATH_PATTERNS to avoid false positives on regular
    # values (e.g. "doc:1", "ghosts", "http://")
    SUSPICIOUS_REQUEST_PATTERNS = [
    r'\.{2,}[/\\]',                  # Path traversal: ../ ..\
    r'[/\\]\.{2,}$',                 # Path traversal: trailing /..
    r'~/',                           # Home directory
    r'/etc/',                        # Unix system
    r'/proc/',                       # Unix system
    r'/sys/',                        # Unix system
    r'/var/',                        # Unix system
    r'(^|[^a-z0-9])[a-z]:[/\\]',     # Windows drive (C:\ or C:/)
    r'\\\\',                         # UNC paths
    r'\$\{|\$\(',                    # Variable / command expansion
    r'%2e%2e',                       # URL encoded ..
    r'%252e',                        # Double URL encoded
    r'%c0%af',                       # Unicode encoding attacks
    r'[/\\](passwd|shadow|hosts)\b', # Sensitive system files
    ]

    @classmethod
    def get_allowed_base_directories(cls) -> List[str]:
        """Returns the complete list of allowed directories including the dynamic upload folder."""
        from app.config.settings import settings
        
        allowed_dirs = []
        
        # Add static directories with proper path resolution
        for static_dir in cls._STATIC_ALLOWED_DIRECTORIES:
            # Add both variants for compatibility
            allowed_dirs.append(static_dir)
            allowed_dirs.append(f"app/{static_dir}")

        for white_list_dir in settings.directory_white_list:
            # Ensure each directory is absolute or relative to the app root
            if not os.path.isabs(white_list_dir):
                white_list_dir = os.path.join("app", white_list_dir)
            allowed_dirs.append(white_list_dir)    
        
        # Add configured upload directory
        upload_dir = settings.upload_dir
        if upload_dir:
            allowed_dirs.append(upload_dir)
            upload_basename = os.path.basename(upload_dir)
            if upload_basename not in allowed_dirs:
                allowed_dirs.append(upload_basename)
                allowed_dirs.append(f"app/{upload_basename}")
    
        return allowed_dirs
    
    
    
def log_security_event(event_type: str, details: str, severity: str = "WARNING"):
    """Log a security event."""
    import logging
    
    security_logger = logging.getLogger('security')
    
    message = f"{event_type}: {details}"
    
    if severity == "CRITICAL":
        security_logger.critical(message)
    elif severity == "ERROR":
        security_logger.error(message)
    elif severity == "WARNING":
        security_logger.warning(message)
    else:
        security_logger.info(message)
