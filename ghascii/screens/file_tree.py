"""Repository file-tree browser screen."""

from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import ListItem, ListView, Static

from ghascii.github import GitHubClient
from ghascii.screens.clone_progress import CloneProgressScreen
from ghascii.screens.code_view import CodeViewScreen


class FileTreeScreen(Screen):
    """Displays a recursive file tree for a single repository."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("backspace", "pop_screen", "Back"),
        ("r", "refresh", "Refresh"),
        ("c", "clone", "Clone locally"),
    ]

    def __init__(
        self,
        github: GitHubClient,
        owner: str,
        repo: str,
        clone_url: str = "",
    ) -> None:
        super().__init__()
        self.github = github
        self.owner = owner
        self.repo = repo
        self.clone_url = clone_url
        self.entries: list[tuple[str, str, dict]] = []

    def compose(self) -> None:
        yield Static(f"{self.owner}/{self.repo}", id="tree-title")
        yield ListView(id="file-tree")
        yield Static(
            "q: quit | backspace: back | enter: open file | c: clone",
            id="tree-footer",
        )

    def on_mount(self) -> None:
        self.run_worker(self._load_tree(), exclusive=True)

    async def _load_tree(self) -> None:
        list_view = self.query_one("#file-tree", ListView)
        list_view.clear()
        list_view.append(ListItem(Static("Loading tree...", markup=False)))
        try:
            branch = await self.github.get_default_branch(self.owner, self.repo)
            commit_sha = await self.github.get_latest_commit_sha(
                self.owner, self.repo, branch
            )
            tree_sha = await self.github.get_commit_tree_sha(
                self.owner, self.repo, commit_sha
            )
            tree = await self.github.get_tree(self.owner, self.repo, tree_sha)
            self.entries = self._build_entries(tree)
            list_view.clear()
            if not self.entries:
                list_view.append(ListItem(Static("Empty repository.", markup=False)))
                return
            for kind, path, _entry in self.entries:
                prefix = "[D]" if kind == "dir" else "[F]"
                text = f"{prefix} {path}"
                list_view.append(ListItem(Static(text, markup=False)))
        except Exception as e:
            list_view.clear()
            list_view.append(ListItem(Static(f"Error: {e}", markup=False)))

    def _build_entries(self, tree: list[dict]) -> list[tuple[str, str, dict]]:
        files = [e for e in tree if e.get("type") == "blob"]
        dirs = {e["path"].rsplit("/", 1)[0] for e in files if "/" in e["path"]}
        entries: list[tuple[str, str, dict]] = []
        for d in sorted(dirs):
            entries.append(("dir", d, {"path": d}))
        for f in sorted(files, key=lambda x: x.get("path", "")):
            entries.append(("file", f.get("path", ""), f))
        return entries

    def action_refresh(self) -> None:
        self.run_worker(self._load_tree(), exclusive=True)

    def action_clone(self) -> None:
        if not self.clone_url:
            self.notify("No clone URL available for this repository.", severity="error")
            return
        self.app.push_screen(
            CloneProgressScreen(self.owner, self.repo, self.clone_url)
        )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        index = event.index
        if 0 <= index < len(self.entries):
            kind, path, _entry = self.entries[index]
            if kind == "file":
                self.app.push_screen(
                    CodeViewScreen(self.github, self.owner, self.repo, path)
                )
