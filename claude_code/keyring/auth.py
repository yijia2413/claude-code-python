import os
from typing import Optional

try:
    import keyring
except ImportError:
    keyring = None

SERVICE_NAME = "claude-py"

def is_keyring_available() -> bool:
    """
    Checks if keyring library is installed and has a functional backend.
    """
    if keyring is None:
        return False
    try:
        # Try a quick test read to ensure backend is not completely broken
        keyring.get_password(SERVICE_NAME, "test_availability")
        return True
    except Exception:
        return False

def get_secure_credential(username: str) -> Optional[str]:
    """
    Safely retrieves a password/credential from the system keychain.
    """
    if not is_keyring_available():
        return None
    try:
        return keyring.get_password(SERVICE_NAME, username)
    except Exception:
        return None

def set_secure_credential(username: str, value: str) -> bool:
    """
    Safely writes a password/credential to the system keychain.
    """
    if not is_keyring_available():
        return False
    try:
        keyring.set_password(SERVICE_NAME, username, value)
        return True
    except Exception:
        return False

def delete_secure_credential(username: str) -> bool:
    """
    Safely deletes a password/credential from the system keychain.
    """
    if not is_keyring_available():
        return False
    try:
        keyring.delete_password(SERVICE_NAME, username)
        return True
    except Exception:
        return False

# High level helper functions for API KEY
def get_api_key() -> Optional[str]:
    return get_secure_credential("CLAUDE_API_KEY")

def set_api_key(api_key: str) -> bool:
    return set_secure_credential("CLAUDE_API_KEY", api_key)

def delete_api_key() -> bool:
    return delete_secure_credential("CLAUDE_API_KEY")

# High level helper functions for BASE URL
def get_base_url() -> Optional[str]:
    return get_secure_credential("CLAUDE_BASE_URL")

def set_base_url(base_url: str) -> bool:
    return set_secure_credential("CLAUDE_BASE_URL", base_url)

# High level helper functions for MODEL NAME
def get_model_name() -> Optional[str]:
    return get_secure_credential("CLAUDE_MODEL_NAME")

def set_model_name(model_name: str) -> bool:
    return set_secure_credential("CLAUDE_MODEL_NAME", model_name)
