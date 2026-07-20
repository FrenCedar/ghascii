"""Repository list screen."""

from pathlib import Path

from rich.text import Text
from textual.screen import Screen
from textual.widgets import Input, ListItem, ListView, Static

from ghascii.github import GitHubClient
from ghascii.screens.file_tree import FileTreeScreen
from ghascii.screens.update import UpdateScreen
from ghascii.ui import keybar


class RepoListScreen(Screen):
    """Displays repositories owned by the authenticated user."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("/", "focus_filter", "Filter"),
        ("escape", "focus_list", "List"),
        ("u", "update", "Update"),
    ]

    def __init__(self, github: GitHubClient) -> None:
        super().__init__()
        self.github = github
        self.username = ""
        self.repos: list[dict] = []
        self.filtered_repos: list[dict] = []
        self._repo_labels: list[Static] = []
        self._repo_texts: list[str] = []

    def _header_text(self) -> Text:
        return Text(f"{self.username} >", style="bold white")

    def compose(self) -> None:
        yield Static(self._header_text(), id="repo-header", classes="bar-top")
        filter_input = Input(
            placeholder="type to filter...",
            id="repo-filter",
            classes="panel hidden",
            disabled=True,
        )
        filter_input.border_title = "Filter"
        filter_input.border_subtitle = "esc: close"
        yield filter_input
        list_view = ListView(id="repo-list", classes="panel")
        list_view.border_title = "Your repositories"
        yield list_view
        yield Static(
            keybar(
                ("j/k", "move"),
                ("enter", "open"),
                ("/", "filter"),
                ("r", "refresh"),
                ("u", "update"),
                ("?", "help"),
                ("q", "quit"),
            ),
            classes="bar-bottom",
        )

    def on_mount(self) -> None:
        self.run_worker(self._load_repos(), exclusive=True)

    def _repo_text(self, repo: dict) -> str:
        name = repo.get("name", "")
        lang = repo.get("language") or "-"
        updated = repo.get("updated_at", "")[:10]
        vis = "private" if repo.get("private") else "public"
        return f"{name:<32} {lang:<12} {updated:<12} {vis}"

    async def _load_repos(self) -> None:
        list_view = self.query_one("#repo-list", ListView)
        filter_input = self.query_one("#repo-filter", Input)
        list_view.clear()
        filter_input.disabled = True
        list_view.border_subtitle = "loading..."
        list_view.append(ListItem(Static("Loading...", markup=False)))
        try:
            user = await self.github.verify_token()
            self.username = user.get("login", "")
            self.query_one("#repo-header", Static).update(self._header_text())
            self.repos = await self.github.list_repositories()
            self._apply_filter()
            self.query_one("#repo-list", ListView).focus()
        except Exception as e:
            list_view.clear()
            list_view.border_subtitle = "error"
            list_view.append(ListItem(Static(f"Error: {e}", markup=False)))
        finally:
            filter_input.disabled = False

    def _apply_filter(self) -> None:
        filter_input = self.query_one("#repo-filter", Input)
        list_view = self.query_one("#repo-list", ListView)
        query = filter_input.value.lower()
        self.filtered_repos = [
            repo for repo in self.repos if query in repo.get("name", "").lower()
        ]
        self._repo_labels = []
        self._repo_texts = []
        list_view.clear()
        if query:
            list_view.border_subtitle = (
                f"{len(self.filtered_repos)}/{len(self.repos)} repos"
            )
        else:
            list_view.border_subtitle = f"{len(self.repos)} repos"
        if not self.filtered_repos:
            list_view.append(
                ListItem(Static("No matching repositories.", markup=False))
            )
            return
        for repo in self.filtered_repos:
            text = self._repo_text(repo)
            label = Static(f"  {text}", markup=False)
            self._repo_labels.append(label)
            self._repo_texts.append(text)
            list_view.append(ListItem(label))
        if self.filtered_repos:
            list_view.index = 0
            self._sync_selection()

    def _sync_selection(self) -> None:
        list_view = self.query_one("#repo-list", ListView)
        index = list_view.index
        for i, label in enumerate(self._repo_labels):
            original = self._repo_texts[i]
            if index == i:
                label.update(Text(f"> {original}", style="reverse"))
            else:
                label.update(Text(f"  {original}"))

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        self._sync_selection()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "repo-filter":
            self._apply_filter()

    def action_refresh(self) -> None:
        self.run_worker(self._load_repos(), exclusive=True)

    def action_update(self) -> None:
        root = Path(__file__).resolve().parents[2]
        self.app.push_screen(UpdateScreen(root))

    def action_cursor_down(self) -> None:
        self.query_one("#repo-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#repo-list", ListView).action_cursor_up()

    def action_focus_filter(self) -> None:
        filter_input = self.query_one("#repo-filter", Input)
        filter_input.remove_class("hidden")
        filter_input.focus()

    def action_focus_list(self) -> None:
        filter_input = self.query_one("#repo-filter", Input)
        if not filter_input.value:
            filter_input.add_class("hidden")
        self.query_one("#repo-list", ListView).focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        index = event.index
        if 0 <= index < len(self.filtered_repos):
            repo = self.filtered_repos[index]
            owner = repo.get("owner", {}).get("login", "")
            name = repo.get("name", "")
            clone_url = repo.get("clone_url", "")
            self.app.push_screen(
                FileTreeScreen(self.github, owner, name, clone_url)
            )
