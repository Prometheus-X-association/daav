"""
Application secrets: JWT_SECRET_KEY and FIELD_ENCRYPTION_KEY.

No default value is shipped for these secrets. When one of them is not configured,
a temporary value is generated on first start and stored in SECRETS_DIR/<NAME>_TMP,
so that it survives restarts and is shared by all workers. An error is logged at
every start until the value is copied to <NAME> and saved in a secrets vault.
"""
import logging
import os
import secrets
import tempfile
from pathlib import Path
from typing import Callable, Dict, Optional

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# Placeholder JWT secrets shipped by previous versions (settings, docker-compose.yml,
# .env.example, README). They are public: they are refused as JWT_SECRET_KEY and only
# used to decrypt data encrypted with them, so that it can be re-encrypted.
PUBLIC_DEFAULT_JWT_SECRETS = (
    "your-secret-key-change-this-in-production-please-min-32-chars",
    "change-this-to-a-random-secret-min-32-chars-in-production",
    "change-this-to-a-strong-random-secret-key-min-32-characters-REQUIRED",
    "change-this-to-a-strong-random-secret-key-min-32-characters",
)

SECRET_GENERATORS: Dict[str, Callable[[], str]] = {
    "JWT_SECRET_KEY": lambda: secrets.token_urlsafe(64),
    "FIELD_ENCRYPTION_KEY": lambda: Fernet.generate_key().decode(),
}

LOSS_CONSEQUENCES = {
    "JWT_SECRET_KEY": "if it is lost or changed, users only have to log in again",
    "FIELD_ENCRYPTION_KEY": "if it is lost, the credentials stored in the datasets can no longer be decrypted",
}


def tmp_secret_path(name: str, secrets_dir: str) -> Path:
    """Path of the temporary secret file <NAME>_TMP"""
    return Path(secrets_dir) / f"{name}_TMP"


def read_tmp_secret(name: str, secrets_dir: str) -> Optional[str]:
    """Read the temporary secret <NAME>_TMP, None if it has not been generated"""
    try:
        value = tmp_secret_path(name, secrets_dir).read_text().strip()
    except (FileNotFoundError, NotADirectoryError):
        return None
    return value or None


def load_or_create_tmp_secret(name: str, secrets_dir: str) -> str:
    """Return the temporary secret <NAME>_TMP, generating it on first call.

    The file is published atomically (hard link of a complete, owner-only temp file),
    so workers starting at the same time all end up with the same value.
    """
    existing = read_tmp_secret(name, secrets_dir)
    if existing:
        return existing

    directory = Path(secrets_dir)
    try:
        directory.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=directory, prefix=f".{name}.")
        try:
            with os.fdopen(fd, "w") as tmp_file:
                tmp_file.write(SECRET_GENERATORS[name]() + "\n")
            os.link(tmp_name, tmp_secret_path(name, secrets_dir))
        except FileExistsError:
            pass  # Another worker generated it first: use its value
        finally:
            os.unlink(tmp_name)
    except OSError as e:
        raise RuntimeError(
            f"{name} is not set and a temporary key could not be written to {directory}: {e}. "
            f"Set {name} in the environment or make SECRETS_DIR writable."
        ) from e

    return read_tmp_secret(name, secrets_dir)


def log_temporary_secrets(temporary_secrets: Dict[str, str]) -> None:
    """Log an error for each secret that uses a generated temporary value"""
    for name, path in temporary_secrets.items():
        logger.error(
            "%s is not set: using the temporary key generated in %s. "
            "Copy this value to %s (backendApi/.env or docker-compose.yml) "
            "and save it in a secrets vault (password manager, Vault...): %s.",
            name, path, name, LOSS_CONSEQUENCES[name],
        )
