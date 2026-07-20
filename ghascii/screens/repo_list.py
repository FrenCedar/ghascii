"""Repository list screen."""

from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Input, ListItem, ListView, Static

from ghascii.github import GitHubClient
from ghascii.screens.file_tree import FileTreeScreen


class RepoListScreen(Screen):
    """Displays repositories owned by the authenticated user."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("/", "focus_filter", "Filter"),
        ("escape", "focus_list", "List"),
    ]

    def __init__(self, github: GitHubClient) -> None:
        super().__init__()
        self.github = github
        self.repos: list[dict] = []
        self.filtered_repos: list[dict] = []

    def compose(self) -> None:
        yield Static("[cyan]ghascii[/cyan]  |  Your repositories", id="repo-title")
        yield Input(
            placeholder="Filter repositories... (Esc to return)",
            id="repo-filter",
            disabled=True,
        )
        yield ListView(id="repo-list")
        yield Static(
            "q: quit | r: refresh | /: filter | j/k: move | enter: open",
            id="repo-footer",
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
        list_view.append(ListItem(Static("Loading...", markup=False)))
        try:
            self.repos = await self.github.list_repositories()
            self._apply_filter()
            self.query_one("#repo-list", ListView).focus()
        except Exception as e:
            list_view.clear()
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
        list_view.clear()
        if not self.filtered_repos:
            list_view.append(ListItem(Static("No matching repositories.", markup=False)))
            return
        for repo in self.filtered_repos:
            list_view.append(ListItem(Static(self._repo_text(repo), markup=False)))
        if self.filtered_repos:
            list_view.index = 0

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "repo-filter":
            self._apply_filter()

    def action_refresh(self) -> None:
        self.run_worker(self._load_repos(), exclusive=True)

    def action_cursor_down(self) -> None:
        self.query_one("#repo-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#repo-list", ListView).action_cursor_up()

    def action_focus_filter(self) -> None:
        self.query_one("#repo-filter", Input).focus()

    def action_focus_list(self) -> None:
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
