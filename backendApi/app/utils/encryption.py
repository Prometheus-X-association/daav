"""
Symmetric encryption utility for sensitive dataset fields (passwords, tokens, secrets).

Values are encrypted with FIELD_ENCRYPTION_KEY (see settings). When it is not configured,
a temporary key is generated on first start (see app.config.secret_keys).

Previous keys are still accepted for decryption, so that existing data stays readable
and can be re-encrypted with the current key (see reencrypt_field):
  - the key derived from JWT_SECRET_KEY (HKDF), used when FIELD_ENCRYPTION_KEY was not set
  - the keys derived from the public placeholder JWT secrets of previous versions
  - FIELD_ENCRYPTION_KEY_TMP, once a different FIELD_ENCRYPTION_KEY has been configured

To generate a dedicated key:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
import base64
import logging
from functools import lru_cache
from typing import Optional, Tuple

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.config.secret_keys import PUBLIC_DEFAULT_JWT_SECRETS, read_tmp_secret
from app.config.settings import settings

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


@lru_cache(maxsize=8)
def _read_tmp_field_key(secrets_dir: str) -> Optional[str]:
    return read_tmp_secret("FIELD_ENCRYPTION_KEY", secrets_dir)


@lru_cache(maxsize=8)
def _build_fernets(current_key: str, jwt_secret: str, tmp_key: Optional[str]) -> Tuple[Fernet, MultiFernet]:
    """Return the current key and a MultiFernet that also accepts the previous keys."""
    current = Fernet(current_key.encode())
    previous_keys = [_derive_key_from_jwt(secret) for secret in (jwt_secret, *PUBLIC_DEFAULT_JWT_SECRETS)]
    if tmp_key and tmp_key != current_key:
        previous_keys.append(tmp_key.encode())
    return current, MultiFernet([current, *(Fernet(key) for key in previous_keys)])


def _get_fernets() -> Tuple[Fernet, MultiFernet]:
    return _build_fernets(
        settings.field_encryption_key,
        settings.jwt_secret_key,
        _read_tmp_field_key(settings.secrets_dir),
    )


def encrypt_field(value: Optional[str]) -> Optional[str]:
    """Encrypt a string value before DB write. Returns enc:<ciphertext>."""
    if not value or value.startswith(_ENC_PREFIX):
        return value
    current, _ = _get_fernets()
    return _ENC_PREFIX + current.encrypt(value.encode()).decode()


def decrypt_field(value: Optional[str]) -> Optional[str]:
    """Decrypt a string value after DB read.
    Returns plain text or the original value if not encrypted / not decryptable."""
    if not value or not value.startswith(_ENC_PREFIX):
        return value
    _, all_keys = _get_fernets()
    try:
        return all_keys.decrypt(value[len(_ENC_PREFIX):].encode()).decode()
    except InvalidToken:
        logger.error("Failed to decrypt field value — wrong key or corrupted data")
        return value


def reencrypt_field(value: Optional[str]) -> Optional[str]:
    """Return the value encrypted with the current key, or None if it already is.

    Plain text values are encrypted, values encrypted with a previous key are re-encrypted.
    Raises InvalidToken if the value cannot be decrypted with any known key.
    """
    if not value:
        return None
    if not value.startswith(_ENC_PREFIX):
        return encrypt_field(value)
    current, all_keys = _get_fernets()
    token = value[len(_ENC_PREFIX):].encode()
    try:
        current.decrypt(token)
        return None
    except InvalidToken:
        return _ENC_PREFIX + all_keys.rotate(token).decode()
