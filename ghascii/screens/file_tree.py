"""Repository browser screen: file tree (2/3) plus version panel (1/3)."""

from typing import Any

from rich.text import Text
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Input, ListItem, ListView, Static, Tree
from textual.widgets.tree import TreeNode

from ghascii.github import GitHubClient
from ghascii.screens.clone_progress import CloneProgressScreen
from ghascii.screens.code_view import CodeViewScreen
from ghascii.screens.diff_view import DiffScreen
from ghascii.ui import breadcrumb, keybar


class AsciiTree(Tree):
    """Tree widget that renders as a flat, ASCII-only dropdown."""

    show_guides = False
    guide_depth = 0
    ICON_NODE = "+ "
    ICON_NODE_EXPANDED = "- "
    LINES = {
        "default": ("", "", "", ""),
        "bold": ("", "", "", ""),
        "double": ("", "", "", ""),
    }

    def render_label(
        self, node: TreeNode[Any], base_style, style
    ) -> Text:
        node_label = node._label.copy()
        node_label.stylize(style)
        node_label.stylize("white")
        if node._allow_expand:
            prefix = (
                self.ICON_NODE_EXPANDED if node.is_expanded else self.ICON_NODE,
                base_style,
            )
        else:
            prefix = ("  ", base_style)
        is_cursor = node == self.cursor_node
        indicator = ("> ", style) if is_cursor else ("  ", base_style)
        text = Text.assemble(indicator, prefix, node_label)
        if is_cursor:
            text.stylize("reverse")
        return text


