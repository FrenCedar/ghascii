"""Generic error modal screen."""

from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Static


class ErrorScreen(Screen):
    """Displays an error message that can be dismissed with Enter/Escape."""

    BINDINGS = [
        ("enter", "pop_screen", "Dismiss"),
        ("escape", "pop_screen", "Dismiss"),
    ]

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> None:
        yield Vertical(
            Static("Error", id="error-title"),
            Static(self.message, id="error-message"),
            Center(Static("[ Press Enter or Escape ]", id="error-dismiss")),
            id="error-box",
        )
