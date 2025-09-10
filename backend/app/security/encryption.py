"""
Secure token encryption using Fernet (AES-128-CBC with HMAC-SHA256).

Fernet guarantees that a message encrypted using it cannot be manipulated
or read without the key. Uses AES in CBC mode with a 128-bit key for
encryption, PKCS7 padding, and HMAC using SHA256 for authentication.
"""

from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings
import hashlib
import base64
import logging

logger = logging.getLogger(__name__)

_fernet_instance = None


def _get_fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is not None:
        return _fernet_instance

    key = settings.ENCRYPTION_KEY
    if key:
        try:
            _fernet_instance = Fernet(key.encode() if isinstance(key, str) else key)
            return _fernet_instance
        except Exception:
            logger.warning("ENCRYPTION_KEY is not a valid Fernet key; deriving one from it")
            derived = hashlib.sha256(key.encode()).digest()
            _fernet_instance = Fernet(base64.urlsafe_b64encode(derived))
            return _fernet_instance

    # Fallback: derive from JWT_SECRET_KEY (local dev only)
    if settings.JWT_SECRET_KEY:
        logger.warning("No ENCRYPTION_KEY set; deriving from JWT_SECRET_KEY (not recommended for production)")
        derived = hashlib.sha256(settings.JWT_SECRET_KEY.encode()).digest()
        _fernet_instance = Fernet(base64.urlsafe_b64encode(derived))
        return _fernet_instance

    raise ValueError("No encryption key configured. Set ENCRYPTION_KEY in environment.")


async def store_encrypted_token(user_id: str, token: str) -> str:
    """Encrypt and return the GitHub access token."""
    encrypted = encrypt_github_token(token)
    return encrypted


def encrypt_github_token(token: str) -> str:
    """Encrypt GitHub token using Fernet (AES)."""
    f = _get_fernet()
    return f.encrypt(token.encode()).decode()


def decrypt_github_token(encrypted_token: str) -> str:
    """Decrypt GitHub token using Fernet (AES)."""
    f = _get_fernet()
    try:
        return f.decrypt(encrypted_token.encode()).decode()
    except InvalidToken:
        logger.error("Failed to decrypt token -- key may have changed or token is corrupted")
        raise ValueError("Token decryption failed")


async def retrieve_github_token(encrypted_token_ref: str) -> str:
    """Retrieve GitHub token from encrypted reference."""
    return decrypt_github_token(encrypted_token_ref)
