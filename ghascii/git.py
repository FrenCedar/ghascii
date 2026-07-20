"""Local git clone/update helpers for ghascii."""

import subprocess
from pathlib import Path


class GitError(Exception):
    """Raised when a git subprocess command fails."""


def clone_or_update(owner: str, repo: str, clone_url: str, dest: Path) -> str:
    """Clone a repository into dest/owner/repo or pull if it already exists."""
    target = dest / owner / repo
    if (target / ".git").is_dir():
        result = subprocess.run(
            ["git", "-C", str(target), "pull", "--ff-only"],
            capture_output=True,
            text=True,
            check=False,
        )
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "clone", clone_url, str(target)],
            capture_output=True,
            text=True,
            check=False,
        )
    if result.returncode != 0:
        raise GitError(result.stderr.strip() or "git command failed")
    return result.stdout.strip() or "Done"
