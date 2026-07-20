"""Generic error modal screen."""

from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static


class ErrorScreen(Screen):
    """Displays an error message that can be dismissed with Enter/Escape."""

    BINDINGS = [
        ("enter", "pop_screen", "Dismiss"),
        ("escape", "pop_screen", "Dismiss"),
    ]

    def __init__(self, message: str) -> None:
        super().__init__(id="error-screen")
        self.message = message

    def compose(self) -> None:
        box = Vertical(
            Static(self.message, id="error-message"),
            id="error-box",
            classes="modal-box",
        )
        box.border_title = "Error"
        box.border_subtitle = "enter/esc: dismiss"
        yield box

    def action_pop_screen(self) -> None:
        self.app.pop_screen()
