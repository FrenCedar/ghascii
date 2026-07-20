"""Help screen showing key bindings."""

from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static


class HelpScreen(Screen):
    """Displays keyboard controls for ghascii."""

    BINDINGS = [("q", "pop_screen", "Close")]

    def __init__(self) -> None:
        super().__init__(id="help-screen")

    def compose(self) -> None:
        text = (
            "up/down or j/k  move selection / scroll\n"
            "enter           open selected item / view diff\n"
            "tab             switch files/versions panel\n"
            "backspace or h  go back\n"
            "/               filter the current list\n"
            "esc             close filter / return to list\n"
            "r               refresh\n"
            "c               clone current repo\n"
            "v               revision history (file view)\n"
            "?               show this help\n"
            "q               quit"
        )
        box = Vertical(
            Static(text, id="help-text"),
            id="help-box",
            classes="modal-box",
        )
        box.border_title = "Help"
        box.border_subtitle = "q: close"
        yield box

    def action_pop_screen(self) -> None:
        self.app.pop_screen()
