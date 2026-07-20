"""GitHub device-flow login screen."""

import asyncio

import httpx
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Static

from ghascii.auth import poll_for_token, save_token, start_device_flow


class LoginScreen(Screen):
    """Guides the user through GitHub device-flow authentication."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("enter", "login", "Login"),
    ]

    def __init__(self) -> None:
        super().__init__(id="login-screen")
        self.http_client = httpx.AsyncClient(follow_redirects=True)

    def compose(self) -> None:
        box = Vertical(
            Static(
                "Authenticate with GitHub to view your repositories.\n\n"
                "Press Enter to start device login.",
                id="login-status",
            ),
            Center(Static("[ Login ]", id="login-button")),
            id="login-box",
            classes="modal-box",
        )
        box.border_title = " "
        box.border_subtitle = "enter: login | q: quit"
        yield box

    def action_login(self) -> None:
        self._start_login()

    def _start_login(self) -> None:
        status = self.query_one("#login-status", Static)
        status.update("Requesting device code from GitHub...")
        self.run_worker(self._do_login(), exclusive=True)

    async def _do_login(self) -> None:
        status = self.query_one("#login-status", Static)
        try:
            device = await start_device_flow(self.http_client)
            user_code = device["user_code"]
            uri = device.get("verification_uri", "https://github.com/login/device")
            interval = device.get("interval", 5)
            status.update(
                f"Open: {uri}\n"
                f"Enter code: {user_code}\n\n"
                "Waiting for authorization..."
            )
            token = await poll_for_token(
                self.http_client,
                device["device_code"],
                interval=interval,
            )
            save_token(token)
            status.update("Login successful. Loading repositories...")
            await asyncio.sleep(0.3)
            from ghascii.github import GitHubClient
            from ghascii.screens.repo_list import RepoListScreen

            github = GitHubClient(token)
            self.app.switch_screen(RepoListScreen(github))
        except httpx.HTTPError as e:
            status.update(f"Network error: {e}")
        except Exception as e:
            status.update(f"Error: {e}")

    async def on_unmount(self) -> None:
        await self.http_client.aclose()
