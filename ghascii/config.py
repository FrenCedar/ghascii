"""Configuration paths and helpers for ghascii."""

import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "ghascii"
CONFIG_PATH = CONFIG_DIR / "config.json"
TOKEN_PATH = CONFIG_DIR / "token.json"
CACHE_DIR = Path.home() / ".cache" / "ghascii"

DEFAULT_CONFIG = {
    "oauth_client_id": "",
    "cache_ttl_repos": 300,
    "cache_ttl_tree": 600,
    "cache_ttl_blob": 3600,
    "local_clone_dir": str(Path.home() / ".cache" / "ghascii" / "repos"),
}


def ensure_dirs() -> None:
    """Create config and cache directories with restrictive permissions."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(CONFIG_DIR, 0o700)
    os.chmod(CACHE_DIR, 0o700)


def load_config() -> dict:
    """Load user config, merging with defaults."""
    ensure_dirs()
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG.copy()
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    except (json.JSONDecodeError, OSError):
        return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> None:
    """Persist user config."""
    ensure_dirs()
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    os.chmod(CONFIG_PATH, 0o600)
