"""Global pause/options menu for ghascii."""

from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import ListItem, ListView, Static

from ghascii.screens.settings import SettingsScreen


class MenuScreen(Screen):
    """Options menu reachable from any screen via Escape."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "resume", "Resume"),
    ]

    def compose(self):
        yield Vertical(
            Static("ghascii", id="menu-title"),
            ListView(
                ListItem(Static("Resume")),
                ListItem(Static("Settings")),
                ListItem(Static("Quit")),
                id="menu-list",
            ),
            id="menu-box",
            classes="modal-box",
        )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        index = event.index
        if index == 0:
            self.action_resume()
        elif index == 1:
            self.app.push_screen(SettingsScreen())
        elif index == 2:
            self.action_quit()

    def on_mount(self) -> None:
        self.query_one("#menu-list", ListView).focus()

    def action_resume(self) -> None:
        self.app.pop_screen()

    def action_quit(self) -> None:
        self.app.action_quit()
