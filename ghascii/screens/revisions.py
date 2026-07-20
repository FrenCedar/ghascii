"""Revision history screen for a repository or file."""

from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Input, ListItem, ListView, Static

from ghascii.github import GitHubClient
from ghascii.screens.code_view import CodeViewScreen


class RevisionsScreen(Screen):
    """Displays recent commits for a repo or a specific file path."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("backspace", "pop_screen", "Back"),
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("/", "focus_filter", "Filter"),
        ("escape", "focus_list", "List"),
    ]

    def __init__(
        self,
        github: GitHubClient,
        owner: str,
        repo: str,
        path: str = "",
    ) -> None:
        super().__init__(id="revisions-screen")
        self.github = github
        self.owner = owner
        self.repo = repo
        self.path = path
        self.commits: list[dict] = []
        self.filtered_commits: list[dict] = []
        self._commit_labels: list[Static] = []
        self._commit_texts: list[str] = []

    def compose(self) -> None:
        label = f"{self.owner}/{self.repo}"
        if self.path:
            label = f"{label}: {self.path}"
        yield Static(
            f"[cyan]ghascii[/cyan]  |  Revisions - {label}", id="revisions-title"
        )
        yield Input(
            placeholder="Filter commits... (Esc to return)",
            id="revisions-filter",
            disabled=True,
        )
        yield ListView(id="revisions-list")
        yield Static(
            "q: quit | backspace: back | /: filter | j/k: move | enter: view",
            id="revisions-footer",
        )

    def on_mount(self) -> None:
        self.run_worker(self._load_commits(), exclusive=True)

    def _commit_text(self, commit: dict) -> str:
        sha = commit.get("sha", "")[:7]
        date = commit.get("commit", {}).get("committer", {}).get("date", "")[:10]
        msg = commit.get("commit", {}).get("message", "").splitlines()[0]
        author = commit.get("commit", {}).get("author", {}).get("name", "")
        return f"{sha}  {date}  {author:<16} {msg}"

    async def _load_commits(self) -> None:
        list_view = self.query_one("#revisions-list", ListView)
        filter_input = self.query_one("#revisions-filter", Input)
        filter_input.disabled = True
        list_view.clear()
        list_view.append(ListItem(Static("Loading commits...", markup=False)))
        try:
            self.commits = await self.github.get_commits(
                self.owner, self.repo, self.path
            )
            self._apply_filter()
            self.query_one("#revisions-list", ListView).focus()
        except Exception as e:
            list_view.clear()
            list_view.append(ListItem(Static(f"Error: {e}", markup=False)))
        finally:
            filter_input.disabled = False

    def _apply_filter(self) -> None:
        filter_input = self.query_one("#revisions-filter", Input)
        list_view = self.query_one("#revisions-list", ListView)
        query = filter_input.value.lower()
        self.filtered_commits = [
            c
            for c in self.commits
            if query in c.get("commit", {}).get("message", "").lower()
            or query in c.get("sha", "").lower()
        ]
        self._commit_labels = []
        self._commit_texts = []
        list_view.clear()
        if not self.filtered_commits:
            list_view.append(
                ListItem(Static("No matching commits.", markup=False))
            )
            return
        for commit in self.filtered_commits:
            text = self._commit_text(commit)
            label = Static(text, markup=False)
            self._commit_labels.append(label)
            self._commit_texts.append(text)
            list_view.append(ListItem(label))
        if self.filtered_commits:
            list_view.index = 0
            self._sync_selection()

    def _sync_selection(self) -> None:
        list_view = self.query_one("#revisions-list", ListView)
        index = list_view.index
        for i, label in enumerate(self._commit_labels):
            original = self._commit_texts[i]
            if index == i:
                label.update(f"> {original}")
            else:
                label.update(original)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        self._sync_selection()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "revisions-filter":
            self._apply_filter()

    def action_cursor_down(self) -> None:
        self.query_one("#revisions-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#revisions-list", ListView).action_cursor_up()

    def action_focus_filter(self) -> None:
        self.query_one("#revisions-filter", Input).focus()

    def action_focus_list(self) -> None:
        self.query_one("#revisions-list", ListView).focus()

    def action_pop_screen(self) -> None:
        self.app.pop_screen()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        index = event.index
        if 0 <= index < len(self.filtered_commits):
            commit = self.filtered_commits[index]
            sha = commit.get("sha", "")
            self.app.push_screen(
                CodeViewScreen(
                    self.github,
                    self.owner,
                    self.repo,
                    self.path,
                    ref=sha,
                )
            )
