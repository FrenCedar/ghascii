"""Main Textual application for ghascii."""

from textual.app import App

from ghascii.auth import load_token
from ghascii.github import GitHubClient
from ghascii.screens.help import HelpScreen
from ghascii.screens.login import LoginScreen
from ghascii.screens.menu import MenuScreen
from ghascii.screens.repo_list import RepoListScreen


class GhasciiApp(App):
    """ASCII-only GitHub TUI for headless Linux consoles."""

    CSS = """
    Screen {
        background: black;
        color: white;
    }

    /* --- Segment: top header bar (brand + breadcrumb) ------------------- */
    .bar-top {
        dock: top;
        height: 1;
        padding: 0 1;
        background: black;
    }

    /* --- Segment: bottom keybar ----------------------------------------- */
    .bar-bottom {
        dock: bottom;
        height: 1;
        padding: 0 1;
        background: black;
    }

    /* --- Segment: framed content panels --------------------------------- */
    .panel {
        border: ascii ansi_bright_black;
        border-title-color: white;
        border-title-style: bold;
        border-subtitle-color: ansi_bright_black;
        background: black;
    }
    .panel:focus {
        border: ascii cyan;
        border-title-color: cyan;
        border-subtitle-color: cyan;
    }

    /* --- Segment: filter panel (hidden until "/") ------------------------ */
    Input.panel {
        height: 3;
        margin: 0;
        padding: 0 1;
        background: black;
        color: white;
    }
    Input.panel:focus {
        background: black;
        color: white;
    }
    .hidden {
        display: none;
    }

    /* --- Lists, trees, code --------------------------------------------- */
    #repo-list, #file-tree, #revisions-list {
        width: 100%;
        height: 1fr;
        padding: 0 1;
    }

    /* --- Repository screen split: 2/3 files, 1/3 versions ---------------- */
    #tree-split {
        width: 100%;
        height: 1fr;
    }
    #tree-left {
        width: 2fr;
        height: 100%;
    }
    #version-list {
        width: 1fr;
        height: 100%;
        padding: 0 1;
    }
    #version-list ListItem Static {
        text-wrap: nowrap;
        text-overflow: clip;
    }

    ListView > ListItem {
        padding: 0 1;
        background: black;
        color: white;
    }
    ListView > ListItem.-highlight {
        background: black;
        color: white;
        text-style: none;
    }

    #file-tree {
        color: white;
    }
    #file-tree > .tree--cursor {
        background: black;
        color: white;
        text-style: none;
    }

    #code-view, #diff-view {
        width: 100%;
        height: 1fr;
        padding: 0 1;
        scrollbar-size: 0 0;
        background: black;
    }
    #code-view:focus, #diff-view:focus {
        background-tint: black 0%;
    }

    /* --- Modal screens (login, help, error, clone, menu) ----------------- */
    #login-screen, #clone-screen, #help-screen, #error-screen, #menu-screen, #settings-screen {
        align: center middle;
    }

    #menu-box {
        width: 30;
        height: auto;
        align: center middle;
        text-align: center;
        padding: 1 2;
    }
    #menu-title {
        text-align: center;
        text-style: bold;
        padding: 1 0;
    }
    #menu-list {
        width: 100%;
        height: auto;
    }
    #menu-list ListItem {
        text-align: center;
    }

    #settings-box {
        width: 50;
        height: auto;
        align: center middle;
        padding: 1 2;
    }
    #settings-title {
        text-align: center;
        text-style: bold;
        padding: 1 0;
    }

    .modal-box {
        width: 70;
        height: auto;
        padding: 1 2;
        border: ascii cyan;
        border-title-color: cyan;
        border-title-style: bold;
        border-subtitle-color: ansi_bright_black;
        background: black;
    }

    #login-status {
        text-align: center;
        color: white;
        padding: 1 0;
    }
    #login-button {
        text-align: center;
        text-style: bold;
        color: black;
        background: cyan;
        padding: 0 2;
    }

    #clone-log {
        height: auto;
        max-height: 20;
        background: black;
    }

    #error-message {
        padding: 1 0;
        color: red;
    }
    #help-text {
        padding: 1 0;
        color: white;
    }
    """

    BINDINGS = [
        ("escape", "menu", "Menu"),
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

    def action_menu(self) -> None:
        self.push_screen(MenuScreen())

    def action_quit(self) -> None:
        if self.github:
            self.run_worker(self.github.close())
        self.exit()
