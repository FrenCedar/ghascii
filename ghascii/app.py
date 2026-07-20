"""Main Textual application for ghascii."""

from textual.app import App

from ghascii.auth import load_token
from ghascii.github import GitHubClient
from ghascii.screens.help import HelpScreen
from ghascii.screens.login import LoginScreen
from ghascii.screens.repo_list import RepoListScreen


class GhasciiApp(App):
    """ASCII-only GitHub TUI for headless Linux consoles."""

    CSS = """
    Screen {
        background: #0f172a;
        color: #e2e8f0;
    }

    #login-screen, #clone-screen, #help-screen, #error-screen {
        align: center middle;
    }

    #login-box {
        width: 70;
        height: auto;
        padding: 2 3;
        background: #1e293b;
    }
    #login-title {
        text-align: center;
        text-style: bold;
        color: cyan;
        padding-bottom: 1;
    }
    #login-status {
        text-align: center;
        color: #94a3b8;
        padding-bottom: 1;
    }
    #login-button {
        text-align: center;
        text-style: bold;
        color: black;
        background: cyan;
        padding: 1 2;
    }

    #repo-title, #tree-title, #code-title {
        dock: top;
        height: auto;
        padding: 0 2;
        text-style: bold;
        background: cyan;
        color: black;
    }

    #repo-footer, #tree-footer, #code-footer, #clone-footer {
        dock: bottom;
        height: auto;
        padding: 0 2;
        background: #1e293b;
        color: #e2e8f0;
    }

    Input {
        height: auto;
        margin: 0 2;
        padding: 0 1;
        background: #1e293b;
        color: #e2e8f0;
    }
    Input:focus {
        background: #334155;
    }

    #repo-list, #file-tree {
        width: 100%;
        height: 1fr;
        padding: 0 1;
        background: #0f172a;
    }

    ListView > ListItem {
        padding: 0 1;
        background: #0f172a;
        color: #e2e8f0;
    }
    ListView > ListItem.--highlight {
        background: cyan;
        color: black;
        text-style: bold;
    }

    #file-tree {
        background: #0f172a;
        color: #e2e8f0;
    }

    #code-view {
        width: 100%;
        height: 1fr;
        scrollbar-size: 0 0;
        background: #0f172a;
    }

    #clone-box {
        width: 70;
        height: auto;
        padding: 2 3;
        background: #1e293b;
    }
    #clone-title {
        text-style: bold;
        color: cyan;
        padding-bottom: 1;
    }
    #clone-log {
        height: auto;
        max-height: 20;
        background: #0f172a;
    }

    #error-box, #help-box {
        width: 60;
        height: auto;
        padding: 2 3;
        background: #1e293b;
    }
    #error-title, #help-title {
        text-align: center;
        text-style: bold;
        color: cyan;
        padding-bottom: 1;
    }
    #error-message {
        padding: 1 0;
        color: red;
    }
    #help-text {
        padding: 1 0;
        color: #e2e8f0;
    }
    #error-dismiss, #help-footer {
        text-align: center;
        color: #94a3b8;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("?", "help", "Help"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.github: GitHubClient | None = None

    async def on_mount(self) -> None:
        token = load_token()
        if token:
            self.github = GitHubClient(token)
            try:
                await self.github.verify_token()
                self.push_screen(RepoListScreen(self.github))
                return
            except Exception:
                self.github = None
        self.push_screen(LoginScreen())

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_quit(self) -> None:
        if self.github:
            self.run_worker(self.github.close())
        self.exit()
