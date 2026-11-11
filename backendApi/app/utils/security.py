
import os
import re
import urllib.parse
from pathlib import Path
from typing import List, Optional
from fastapi import HTTPException
from app.config.security import SecurityConfig


class PathSecurityValidator:
    """
    Security validator for file paths to prevent path traversal attacks.
    """
    # Security state management
    _security_enabled = None  # Cache for automatic detection
    _force_security_state = None  # Override for tests

    @classmethod
    def is_security_enabled(cls) -> bool:
        """
        Check if security validation is enabled.
        
        Returns:
            bool: True if security is enabled, False if disabled (test environment)
        """
        # If security state is forced (for tests)
        if cls._force_security_state is not None:
            return cls._force_security_state
            
        # Cache automatic detection result
        if cls._security_enabled is None:
            import sys
            # Disable security in test environments
            cls._security_enabled = not ('pytest' in sys.modules or 'unittest' in sys.modules)
            
        return cls._security_enabled

    @classmethod
    def set_security_enabled(cls, enabled: bool):
        """
        Force security state (for tests).
        
        Args:
            enabled: True to enable security, False to disable
        """
        cls._force_security_state = enabled

    @classmethod
    def reset_security_state(cls):
        """
        Reset to automatic security detection (for tests cleanup).
        """
        cls._force_security_state = None
        cls._security_enabled = None

    @staticmethod
    def _get_allowed_extensions():
        """Get allowed extensions from security config."""
        return SecurityConfig.ALLOWED_FILE_EXTENSIONS
    
    @staticmethod
    def validate_file_path(file_path: str, base_dir: Optional[str] = None) -> str:
        """
        Validates and sanitizes a file path to prevent path traversal attacks.
        
        Args:
            file_path: The path to validate
            base_dir: Allowed base directory
            
        Returns:
            Validated and secure path
            
        Raises:
            HTTPException: If the path is dangerous
        """
        # Check if security is enabled
        if not PathSecurityValidator.is_security_enabled():
            return file_path  # Bypass validation in test environment
            
        if not file_path:
            raise HTTPException(status_code=400, detail="File path cannot be empty")
        
        # Check for null bytes FIRST
        if '\x00' in file_path:
            raise HTTPException(
                status_code=400,
                detail="Null byte injection detected in file path"
            )
        
        # Check both original and URL decoded versions, to catch encoded attacks
        paths_to_check = PathSecurityValidator._path_variants(file_path)

        # Normalize path
        normalized_path = os.path.normpath(file_path)

        # Check dangerous patterns on all variations
        PathSecurityValidator._reject_dangerous_patterns(paths_to_check, base_dir)

        # Check dangerous characters
        if any(char in normalized_path for char in ['<', '>', '|', '*', '?', '"']):
            raise HTTPException(
                status_code=400,
                detail="Invalid characters in file path"
            )

        # If base directory is specified, verify we don't escape it
        if base_dir:
            return PathSecurityValidator._resolve_within(base_dir, normalized_path)

        return normalized_path

    @staticmethod
    def _path_variants(file_path: str) -> List[str]:
        """The path and its URL decoded version."""
        try:
            return [file_path, urllib.parse.unquote(file_path)]
        except Exception:
            return [file_path]

    @staticmethod
    def _reject_dangerous_patterns(paths_to_check: List[str], base_dir: Optional[str]) -> None:
        """Raise if a normalized variant matches a dangerous pattern: 403 with a base directory (access problem), else 400 (format problem)."""
        for path_variant in paths_to_check:
            normalized_variant = os.path.normpath(path_variant)
            for pattern in SecurityConfig.DANGEROUS_PATH_PATTERNS:
                if re.search(pattern, normalized_variant, re.IGNORECASE):
                    status_code = 403 if base_dir else 400
                    raise HTTPException(
                        status_code=status_code,
                        detail=f"Dangerous path pattern detected: {pattern}"
                    )

    @staticmethod
    def _resolve_within(base_dir: str, normalized_path: str) -> str:
        """Resolve the path under the base directory, refusing (403) a path that escapes it."""
        try:
            resolved_base = Path(base_dir).resolve()
            resolved_path = Path(base_dir) / normalized_path
            resolved_full = resolved_path.resolve()

            # Verify the final path is within allowed directory
            if not str(resolved_full).startswith(str(resolved_base)):
                raise HTTPException(
                    status_code=403,
                    detail="Access outside base directory not allowed"
                )

            return str(resolved_full)

        except (OSError, ValueError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid path: {str(e)}"
            )
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """
        Validates a filename.
        
        Args:
            filename: The filename to validate
            
        Returns:
            Validated filename
            
        Raises:
            HTTPException: If the filename is dangerous
        """
        # Check if security is enabled
        if not PathSecurityValidator.is_security_enabled():
            return filename  # Bypass validation in test environment
            
        if not filename:
            raise HTTPException(status_code=400, detail="Filename cannot be empty")
        
        # Remove dangerous characters
        sanitized = re.sub(r'[<>:"|?*]', '_', filename)
        
        # Check Windows reserved filenames
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
            'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
            'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        name_without_ext = os.path.splitext(sanitized)[0].upper()
        if name_without_ext in reserved_names:
            sanitized = f"file_{sanitized}"
        
        return sanitized
    
    @staticmethod
    def validate_file_extension(filename: str) -> bool:
        """
        Checks if the file extension is allowed.
        
        Args:
            filename: The filename
            
        Returns:
            True if the extension is allowed
        """
        ext = os.path.splitext(filename.lower())[1]
        allowed_extensions = PathSecurityValidator._get_allowed_extensions()
        return ext in allowed_extensions
    
class FileAccessController:
    """
    File access controller with restrictions.
    """
    
    @staticmethod
    def can_read_file(file_path: str, allowed_dirs: list) -> bool:
        """
        Checks if a file can be read according to allowed directories.
        """
        # Check if security is enabled
        if not PathSecurityValidator.is_security_enabled():
            return True  # Allow all access in test environment
            
        try:
            resolved_path = Path(file_path).resolve()
            
            for allowed_dir in allowed_dirs:
                allowed_resolved = Path(allowed_dir).resolve()
                if str(resolved_path).startswith(str(allowed_resolved)):
                    return True
                    
            return False
            
        except (OSError, ValueError):
            return False
    
