"""GitHub device-flow OAuth helpers."""

import asyncio
import json
import os
import time

import httpx

from ghascii.config import TOKEN_PATH, load_config

GITHUB_DEVICE_CODE_URL = "https://github.com/login/device/code"
GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
ACCEPT_JSON = {"Accept": "application/json"}


def save_token(token: str) -> None:
    """Persist the OAuth access token with restricted permissions."""
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TOKEN_PATH.open("w", encoding="utf-8") as f:
        json.dump({"token": token}, f)
    os.chmod(TOKEN_PATH, 0o600)


def load_token() -> str | None:
    """Load a previously saved OAuth token, if any."""
    if not TOKEN_PATH.exists():
        return None
    try:
        with TOKEN_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("token")
    except (json.JSONDecodeError, OSError):
        return None


def clear_token() -> None:
    """Delete the saved token."""
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()


async def start_device_flow(client: httpx.AsyncClient) -> dict:
    """Begin GitHub device flow and return device data."""
    config = load_config()
    client_id = config.get("oauth_client_id", "")
    if not client_id:
        raise ValueError(
            "GitHub OAuth client_id not configured. "
            "Add it to ~/.config/ghascii/config.json: "
            '{"oauth_client_id": "YOUR_CLIENT_ID"}'
        )
    response = await client.post(
        GITHUB_DEVICE_CODE_URL,
        headers=ACCEPT_JSON,
        data={
            "client_id": client_id,
            "scope": "repo read:user",
        },
    )
    response.raise_for_status()
    return response.json()


async def poll_for_token(
    client: httpx.AsyncClient,
    device_code: str,
    interval: int = 5,
    timeout: int = 600,
) -> str:
    """Poll GitHub until the user authorizes the device."""
    config = load_config()
    client_id = config["oauth_client_id"]
    deadline = time.time() + timeout
    while time.time() < deadline:
        response = await client.post(
            GITHUB_ACCESS_TOKEN_URL,
            headers=ACCEPT_JSON,
            data={
                "client_id": client_id,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
        )
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            error = payload["error"]
            if error == "authorization_pending":
                await asyncio.sleep(interval)
                continue
            if error == "slow_down":
                interval += 5
                await asyncio.sleep(interval)
                continue
            raise RuntimeError(f"OAuth error: {error}")
        token = payload.get("access_token")
        if token:
            return token
        await asyncio.sleep(interval)
    raise TimeoutError("Device flow timed out")
