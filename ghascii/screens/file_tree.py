"""Repository file-tree browser screen."""

from typing import Any

from rich.text import Text
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Input, Static, Tree
from textual.widgets.tree import TreeNode

from ghascii.github import GitHubClient
from ghascii.screens.clone_progress import CloneProgressScreen
from ghascii.screens.code_view import CodeViewScreen


class AsciiTree(Tree):
    """Tree widget that uses ASCII-only guide lines and icons."""

    ICON_NODE = "+ "
    ICON_NODE_EXPANDED = "- "
    LINES = {
        "default": ("  ", "| ", "`-", "|-"),
        "bold": ("  ", "| ", "`-", "|-"),
        "double": ("  ", "| ", "`-", "|-"),
    }

    def render_label(
        self, node: TreeNode[Any], base_style, style
    ) -> Text:
        node_label = node._label.copy()
        node_label.stylize(style)
        if node._allow_expand:
            prefix = (
                self.ICON_NODE_EXPANDED if node.is_expanded else self.ICON_NODE,
                base_style,
            )
        else:
            prefix = ("", base_style)
        if node == self.cursor_node:
            text = Text.assemble(prefix, ("> ", style), node_label)
        else:
            text = Text.assemble(prefix, node_label)
        return text


class FileTreeScreen(Screen):
    """Displays a recursive, toggleable file tree for a single repository."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("backspace", "pop_screen", "Back"),
        ("r", "refresh", "Refresh"),
        ("c", "clone", "Clone locally"),
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
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

    def compose(self) -> None:
        yield Static(
            f"[cyan]ghascii[/cyan]  |  {self.owner}/{self.repo}", id="tree-title"
        )
        yield Input(
            placeholder="Filter files... (Esc to return)",
            id="tree-filter",
            disabled=True,
        )
        yield AsciiTree("root", id="file-tree")
        yield Static(
            "q: quit | backspace: back | /: filter | j/k: move | enter: open | c: clone",
            id="tree-footer",
        )

    def on_mount(self) -> None:
        tree = self.query_one("#file-tree", AsciiTree)
        tree.show_root = False
        self.run_worker(self._load_tree(), exclusive=True)

    async def _load_tree(self) -> None:
        tree = self.query_one("#file-tree", AsciiTree)
        filter_input = self.query_one("#tree-filter", Input)
        filter_input.disabled = True
        tree.clear()
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
            self._tree_data = self._build_tree_data(tree_list)
            self._apply_filter()
            self.query_one("#file-tree", AsciiTree).focus()
        except Exception as e:
            tree.clear()
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
            child = node.add(f"[D] {name}", data={"kind": "dir", "path": path})
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
                    f"[F] {name}",
                    data={"kind": "file", "entry": file_entry, "path": full_path},
                )
                has_match = True
        return has_match

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
        self.query_one("#file-tree", AsciiTree).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#file-tree", AsciiTree).action_cursor_up()

    def action_pop_screen(self) -> None:
        self.app.pop_screen()

    def action_focus_filter(self) -> None:
        self.query_one("#tree-filter", Input).focus()

    def action_focus_tree(self) -> None:
        self.query_one("#file-tree", AsciiTree).focus()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        data = event.node.data or {}
        if data.get("kind") == "file":
            path = data.get("path", "")
            if path:
                self.app.push_screen(
                    CodeViewScreen(self.github, self.owner, self.repo, path)
                )
