"""Smoke tests for ghascii screens."""

import asyncio
from contextlib import ExitStack
from unittest.mock import AsyncMock, patch

import pytest
from textual.widgets import Input, ListView, Static, Tree

from ghascii.app import GhasciiApp
from ghascii.github import GitHubClient
from ghascii.screens.code_view import CodeViewScreen
from ghascii.screens.file_tree import FileTreeScreen
from ghascii.screens.login import LoginScreen
from ghascii.screens.repo_list import RepoListScreen


@pytest.mark.asyncio
async def test_app_opens_login_screen_without_token() -> None:
    """The app should present the login screen when no token is saved."""
    with patch("ghascii.app.load_token", return_value=None):
        app = GhasciiApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            assert isinstance(app.screen, LoginScreen)


@pytest.mark.asyncio
async def test_navigate_to_code_view() -> None:
    """With a saved token, the app should list repos, open a tree, and view a file."""
    demo_repo = {
        "name": "demo",
        "language": "Python",
        "updated_at": "2024-01-01T00:00:00Z",
        "private": False,
        "owner": {"login": "testuser"},
    }
    demo_tree = [{"path": "README.md", "type": "blob", "sha": "blobsha"}]

    async def wait_for(predicate, timeout: float = 5.0) -> None:
        deadline = asyncio.get_event_loop().time() + timeout
        while not predicate() and asyncio.get_event_loop().time() < deadline:
            await pilot.pause()
            await asyncio.sleep(0.05)
        assert predicate()

    def list_contains_text(text: str) -> bool:
        return any(
            text in str(static.render())
            for static in app.screen.query("#repo-list ListItem Static")
        )

    def tree_contains_text(text: str) -> bool:
        tree = app.screen.query_one("#file-tree", Tree)

        def _walk(node):
            yield node
            for child in node.children:
                yield from _walk(child)

        return any(text in str(node.label) for node in _walk(tree.root))

    patches = {
        "verify_token": AsyncMock(return_value={"login": "testuser"}),
        "list_repositories": AsyncMock(return_value=[demo_repo]),
        "get_default_branch": AsyncMock(return_value="main"),
        "get_latest_commit_sha": AsyncMock(return_value="commitsha"),
        "get_commit_tree_sha": AsyncMock(return_value="treesha"),
        "get_tree": AsyncMock(return_value=demo_tree),
        "get_file_content": AsyncMock(return_value="# Hello\n"),
    }
    with patch("ghascii.app.load_token", return_value="fake-token"):
        app = GhasciiApp()
        with ExitStack() as stack:
            for name, mock in patches.items():
                stack.enter_context(
                    patch.object(GitHubClient, name, mock)
                )
            async with app.run_test() as pilot:
                await pilot.pause()
                assert isinstance(app.screen, RepoListScreen)

                await wait_for(lambda: list_contains_text("demo"))
                app.screen.query_one("#repo-list", ListView).focus()
                await pilot.pause()
                await pilot.press("down", "enter")
                await wait_for(lambda: isinstance(app.screen, FileTreeScreen))

                await wait_for(lambda: tree_contains_text("README.md"))
                app.screen.query_one("#file-tree", Tree).focus()
                await pilot.pause()
                await pilot.press("down", "enter")
                await wait_for(lambda: isinstance(app.screen, CodeViewScreen))


@pytest.mark.asyncio
async def test_filter_repositories() -> None:
    """The repo list filter input should narrow displayed repositories."""
    demo_repo = {
        "name": "demo",
        "language": "Python",
        "updated_at": "2024-01-01T00:00:00Z",
        "private": False,
        "owner": {"login": "testuser"},
    }
    other_repo = {
        "name": "other-project",
        "language": "Rust",
        "updated_at": "2024-02-02T00:00:00Z",
        "private": True,
        "owner": {"login": "testuser"},
    }

    async def wait_for(predicate, timeout: float = 5.0) -> None:
        deadline = asyncio.get_event_loop().time() + timeout
        while not predicate() and asyncio.get_event_loop().time() < deadline:
            await pilot.pause()
            await asyncio.sleep(0.05)
        assert predicate()

    def list_contains_text(text: str) -> bool:
        return any(
            text in str(static.render())
            for static in app.screen.query("#repo-list ListItem Static")
        )

    with patch("ghascii.app.load_token", return_value="fake-token"):
        app = GhasciiApp()
        with patch.object(
            GitHubClient, "verify_token", AsyncMock(return_value={"login": "testuser"})
        ):
            with patch.object(
                GitHubClient,
                "list_repositories",
                AsyncMock(return_value=[demo_repo, other_repo]),
            ):
                async with app.run_test() as pilot:
                    await wait_for(lambda: list_contains_text("demo"))
                    await wait_for(lambda: list_contains_text("other-project"))

                    await pilot.press("/")
                    await pilot.pause()
                    filter_input = app.screen.query_one("#repo-filter", Input)
                    assert not filter_input.has_class("hidden")
                    await pilot.press("o", "t", "h")
                    await wait_for(lambda: list_contains_text("other-project"))
                    await wait_for(lambda: not list_contains_text("demo"))

