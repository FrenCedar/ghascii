"""Repository list screen."""

from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import ListItem, ListView, Static

from ghascii.github import GitHubClient
from ghascii.screens.file_tree import FileTreeScreen


class RepoListScreen(Screen):
    """Displays repositories owned by the authenticated user."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

    def __init__(self, github: GitHubClient) -> None:
        super().__init__()
        self.github = github
        self.repos: list[dict] = []

    def compose(self) -> None:
        yield Static("Your repositories", id="repo-title")
        yield ListView(id="repo-list")
        yield Static("q: quit | r: refresh | enter: open", id="repo-footer")

    def on_mount(self) -> None:
        self.run_worker(self._load_repos(), exclusive=True)

    async def _load_repos(self) -> None:
        list_view = self.query_one("#repo-list", ListView)
        list_view.clear()
        list_view.append(ListItem(Static("Loading...", markup=False)))
        try:
            self.repos = await self.github.list_repositories()
            list_view.clear()
            if not self.repos:
                list_view.append(ListItem(Static("No repositories found.", markup=False)))
                return
            for repo in self.repos:
                name = repo.get("name", "")
                lang = repo.get("language") or "-"
                updated = repo.get("updated_at", "")[:10]
                vis = "private" if repo.get("private") else "public"
                text = f"{name:<32} {lang:<12} {updated:<12} {vis}"
                list_view.append(ListItem(Static(text, markup=False)))
        except Exception as e:
            list_view.clear()
            list_view.append(ListItem(Static(f"Error: {e}", markup=False)))

    def action_refresh(self) -> None:
        self.run_worker(self._load_repos(), exclusive=True)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        index = event.index
        if 0 <= index < len(self.repos):
            repo = self.repos[index]
            owner = repo.get("owner", {}).get("login", "")
            name = repo.get("name", "")
            clone_url = repo.get("clone_url", "")
            self.app.push_screen(
                FileTreeScreen(self.github, owner, name, clone_url)
            )
