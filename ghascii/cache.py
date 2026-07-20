"""Simple disk cache for GitHub API responses."""

import hashlib
import json
import os
import time
from pathlib import Path

from ghascii.config import CACHE_DIR

_API_CACHE_DIR = CACHE_DIR / "api"


def _cache_path(method: str, url: str) -> Path:
    key = hashlib.sha256(f"{method}:{url}".encode("utf-8")).hexdigest()
    return _API_CACHE_DIR / key[:2] / key[2:]


def get(method: str, url: str, ttl: int) -> dict | list | None:
    """Return cached data if it exists and is still fresh, otherwise None."""
    path = _cache_path(method, url)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            entry = json.load(f)
        if time.time() - entry["timestamp"] > ttl:
            return None
        return entry["data"]
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def set(method: str, url: str, data: dict | list) -> None:
    """Store API response data on disk."""
    path = _cache_path(method, url)
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"timestamp": time.time(), "data": data}
    with path.open("w", encoding="utf-8") as f:
        json.dump(entry, f)
    os.chmod(path, 0o600)