class FileTreeScreen(Screen):
    """Split repository browser: file tree left, commit versions right."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("backspace", "pop_screen", "Back"),
        ("h", "pop_screen", "Back"),
        ("r", "refresh", "Refresh"),
        ("c", "clone", "Clone locally"),
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("tab", "toggle_panel", "Switch panel"),
        ("/", "focus_filter", "Filter"),
        ("escape", "focus_tree", "Tree"),
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
        self._tree_data: dict[str, Any] = {}
        self._file_count = 0
        self.commits: list[dict] = []
        self._version_labels: list[Static] = []

    def compose(self) -> None:
        yield Static(
            breadcrumb(f"{self.owner}/{self.repo}"),
            classes="bar-top",
        )
        filter_input = Input(
            placeholder="type to filter...",
            id="tree-filter",
            classes="panel hidden",
            disabled=True,
        )
        filter_input.border_title = "Filter"
        filter_input.border_subtitle = "esc: close"
        tree = AsciiTree("root", id="file-tree", classes="panel")
        tree.border_title = "Files"
        versions = ListView(id="version-list", classes="panel")
        versions.border_title = "Versions"
        yield Horizontal(
            Vertical(filter_input, tree, id="tree-left"),
            versions,
            id="tree-split",
        )
        yield Static(
            keybar(
                ("j/k", "move"),
                ("enter", "open"),
                ("tab", "panel"),
                ("/", "filter"),
                ("c", "clone"),
                ("q", "quit"),
            ),
            classes="bar-bottom",
        )

    def on_mount(self) -> None:
        tree = self.query_one("#file-tree", AsciiTree)
        tree.show_root = False
        self.run_worker(self._load_tree(), exclusive=True, group="tree")
        self.run_worker(self._load_versions(), exclusive=True, group="versions")

    # --- File tree (left, 2/3) ------------------------------------------

    async def _load_tree(self) -> None:
        tree = self.query_one("#file-tree", AsciiTree)
        filter_input = self.query_one("#tree-filter", Input)
        filter_input.disabled = True
        tree.clear()
        tree.border_subtitle = "loading..."
        tree.root.add("Loading tree...")
        try:
            branch = await self.github.get_default_branch(self.owner, self.repo)
            commit_sha = await self.github.get_latest_commit_sha(
                self.owner, self.repo, branch
            )
            tree_sha = await self.github.get_commit_tree_sha(
                self.owner, self.repo, commit_sha
            )
            tree_list = await self.github.get_tree(self.owner, self.repo, tree_sha)
            self._file_count = sum(
                1 for e in tree_list if e.get("type") == "blob"
            )
            self._tree_data = self._build_tree_data(tree_list)
            self._apply_filter()
            self.query_one("#file-tree", AsciiTree).focus()
        except Exception as e:
            tree.clear()
            tree.border_subtitle = "error"
            tree.root.add(f"Error: {e}")
        finally:
            filter_input.disabled = False

    def _build_tree_data(self, tree_list: list[dict]) -> dict[str, Any]:
        """Convert a flat GitHub tree into a nested dictionary."""
        files = [e for e in tree_list if e.get("type") == "blob"]
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
        return root

    def _apply_filter(self) -> None:
        tree = self.query_one("#file-tree", AsciiTree)
        filter_input = self.query_one("#tree-filter", Input)
        query = filter_input.value.lower()
        tree.clear()
        self._populate_node(tree.root, self._tree_data, query, "")
        if query:
            tree.border_subtitle = f"filtered / {self._file_count} files"
        else:
            tree.border_subtitle = f"{self._file_count} files"
        if not tree.root.children:
            tree.root.add("No matching files.")

    def _populate_node(
        self,
        node: TreeNode,
        data: dict[str, Any],
        query: str,
        prefix: str,
    ) -> bool:
        """Add directory and file nodes, returning whether anything matched."""
        has_match = False
        for name in sorted(data["dirs"]):
            sub = data["dirs"][name]
            path = f"{prefix}/{name}".lstrip("/") if prefix else name
            child = node.add(name, data={"kind": "dir", "path": path})
            sub_match = self._populate_node(child, sub, query, path)
            dir_matches = not query or query in name.lower()
            if not dir_matches and not sub_match:
                child.remove()
            else:
                has_match = True
                if query and sub_match:
                    child.expand()
        for name in sorted(data["files"]):
            if not query or query in name.lower():
                file_entry = data["files"][name]
                full_path = file_entry.get("path", "")
                node.add(
                    name,
                    data={"kind": "file", "entry": file_entry, "path": full_path},
                    allow_expand=False,
                )
                has_match = True
        return has_match

    # --- Version panel (right, 1/3) -------------------------------------

    def _version_label(self, commit: dict, selected: bool) -> Text:
        commit_data = commit.get("commit", {})
        date = commit_data.get("committer", {}).get("date", "")[:10]
        msg = commit_data.get("message", "").splitlines()[0]
        marker = ">" if selected else " "
        label = Text(no_wrap=True, overflow="crop")
        label.append(f"{marker} ", style="white")
        label.append(f"{msg} | {date}", style="white")
        if selected:
            label.stylize("reverse")
        return label

    async def _load_versions(self) -> None:
        versions = self.query_one("#version-list", ListView)
        versions.clear()
        versions.border_subtitle = "loading..."
        try:
            self.commits = await self.github.get_commits(self.owner, self.repo)
        except Exception as e:
            versions.clear()
            versions.border_subtitle = "error"
            versions.append(ListItem(Static(f"Error: {e}", markup=False)))
            return
        versions.clear()
        versions.border_subtitle = f"{len(self.commits)} commits"
        self._version_labels = []
        if not self.commits:
            versions.append(ListItem(Static("No commits.", markup=False)))
            return
        for commit in self.commits:
            label = Static(self._version_label(commit, selected=False))
            self._version_labels.append(label)
            versions.append(ListItem(label))
        versions.index = 0
        self._sync_version_selection()

    def _sync_version_selection(self) -> None:
        versions = self.query_one("#version-list", ListView)
        index = versions.index
        for i, label in enumerate(self._version_labels):
            label.update(self._version_label(self.commits[i], selected=index == i))

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.list_view.id == "version-list":
            self._sync_version_selection()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id != "version-list":
            return
        index = event.index
        if 0 <= index < len(self.commits):
            commit = self.commits[index]
            sha = commit.get("sha", "")
            commit_data = commit.get("commit", {})
            author = commit_data.get("author", {}).get("name", "")
            date = commit_data.get("committer", {}).get("date", "")[:10]
            if sha:
                self.app.push_screen(
                    DiffScreen(self.github, self.owner, self.repo, sha, author, date)
                )

    # --- Actions ---------------------------------------------------------

    def _active_panel(self):
        versions = self.query_one("#version-list", ListView)
        if versions.has_focus:
            return versions
        return self.query_one("#file-tree", AsciiTree)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "tree-filter":
            self._apply_filter()

    def action_refresh(self) -> None:
        self.run_worker(self._load_tree(), exclusive=True, group="tree")
        self.run_worker(self._load_versions(), exclusive=True, group="versions")

    def action_clone(self) -> None:
        if not self.clone_url:
            self.notify("No clone URL available for this repository.", severity="error")
            return
        self.app.push_screen(
            CloneProgressScreen(self.owner, self.repo, self.clone_url)
        )

    def action_cursor_down(self) -> None:
        self._active_panel().action_cursor_down()

    def action_cursor_up(self) -> None:
        self._active_panel().action_cursor_up()

    def action_toggle_panel(self) -> None:
        versions = self.query_one("#version-list", ListView)
        if versions.has_focus:
            self.query_one("#file-tree", AsciiTree).focus()
        else:
            versions.focus()

    def action_pop_screen(self) -> None:
        self.app.pop_screen()

    def action_focus_filter(self) -> None:
        filter_input = self.query_one("#tree-filter", Input)
        filter_input.remove_class("hidden")
        filter_input.focus()

    def action_focus_tree(self) -> None:
        filter_input = self.query_one("#tree-filter", Input)
        if not filter_input.value:
            filter_input.add_class("hidden")
        self.query_one("#file-tree", AsciiTree).focus()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        data = event.node.data or {}
        if data.get("kind") == "file":
            path = data.get("path", "")
            if path:
                self.app.push_screen(
                    CodeViewScreen(self.github, self.owner, self.repo, path)
                )
