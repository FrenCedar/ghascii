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


def _fallback_copy(root: Path) -> Path:
    """Clone ghascii into a user-owned cache directory for updates."""
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


def _git_pull_error(stderr: str) -> bool:
    """Return True if stderr indicates a permission/ownership git error."""
    lowered = stderr.lower()
    return any(
        phrase in lowered
        for phrase in (
            "permission",
            "adding an object",
            "detected dubious",
            "safe.directory",
            "not a git repository",
        )
    )


def _pip_install(workdir: Path) -> subprocess.CompletedProcess[str]:
    """Install the package in editable mode, falling back to --user on permission errors."""
    base_cmd = [sys.executable, "-m", "pip", "install", "-e", "."]
    install = subprocess.run(
        base_cmd,
        cwd=str(workdir),
        capture_output=True,
        text=True,
        check=False,
    )
    if install.returncode != 0 and "Permission" in install.stderr:
        install = subprocess.run(
            [*base_cmd, "--user"],
            cwd=str(workdir),
            capture_output=True,
            text=True,
            check=False,
        )
    return install


def update_ghascii(root: Path) -> str:
    """Pull the latest ghascii source and reinstall it in the current environment."""
    workdir = root
    pull = subprocess.run(
        ["git", "-C", str(workdir), "pull", "--ff-only"],
        capture_output=True,
        text=True,
        check=False,
    )
    if pull.returncode != 0 and _git_pull_error(pull.stderr):
        workdir = _fallback_copy(root)
        pull = subprocess.run(
            ["git", "-C", str(workdir), "pull", "--ff-only"],
            capture_output=True,
            text=True,
            check=False,
        )
    if pull.returncode != 0:
        raise GitError(pull.stderr.strip() or "git pull failed")
    install = _pip_install(workdir)
    if install.returncode != 0:
        raise GitError(install.stderr.strip() or "pip install failed")
    stdout = (pull.stdout.strip() + "\n" + install.stdout.strip()).strip()
    return stdout or "Done"
