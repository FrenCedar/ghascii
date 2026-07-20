"""In-app self-update screen for ghascii."""

import asyncio
from pathlib import Path

from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import RichLog, Static

from ghascii.git import GitError, update_ghascii


class UpdateScreen(Screen):
    """Runs git pull + pip install -e . and shows the output."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("backspace", "pop_screen", "Back"),
    ]

    def __init__(self, root: Path) -> None:
        super().__init__(id="update-screen")
        self.root = root

    def compose(self) -> None:
        box = Vertical(
            RichLog(id="update-log", wrap=False, highlight=False),
            id="update-box",
            classes="modal-box",
        )
        box.border_title = "Updating ghascii"
        box.border_subtitle = "backspace: back | q: quit"
        yield box

    def on_mount(self) -> None:
        self.run_worker(self._update(), exclusive=True)

    async def _update(self) -> None:
        log = self.query_one("#update-log", RichLog)
        log.write(f"Pulling latest changes in {self.root}...")
        try:
            output = await asyncio.to_thread(update_ghascii, self.root)
            log.write(output)
            log.write("Update complete. Restart ghascii to use the new version.")
        except GitError as e:
            log.write(f"Update failed: {e}")

    def action_pop_screen(self) -> None:
        self.app.pop_screen()
