"""Shared UI helpers for segmented screen chrome (header bars and keybars)."""

from rich.text import Text


def breadcrumb(*parts: str) -> Text:
    """Build the top header bar: breadcrumb parts without a brand block."""
    bar = Text()
    for i, part in enumerate(parts):
        if not part:
            continue
        if i:
            bar.append(" > ", style="bright_black")
        bar.append(part, style="bold white")
    return bar


def keybar(*pairs: tuple[str, str]) -> Text:
    """Build the bottom key bar: reverse-video key caps with labels."""
    bar = Text()
    for i, (key, label) in enumerate(pairs):
        if i:
            bar.append("  ")
        bar.append(f" {key} ", style="reverse")
        bar.append(f" {label}", style="white")
    return bar
