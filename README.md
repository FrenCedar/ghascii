# ghascii

A keyboard-driven, ASCII-only terminal user interface for browsing your own
GitHub repositories and reading source code on a headless Linux console.

Built with Python, Textual, and Rich. Runs on Arch Linux without a desktop
environment.

## Features

- GitHub device-flow OAuth authentication
- List your repositories (public and private)
- Browse repository file trees via the GitHub API
- Read file contents with ANSI-colored syntax highlighting
- Clone repositories locally from the file-tree screen
- Disk cache for API responses so previously viewed data works offline
- Pure ASCII visuals + ANSI colors

## Setup

1. Create a free GitHub OAuth app at https://github.com/settings/developers.
2. Enable **Device Authorization** in the app settings.
3. Note the **Client ID**.
4. Create `~/.config/ghascii/config.json`:

```json
{
  "oauth_client_id": "YOUR_CLIENT_ID_HERE"
}
```

## Install

On Arch Linux (no desktop environment):

```bash
sudo pacman -S python python-pip git
cd ~/ghascii
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run

```bash
cd ~/ghascii
source .venv/bin/activate
ghascii
```

## Controls

- `↑/↓` or `j/k` - move selection
- `Enter` - open selected item
- `Backspace` or `h` - go back
- `/` - filter/search the current list
- `r` - refresh
- `c` - clone current repository locally (file-tree screen)
- `?` - help
- `q` - quit

## Updating on Arch

If you keep the project in a git repo, run this on the laptop after each push:

```bash
cd ~/ghascii
git pull
source .venv/bin/activate
pip install -e .
```

If you only want the latest code without a git repo, copy the project folder
(excluding `.venv`) with a USB drive or `scp -r`, then reinstall:

```bash
cd ghascii
source .venv/bin/activate
pip install -e .
```

## Tests

```bash
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```
