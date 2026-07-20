"""Help screen showing key bindings."""

from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static


class HelpScreen(Screen):
    """Displays keyboard controls for ghascii."""

    BINDINGS = [("q", "pop_screen", "Close")]

    def compose(self) -> None:
        text = (
            "ghascii controls\n\n"
            "up/down or j/k  move selection\n"
            "enter           open selected item\n"
            "backspace or h  go back\n"
            "r               refresh\n"
            "c               clone current repo\n"
            "?               show this help\n"
            "q               quit"
        )
        yield Vertical(
            Static("Help", id="help-title"),
            Static(text, id="help-text"),
            Static("Press q to close", id="help-footer"),
            id="help-box",
        )
