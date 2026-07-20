"""Screen that shows git clone/update progress for the current repository."""

import asyncio
from pathlib import Path

from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import RichLog, Static

from ghascii.config import load_config
from ghascii.git import GitError, clone_or_update


class CloneProgressScreen(Screen):
    """Runs a git clone or pull and displays the output."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("backspace", "pop_screen", "Back"),
    ]

    def __init__(self, owner: str, repo: str, clone_url: str) -> None:
        super().__init__(id="clone-screen")
        self.owner = owner
        self.repo = repo
        self.clone_url = clone_url

    def compose(self) -> None:
        yield Vertical(
            Static(f"Cloning {self.owner}/{self.repo}...", id="clone-title"),
            RichLog(id="clone-log", wrap=False, highlight=False),
            Static("q: quit | backspace: back", id="clone-footer"),
            id="clone-box",
        )

    def on_mount(self) -> None:
        self.run_worker(self._clone(), exclusive=True)

    async def _clone(self) -> None:
        log = self.query_one("#clone-log", RichLog)
        config = load_config()
        dest = Path(config.get("local_clone_dir"))
        try:
            output = await asyncio.to_thread(
                clone_or_update,
                self.owner,
                self.repo,
                self.clone_url,
                dest,
            )
            log.write(output)
            log.write(f"Repository is at: {dest / self.owner / self.repo}")
        except GitError as e:
            log.write(f"Git error: {e}")

    def action_pop_screen(self) -> None:
        self.app.pop_screen()
