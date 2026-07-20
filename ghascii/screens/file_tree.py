"""Repository file-tree browser screen."""

from typing import Any

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

    def _build_entries(
        self, tree: list[dict]
    ) -> list[tuple[str, str, dict]]:
        """Build a nested, indented ASCII tree from a flat GitHub tree."""
        files = [e for e in tree if e.get("type") == "blob"]
        root: dict[str, Any] = {"dirs": {}, "files": {}}

        for file_entry in files:
            path = file_entry.get("path", "")
            if not path:
                continue
            parts = path.split("/")
            node = root
            for i, part in enumerate(parts[:-1]):
                if part not in node["dirs"]:
                    node["dirs"][part] = {
                        "dirs": {},
                        "files": {},
                        "path": "/".join(parts[: i + 1]),
                    }
                node = node["dirs"][part]
            node["files"][parts[-1]] = file_entry

        entries: list[tuple[str, str, dict]] = []

        def walk(node: dict[str, Any], depth: int) -> None:
            indent = "    " * depth
            for name in sorted(node["dirs"]):
                sub = node["dirs"][name]
                entries.append(("dir", f"{indent}[D] {name}", {"path": sub["path"]}))
                walk(sub, depth + 1)
            for name in sorted(node["files"]):
                file_entry = node["files"][name]
                entries.append(("file", f"{indent}[F] {name}", file_entry))

        walk(root, 0)
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
        for _kind, display, _entry in self.filtered_entries:
            list_view.append(ListItem(Static(display, markup=False)))

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
            kind, _display, entry = self.filtered_entries[index]
            if kind == "file":
                path = entry.get("path", "")
                if path:
                    self.app.push_screen(
                        CodeViewScreen(self.github, self.owner, self.repo, path)
                    )
