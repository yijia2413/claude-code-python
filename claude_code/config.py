import os
import yaml
from typing import Optional, Dict, Any

def get_config_path() -> Optional[str]:
    """Find the path to config.yaml if it exists."""
    # Check current directory
    cwd_config = os.path.join(os.getcwd(), "config.yaml")
    if os.path.isfile(cwd_config):
        return cwd_config

    # Check ~/.claude_code/config.yaml
    home_config = os.path.expanduser("~/.claude_code/config.yaml")
    if os.path.isfile(home_config):
        return home_config

    return None

def load_config() -> Optional[Dict[str, Any]]:
    """Loads the config.yaml and returns the parsed dictionary."""
    path = get_config_path()
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config at {path}: {e}")
        return None

def get_active_provider_config() -> Optional[Dict[str, Any]]:
    """
    Returns the active provider configuration block merged with default_model.
    Example return: {"protocol": "openai", "api_key": "sk-...", "base_url": "...", "model": "moonshot-v1-auto"}
    """
    config = load_config()
    if not config:
        return None
    
    default_provider = config.get("default_provider")
    default_model = config.get("default_model")
    providers = config.get("providers", {})
    
    if not default_provider or default_provider not in providers:
        return None
        
    provider_config = providers[default_provider].copy()
    provider_config["model"] = default_model
    return provider_config
