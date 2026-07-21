"""Settings screen for ghascii configuration."""

from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Static

from ghascii.config import DEFAULT_CONFIG, load_config, save_config


class SettingsScreen(Screen):
    """Edit ghascii configuration values."""

    BINDINGS = [
        ("backspace", "pop_screen", "Back"),
        ("escape", "pop_screen", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__(id="settings-screen")
        self.config = load_config()

    def compose(self):
        yield Vertical(
            Static("Settings", id="settings-title"),
            Static("GitHub OAuth client ID"),
            Input(
                value=self.config.get("oauth_client_id", ""),
                id="oauth-client-id",
            ),
            Static("Local clone directory"),
            Input(
                value=self.config.get(
                    "local_clone_dir", DEFAULT_CONFIG["local_clone_dir"]
                ),
                id="local-clone-dir",
            ),
            Horizontal(
                Button("Save", id="save", variant="primary"),
                Button("Back", id="back"),
            ),
            id="settings-box",
            classes="modal-box",
        )

    def on_mount(self) -> None:
        self.query_one("#oauth-client-id", Input).focus()

    def action_pop_screen(self) -> None:
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "save":
            self._save()
        elif button_id == "back":
            self.action_pop_screen()

    def _save(self) -> None:
        self.config["oauth_client_id"] = self.query_one(
            "#oauth-client-id", Input
        ).value.strip()
        self.config["local_clone_dir"] = self.query_one(
            "#local-clone-dir", Input
        ).value.strip()
        save_config(self.config)
        self.notify("Settings saved", severity="information")
