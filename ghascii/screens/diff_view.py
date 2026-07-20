"""Full-screen unified diff viewer for a single commit."""

from rich.syntax import Syntax
from textual.screen import Screen
from textual.widgets import RichLog, Static

from ghascii.github import GitHubClient
from ghascii.ui import breadcrumb, keybar


class DiffScreen(Screen):
    """Displays the unified diff of a commit against its parent."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("backspace", "pop_screen", "Back"),
        ("h", "pop_screen", "Back"),
        ("j", "scroll_down", "Down"),
        ("k", "scroll_up", "Up"),
    ]

    def __init__(
        self,
        github: GitHubClient,
        owner: str,
        repo: str,
        sha: str,
        author: str = "",
        date: str = "",
    ) -> None:
        super().__init__()
        self.github = github
        self.owner = owner
        self.repo = repo
        self.sha = sha
        self.author = author
        self.date = date

    def compose(self) -> None:
        header = f"{self.author} | {self.date}" if self.author or self.date else ""
        yield Static(
            breadcrumb(f"{self.owner}/{self.repo}", header),
            classes="bar-top",
        )
        log = RichLog(id="diff-view", wrap=False, highlight=False, classes="panel")
        log.border_title = f"diff@{self.sha[:7]}"
        yield log
        yield Static(
            keybar(
                ("j/k", "scroll"),
                ("h", "back"),
                ("q", "quit"),
            ),
            classes="bar-bottom",
        )

    def on_mount(self) -> None:
        self.query_one("#diff-view", RichLog).focus()
        self.run_worker(self._load_diff(), exclusive=True)

    async def _load_diff(self) -> None:
        log = self.query_one("#diff-view", RichLog)
        try:
            diff = await self.github.get_commit_diff(
                self.owner, self.repo, self.sha
            )
            log.clear()
            if not diff.strip():
                log.write("No changes in this commit.")
                return
            log.write(
                Syntax(
                    diff,
                    "diff",
                    theme="ansi_dark",
                    word_wrap=False,
                    background_color="default",
                )
            )
        except Exception as e:
            log.write(f"Error loading diff: {e}")

    def action_pop_screen(self) -> None:
        self.app.pop_screen()

    def action_scroll_down(self) -> None:
        self.query_one("#diff-view", RichLog).scroll_relative(y=1, animate=False)

    def action_scroll_up(self) -> None:
        self.query_one("#diff-view", RichLog).scroll_relative(y=-1, animate=False)
