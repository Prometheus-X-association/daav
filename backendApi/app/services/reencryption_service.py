"""
Re-encryption of the sensitive dataset fields with the current FIELD_ENCRYPTION_KEY.

Run at startup: plain text values are encrypted and values encrypted with a previous
key (see app.utils.encryption) are re-encrypted with the current one.
"""
import logging
from typing import Dict

from cryptography.fernet import InvalidToken

from app.models.interface.dataset_interface import Dataset
from app.utils.encryption import reencrypt_field

logger = logging.getLogger(__name__)


async def reencrypt_sensitive_fields() -> Dict[str, int]:
    """Re-encrypt the sensitive fields of all datasets.

    Returns the number of fields re-encrypted and of fields that could not be decrypted.
    """
    sensitive_fields = {
        dataset_class.Settings.class_id_value: dataset_class._sensitive_fields
        for dataset_class in Dataset.__subclasses__()
        if dataset_class._sensitive_fields
    }
    counts = {"reencrypted": 0, "failed": 0}
    collection = Dataset.get_pymongo_collection()

    async for document in collection.find({"type": {"$in": list(sensitive_fields)}}):
        for field in sensitive_fields[document["type"]]:
            value = document.get(field)
            if not isinstance(value, str):
                continue
            try:
                new_value = reencrypt_field(value)
            except InvalidToken:
                logger.error(f"Dataset {document['_id']}: field '{field}' cannot be decrypted with any known key")
                counts["failed"] += 1
                continue
            if new_value is None:
                continue
            # Conditional update: workers running this at the same time do not overwrite each other
            result = await collection.update_one(
                {"_id": document["_id"], field: value},
                {"$set": {field: new_value}},
            )
            counts["reencrypted"] += result.modified_count

    return counts
