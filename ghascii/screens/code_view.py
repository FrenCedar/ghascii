"""File content viewer screen."""

from rich.markdown import Markdown
from rich.syntax import Syntax

from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import RichLog, Static

from ghascii.github import GitHubClient


class CodeViewScreen(Screen):
    """Displays a single file with ANSI syntax highlighting."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("backspace", "pop_screen", "Back"),
    ]

    def __init__(
        self, github: GitHubClient, owner: str, repo: str, path: str
    ) -> None:
        super().__init__()
        self.github = github
        self.owner = owner
        self.repo = repo
        self.path = path

    def compose(self) -> None:
        yield Static(f"{self.owner}/{self.repo}: {self.path}", id="code-title")
        yield RichLog(id="code-view", wrap=False, highlight=True)
        yield Static("q: quit | backspace: back", id="code-footer")

    def on_mount(self) -> None:
        self.run_worker(self._load_file(), exclusive=True)

    async def _load_file(self) -> None:
        log = self.query_one("#code-view", RichLog)
        try:
            content = await self.github.get_file_content(
                self.owner, self.repo, self.path
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
                    theme="default",
                    line_numbers=True,
                    word_wrap=False,
                )
                log.write(syntax)
        except Exception as e:
            log.write(f"Error loading file: {e}")

    def action_pop_screen(self) -> None:
        self.app.pop_screen()
