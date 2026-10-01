import os
from cryptography.fernet import Fernet
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load env variables if not already loaded
load_dotenv()

# Get the key from env
_key = os.getenv("FERNET_KEY")
if not _key:
    logger.warning("FERNET_KEY is not set in environment! Telnet passwords will not be encrypted securely.")
    # Fallback to a hardcoded key so the app doesn't crash, but warn heavily
    _key = "0etvgIbu3IV3jPeXD7Wc7xb3aaIM9Y2gmzWHpo8LwBc="

try:
    _fernet = Fernet(_key.encode())
except Exception as e:
    logger.error(f"Failed to initialize Fernet with key: {e}")
    _fernet = None

def encrypt_password(password: str) -> str:
    """Encrypts a plaintext password."""
    if not password:
        return password
    if not _fernet:
        return password
    try:
        # If it looks like it's already encrypted (starts with gAAAAA), skip encryption
        if password.startswith("gAAAAA"):
            return password
        return _fernet.encrypt(password.encode()).decode()
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return password

def decrypt_password(encrypted_password: str) -> str:
    """Decrypts an encrypted password."""
    if not encrypted_password:
        return encrypted_password
    if not _fernet:
        return encrypted_password
    try:
        # Only decrypt if it looks like a Fernet token
        if encrypted_password.startswith("gAAAAA"):
            return _fernet.decrypt(encrypted_password.encode()).decode()
        return encrypted_password
    except Exception as e:
        # If decryption fails, maybe it wasn't encrypted, or key changed. Return original.
        logger.error(f"Decryption failed (maybe plain text?): {e}")
        return encrypted_password
