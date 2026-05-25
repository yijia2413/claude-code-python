import sys
from unittest.mock import MagicMock, patch
import pytest

# Mock keyring library before importing auth
mock_keyring = MagicMock()
sys.modules['keyring'] = mock_keyring

# Import auth module which now uses mock_keyring
from claude_code.keyring.auth import (
    get_api_key,
    set_api_key,
    delete_api_key,
    get_base_url,
    set_base_url,
    get_model_name,
    set_model_name,
    is_keyring_available
)

def test_keyring_availability():
    # Setup test mock response for checking availability
    mock_keyring.get_password.return_value = None
    assert is_keyring_available() is True

def test_secure_credentials_flow():
    # Mock behavior of keyring
    credentials_store = {}
    
    def mock_get(service, username):
        if service == "claude-py":
            return credentials_store.get(username)
        return None
        
    def mock_set(service, username, val):
        if service == "claude-py":
            credentials_store[username] = val
        return None

    def mock_delete(service, username):
        if service == "claude-py" and username in credentials_store:
            del credentials_store[username]
        return None

    mock_keyring.get_password.side_effect = mock_get
    mock_keyring.set_password.side_effect = mock_set
    mock_keyring.delete_password.side_effect = mock_delete

    # Test API KEY Flow
    assert get_api_key() is None
    assert set_api_key("sk-ant-testkey") is True
    assert get_api_key() == "sk-ant-testkey"
    
    # Test Base URL Flow
    assert get_base_url() is None
    assert set_base_url("https://api.example.com") is True
    assert get_base_url() == "https://api.example.com"

    # Test Model Name Flow
    assert get_model_name() is None
    assert set_model_name("claude-3-haiku") is True
    assert get_model_name() == "claude-3-haiku"

    # Clean API KEY
    assert delete_api_key() is True
    assert get_api_key() is None
