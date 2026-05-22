"""
Symmetric encryption utility for sensitive dataset fields (passwords, tokens, secrets).

Key resolution order:
  1. FIELD_ENCRYPTION_KEY env var (explicit Fernet key — recommended in production)
  2. JWT_SECRET_KEY env var (derived via HKDF — zero-config fallback)
  3. No key → plain text stored with a warning

To generate a dedicated key:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
import base64
import os
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

logger = logging.getLogger(__name__)

_ENC_PREFIX = "enc:"


def _derive_key_from_jwt(jwt_secret: str) -> bytes:
    """Derive a 32-byte Fernet-compatible key from the JWT secret using HKDF-SHA256."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"daav-field-encryption-v1",
        info=b"dataset-credentials",
    )
    return base64.urlsafe_b64encode(hkdf.derive(jwt_secret.encode()))


def _get_fernet() -> Optional[Fernet]:
    # Priority 1: explicit dedicated key
    key = os.environ.get("FIELD_ENCRYPTION_KEY")
    if key:
        try:
            return Fernet(key.encode())
        except Exception:
            logger.error("FIELD_ENCRYPTION_KEY is not a valid Fernet key — falling back to JWT derivation")

    # Priority 2: derive from JWT secret (zero-config)
    jwt_secret = os.environ.get("JWT_SECRET_KEY")
    if jwt_secret:
        try:
            return Fernet(_derive_key_from_jwt(jwt_secret))
        except Exception:
            logger.error("Could not derive encryption key from JWT_SECRET_KEY")

    logger.warning("No encryption key available — sensitive dataset fields stored in plain text")
    return None


def encrypt_field(value: Optional[str]) -> Optional[str]:
    """Encrypt a string value before DB write.
    Returns enc:<ciphertext> or the original value if no key is configured."""
    if not value or value.startswith(_ENC_PREFIX):
        return value
    f = _get_fernet()
    if f is None:
        return value
    return _ENC_PREFIX + f.encrypt(value.encode()).decode()


def decrypt_field(value: Optional[str]) -> Optional[str]:
    """Decrypt a string value after DB read.
    Returns plain text or the original value if not encrypted / no key configured."""
    if not value or not value.startswith(_ENC_PREFIX):
        return value
    f = _get_fernet()
    if f is None:
        logger.warning("FIELD_ENCRYPTION_KEY not set — cannot decrypt stored field value")
        return value
    try:
        return f.decrypt(value[len(_ENC_PREFIX):].encode()).decode()
    except InvalidToken:
        logger.error("Failed to decrypt field value — wrong key or corrupted data")
        return value
