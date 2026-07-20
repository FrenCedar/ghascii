"""Repository file-tree browser screen."""

from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Input, ListItem, ListView, Static

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
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("/", "focus_filter", "Filter"),
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
        self.filtered_entries: list[tuple[str, str, dict]] = []

    def compose(self) -> None:
        yield Static(f"{self.owner}/{self.repo}", id="tree-title")
        yield Input(
            placeholder="Filter files...",
            id="tree-filter",
            disabled=True,
        )
        yield ListView(id="file-tree")
        yield Static(
            "q: quit | backspace: back | /: filter | j/k: move | enter: open | c: clone",
            id="tree-footer",
        )

    def on_mount(self) -> None:
        self.run_worker(self._load_tree(), exclusive=True)

    def _entry_text(self, kind: str, path: str) -> str:
        prefix = "[D]" if kind == "dir" else "[F]"
        return f"{prefix} {path}"

    async def _load_tree(self) -> None:
        list_view = self.query_one("#file-tree", ListView)
        filter_input = self.query_one("#tree-filter", Input)
        list_view.clear()
        filter_input.disabled = True
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
            self._apply_filter()
        except Exception as e:
            list_view.clear()
            list_view.append(ListItem(Static(f"Error: {e}", markup=False)))
        finally:
            filter_input.disabled = False

    def _build_entries(self, tree: list[dict]) -> list[tuple[str, str, dict]]:
        files = [e for e in tree if e.get("type") == "blob"]
        dirs = {e["path"].rsplit("/", 1)[0] for e in files if "/" in e["path"]}
        entries: list[tuple[str, str, dict]] = []
        for d in sorted(dirs):
            entries.append(("dir", d, {"path": d}))
        for f in sorted(files, key=lambda x: x.get("path", "")):
            entries.append(("file", f.get("path", ""), f))
        return entries

    def _apply_filter(self) -> None:
        filter_input = self.query_one("#tree-filter", Input)
        list_view = self.query_one("#file-tree", ListView)
        query = filter_input.value.lower()
        self.filtered_entries = [
            entry for entry in self.entries if query in entry[1].lower()
        ]
        list_view.clear()
        if not self.filtered_entries:
            list_view.append(ListItem(Static("No matching files.", markup=False)))
            return
        for kind, path, _entry in self.filtered_entries:
            list_view.append(ListItem(Static(self._entry_text(kind, path), markup=False)))

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "tree-filter":
            self._apply_filter()

    def action_refresh(self) -> None:
        self.run_worker(self._load_tree(), exclusive=True)

    def action_clone(self) -> None:
        if not self.clone_url:
            self.notify("No clone URL available for this repository.", severity="error")
            return
        self.app.push_screen(
            CloneProgressScreen(self.owner, self.repo, self.clone_url)
        )

    def action_cursor_down(self) -> None:
        self.query_one("#file-tree", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#file-tree", ListView).action_cursor_up()

    def action_focus_filter(self) -> None:
        self.query_one("#tree-filter", Input).focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        index = event.index
        if 0 <= index < len(self.filtered_entries):
            kind, path, _entry = self.filtered_entries[index]
            if kind == "file":
                self.app.push_screen(
                    CodeViewScreen(self.github, self.owner, self.repo, path)
                )
