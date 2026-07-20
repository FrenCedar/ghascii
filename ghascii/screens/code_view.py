"""File content viewer screen."""

from rich.markdown import Markdown
from rich.syntax import Syntax

from textual.screen import Screen
from textual.widgets import RichLog, Static

from ghascii.github import GitHubClient
from ghascii.ui import breadcrumb, keybar


class CodeViewScreen(Screen):
    """Displays a single file with ANSI syntax highlighting."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("backspace", "pop_screen", "Back"),
        ("h", "pop_screen", "Back"),
        ("v", "revisions", "Revisions"),
        ("j", "scroll_down", "Down"),
        ("k", "scroll_up", "Up"),
    ]

    def __init__(
        self,
        github: GitHubClient,
        owner: str,
        repo: str,
        path: str,
        ref: str = "HEAD",
    ) -> None:
        super().__init__()
        self.github = github
        self.owner = owner
        self.repo = repo
        self.path = path
        self.ref = ref

    def compose(self) -> None:
        yield Static(
            breadcrumb("repositories", f"{self.owner}/{self.repo}", self.path),
            classes="bar-top",
        )
        log = RichLog(id="code-view", wrap=False, highlight=True, classes="panel")
        log.border_title = self.path.rsplit("/", 1)[-1]
        log.border_subtitle = (
            self.ref[:12] if self.ref != "HEAD" else "latest"
        )
        yield log
        yield Static(
            keybar(
                ("j/k", "scroll"),
                ("v", "revisions"),
                ("h", "back"),
                ("q", "quit"),
            ),
            classes="bar-bottom",
        )

    def on_mount(self) -> None:
        self.query_one("#code-view", RichLog).focus()
        self.run_worker(self._load_file(), exclusive=True)

    async def _load_file(self) -> None:
        log = self.query_one("#code-view", RichLog)
        try:
            content = await self.github.get_file_content(
                self.owner, self.repo, self.path, ref=self.ref
            )
            log.clear()
            if self.path.lower().endswith((".md", ".markdown")):
                log.write(Markdown(content, hyperlinks=False))
            else:
                extension = (
                    self.path.rsplit(".", 1)[-1] if "." in self.path else "text"
                )
                syntax = Syntax(
                    content,
                    extension,
                    theme="ansi_dark",
                    line_numbers=True,
                    word_wrap=False,
                    background_color="default",
                )
                log.write(syntax)
        except Exception as e:
            log.write(f"Error loading file: {e}")

    def action_pop_screen(self) -> None:
        self.app.pop_screen()

    def action_scroll_down(self) -> None:
        self.query_one("#code-view", RichLog).scroll_relative(y=1, animate=False)

    def action_scroll_up(self) -> None:
        self.query_one("#code-view", RichLog).scroll_relative(y=-1, animate=False)

    def action_revisions(self) -> None:
        from ghascii.screens.revisions import RevisionsScreen

        self.app.push_screen(
            RevisionsScreen(self.github, self.owner, self.repo, self.path)
        )
