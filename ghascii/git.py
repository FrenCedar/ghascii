"""Local git clone/update helpers for ghascii."""

import subprocess
import sys
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


def update_ghascii(root: Path) -> str:
    """Pull the latest ghascii source and reinstall it in the current environment."""
    if not (root / ".git").is_dir():
        raise GitError(f"{root} is not a git repository")
    pull = subprocess.run(
        ["git", "-C", str(root), "pull", "--ff-only"],
        capture_output=True,
        text=True,
        check=False,
    )
    if pull.returncode != 0:
        raise GitError(pull.stderr.strip() or "git pull failed")
    install = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", "."],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if install.returncode != 0:
        raise GitError(install.stderr.strip() or "pip install failed")
    stdout = (pull.stdout.strip() + "\n" + install.stdout.strip()).strip()
    return stdout or "Done"
