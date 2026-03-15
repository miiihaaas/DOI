"""Custom encrypted field using Fernet symmetric encryption."""

from __future__ import annotations

import base64
import hashlib
import logging

from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)


def _get_fernet():
    """Get Fernet instance using FERNET_KEY or derived from SECRET_KEY.

    Production deployments SHOULD set FERNET_KEY explicitly.
    Changing SECRET_KEY without FERNET_KEY will break existing encrypted data.
    """
    key = getattr(settings, "FERNET_KEY", None)
    if not key:
        logger.debug(
            "FERNET_KEY not set, deriving from SECRET_KEY. "
            "Set FERNET_KEY in production to avoid data loss on SECRET_KEY rotation."
        )
        digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(digest)
    elif isinstance(key, str):
        key = key.encode()
    return Fernet(key)


class EncryptedCharField(models.CharField):
    """CharField that encrypts value at rest using Fernet symmetric encryption.

    Encrypted values are stored as TextField in the database since
    Fernet tokens are longer than the original plaintext.
    """

    def get_prep_value(self, value):
        """Encrypt before saving to database."""
        if value is None or value == "":
            return value
        f = _get_fernet()
        return f.encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        """Decrypt when reading from database."""
        if value is None or value == "":
            return value
        try:
            f = _get_fernet()
            return f.decrypt(value.encode()).decode()
        except Exception:
            logger.exception(
                "Failed to decrypt EncryptedCharField value. "
                "This may indicate a FERNET_KEY/SECRET_KEY mismatch."
            )
            return ""  # Return empty string, not ciphertext

    def get_internal_type(self):
        """Use TextField storage since encrypted values are longer than originals."""
        return "TextField"
