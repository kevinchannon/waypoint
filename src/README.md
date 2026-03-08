# waypoint (`wp`)

A small CLI utility for managing “waypoints” in your filesystem: save directories and jump back to them quickly from your shell.

Waypoints can be anonymous (index-only) or named, and are stored in a per-user file so they persist across sessions.

---

## Motivation

When working in large trees (monorepos, deep `build/` or `src/` hierarchies), `cd` + `pushd/popd` quickly become annoying:

- You often want to “bookmark” a directory and come back much later.
- You want multiple bookmarks, by index or by name.
- You want a simple, shell-friendly interface that can control `cd` in your current shell.

`wp` provides:

- `wp set [name]` to record the current directory as a waypoint.
- `wp list` to see all waypoints (with indices and names).
- `wp <index|name>` to jump back.
- Persistent storage in `~/.config/wp/waypoints.json`.

---

## Installation

### 1. Install the CLI (recommended: `pipx` or `uv tool`)

Using `pipx`:

```bash
pipx install waypoint
```

Using uv:

```bash
uv tool install waypoint
```
This installs the wp command into your user PATH.

### 2. Install per-user shell integration
Run:

```bash
wp install-shell
```
This will:

- Write a wrapper script to ~/.config/profile.d/wp.sh that defines the wp shell function (which can cd).
- Ensure your ~/.bashrc sources ~/.config/profile.d/*.sh (idempotently).
Then either start a new shell, or:

```bash
source ~/.bashrc
```
After that, wp is ready to use in Bash.

## Usage
Basic commands:
```bash
# Set a waypoint at the current directory
wp set              # anonymous waypoint (index-only)
wp set proj         # named waypoint "proj"

# List all waypoints (indices, names, directories)
wp list

# Jump to a waypoint
wp                  # jump to the last waypoint
wp 3                # jump to waypoint at index 3
wp proj             # jump to waypoint named "proj"

# Delete waypoints
wp del 2            # delete waypoint at index 2
wp del proj         # delete waypoint named "proj"

# Clear all waypoints
wp clear
```