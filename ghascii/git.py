"""Local git clone/update helpers for ghascii."""

import os
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


def _git_remote_url(path: Path) -> str | None:
    """Return the origin URL for a local git clone, if any."""
    result = subprocess.run(
        ["git", "-C", str(path), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _writable_copy(root: Path) -> Path:
    """Return a user-writable path containing the ghascii source.

    If the supplied root is writable, use it; otherwise clone into the
    user cache directory so updates do not fail on permission errors.
    """
    if (root / ".git").is_dir() and os.access(root, os.W_OK):
        return root
    cache = Path.home() / ".cache" / "ghascii" / "self-update"
    target = cache / "ghascii"
    target.parent.mkdir(parents=True, exist_ok=True)
    remote = _git_remote_url(root) or "https://github.com/FrenCedar/ghascii.git"
    if not (target / ".git").is_dir():
        result = subprocess.run(
            ["git", "clone", remote, str(target)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise GitError(result.stderr.strip() or "git clone failed")
    return target


def update_ghascii(root: Path) -> str:
    """Pull the latest ghascii source and reinstall it in the current environment."""
    workdir = _writable_copy(root)
    pull = subprocess.run(
        ["git", "-C", str(workdir), "pull", "--ff-only"],
        capture_output=True,
        text=True,
        check=False,
    )
    if pull.returncode != 0:
        raise GitError(pull.stderr.strip() or "git pull failed")
    install = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", "."],
        cwd=str(workdir),
        capture_output=True,
        text=True,
        check=False,
    )
    if install.returncode != 0:
        raise GitError(install.stderr.strip() or "pip install failed")
    stdout = (pull.stdout.strip() + "\n" + install.stdout.strip()).strip()
    return stdout or "Done"
