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
        background: black;
        color: white;
    }

    #login-screen, #clone-screen, #help-screen, #error-screen {
        align: center middle;
    }

    #login-box {
        width: 70;
        height: auto;
        padding: 2 3;
        background: ansi_bright_black;
    }
    #login-title {
        text-align: center;
        text-style: bold;
        color: cyan;
        padding-bottom: 1;
    }
    #login-status {
        text-align: center;
        color: white;
        padding-bottom: 1;
    }
    #login-button {
        text-align: center;
        text-style: bold;
        color: black;
        background: cyan;
        padding: 1 2;
    }

    #repo-title, #tree-title, #code-title, #revisions-title {
        dock: top;
        height: auto;
        padding: 0 2;
        text-style: bold;
        background: ansi_bright_black;
        color: white;
    }

    #repo-footer, #tree-footer, #code-footer, #clone-footer, #revisions-footer {
        dock: bottom;
        height: auto;
        padding: 0 2;
        background: ansi_bright_black;
        color: white;
    }

    Input {
        height: auto;
        margin: 0 2;
        padding: 0 1;
        background: ansi_bright_black;
        color: white;
    }
    Input:focus {
        background: cyan;
        color: black;
    }

    #repo-list, #file-tree, #revisions-list {
        width: 100%;
        height: 1fr;
        padding: 0 1;
        background: ansi_bright_black;
    }

    ListView > ListItem {
        padding: 0 1;
        background: black;
        color: white;
    }
    ListView > ListItem.-highlight {
        background: white;
        color: black;
        text-style: bold;
    }

    #file-tree {
        background: ansi_bright_black;
        color: white;
    }
    #file-tree > .tree--cursor {
        background: white;
        color: black;
        text-style: bold;
    }

    #code-view {
        width: 100%;
        height: 1fr;
        scrollbar-size: 0 0;
        background: black;
    }
    #code-view:focus {
        background-tint: black 0%;
    }

    #clone-box {
        width: 70;
        height: auto;
        padding: 2 3;
        background: ansi_bright_black;
    }
    #clone-title {
        text-style: bold;
        color: cyan;
        padding-bottom: 1;
    }
    #clone-log {
        height: auto;
        max-height: 20;
        background: black;
    }

    #error-box, #help-box {
        width: 60;
        height: auto;
        padding: 2 3;
        background: ansi_bright_black;
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
        color: white;
    }
    #error-dismiss, #help-footer {
        text-align: center;
        color: white;
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
