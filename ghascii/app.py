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
    #login-screen { align: center middle; }
    #login-box { width: 70; height: auto; padding: 1 2; }
    #login-title { text-align: center; text-style: bold; }
    #repo-title, #tree-title, #code-title {
        dock: top;
        padding: 1 2;
        text-style: bold;
    }
    #repo-footer, #tree-footer, #code-footer {
        dock: bottom;
        padding: 0 2;
        color: white;
    }
    #repo-list, #file-tree { width: 100%; height: 1fr; }
    #code-view { width: 100%; height: 1fr; scrollbar-size: 0 0; }
    #clone-box { width: 70; height: auto; padding: 1 2; }
    #clone-title { text-style: bold; }
    #clone-log { height: auto; max-height: 20; }
    #error-box, #help-box { width: 60; height: auto; padding: 1 2; }
    #error-title, #help-title { text-align: center; text-style: bold; }
    #error-message { padding: 1 0; }
    #help-text { padding: 1 0; }
    ListView > ListItem { padding: 0 1; }
    ListView > ListItem.--highlight { background: blue; }
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
