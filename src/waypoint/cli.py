from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Union
import json
import os
import re
import sys

import typer
from rich.console import Console
from rich.table import Table

from waypoint import __version__

app = typer.Typer(help="Directory waypoint manager", no_args_is_help=True)
console = Console()

NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")

PROFILE_D_DIR_DEFAULT = Path.home() / ".config" / "profile.d"
BASHRC_PATH_DEFAULT = Path.home() / ".bashrc"

PROFILE_BLOCK_MARKER = "# BEGIN wp profile.d integration"
PROFILE_BLOCK = """\
# BEGIN wp profile.d integration
if [ -d "$HOME/.config/profile.d" ]; then
    for file in "$HOME"/.config/profile.d/*.sh; do
        [ -r "$file" ] && . "$file"
    done
fi
# END wp profile.d integration
"""

WP_WRAPPER_SCRIPT = """\
# wp shell integration
_wp_raw() {
    if [[ $# -eq 0 ]]; then
        command wp
    else
        command wp "$@"
    fi
}

wp() {
    local subcommand
    subcommand="$1"
    shift || true

    case "$subcommand" in
        return)
            # cd to a waypoint
            local target_dir
            target_dir="$(_wp_raw get "$@")" || return

            if [[ -d "$target_dir" ]]; then
                cd "$target_dir" || return
            else
                echo "Target directory does not exist: $target_dir" >&2
                return 1
            fi
            ;;
        *)
            # Not "return", pass-through anything else for wp to handle
            if [[ -n "$subcommand" ]]; then
                _wp_raw "$subcommand" "$@"
            else
                _wp_raw
            fi
            ;;
    esac
}
"""


def write_wp_wrapper(profile_dir: Path) -> Path:
    profile_dir.mkdir(parents=True, exist_ok=True)
    target = profile_dir / "wp.sh"
    target.write_text(WP_WRAPPER_SCRIPT, encoding="utf-8")
    return target


def ensure_bashrc_profile_block(bashrc_path: Path) -> bool:
    """
    Ensure that bashrc_path contains the profile.d sourcing block.

    Returns True if we had to modify the file, False if it was already present.
    """
    if bashrc_path.exists():
        content = bashrc_path.read_text(encoding="utf-8")
    else:
        content = ""

    if PROFILE_BLOCK_MARKER in content:
        return False

    if content and not content.endswith("\n"):
        content += "\n"

    content += PROFILE_BLOCK + "\n"
    bashrc_path.write_text(content, encoding="utf-8")
    return True

@dataclass
class Waypoint:
    name: Optional[str]
    directory: str


def get_db_path() -> Path:
    env_path = os.getenv("WP_DB")
    if env_path:
        return Path(env_path).expanduser()

    return Path.home() / ".config" / "wp" / "waypoints.json"


def load_waypoints(db_path: Path) -> List[Waypoint]:
    if not db_path.exists():
        return []

    with db_path.open("r", encoding="utf-8") as file:
        raw = json.load(file)

    return [Waypoint(**entry) for entry in raw]


def save_waypoints(db_path: Path, waypoints: List[Waypoint]) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    data = [asdict(wp) for wp in waypoints]

    with db_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def validate_name(name: str) -> None:
    if not NAME_RE.match(name):
        raise ValueError(
            "Invalid name. Must be alphanumeric/underscore/dash and not start with a digit."
        )


def ensure_unique_name(waypoints: List[Waypoint], name: str) -> None:
    if any(wp.name == name for wp in waypoints):
        raise ValueError(f"Waypoint name '{name}' already exists.")


def add_waypoint(
    db_path: Path,
    directory: Path,
    name: Optional[str],
) -> Waypoint:
    waypoints = load_waypoints(db_path)

    if name is not None:
        validate_name(name)
        ensure_unique_name(waypoints, name)

    waypoint = Waypoint(name=name, directory=str(directory))
    waypoints.append(waypoint)

    save_waypoints(db_path, waypoints)
    return waypoint


Selector = Union[int, str, None]


def _selector_to_index(waypoints: List[Waypoint], selector: Selector) -> int:
    """
    Returns a 0-based index into waypoints for the given selector.

    selector:
    - None        -> last waypoint
    - int         -> 1-based index
    - str (digits)-> parsed as int index
    - str (other) -> name
    """
    if not waypoints:
        raise IndexError("No waypoints defined.")

    if selector is None:
        return len(waypoints) - 1

    if isinstance(selector, int):
        if selector < 1 or selector > len(waypoints):
            raise IndexError(f"Index {selector} out of range.")
        return selector - 1

    # str selector
    if selector.isdigit():
        idx = int(selector)
        if idx < 1 or idx > len(waypoints):
            raise IndexError(f"Index {idx} out of range.")
        return idx - 1

    # name selector
    for index, waypoint in enumerate(waypoints):
        if waypoint.name == selector:
            return index

    raise KeyError(f"No waypoint named '{selector}'.")


def get_waypoint(db_path: Path, selector: Selector) -> Waypoint:
    waypoints = load_waypoints(db_path)
    index = _selector_to_index(waypoints, selector)
    return waypoints[index]


def delete_waypoint(db_path: Path, selector: Selector) -> Waypoint:
    waypoints = load_waypoints(db_path)
    index = _selector_to_index(waypoints, selector)
    waypoint = waypoints.pop(index)
    save_waypoints(db_path, waypoints)
    return waypoint
    
    
def rename_waypoint(db_path: Path, old_selector: Selector, new_name: str) -> Waypoint:
    validate_name(new_name)
    waypoints = load_waypoints(db_path)
    ensure_unique_name(waypoints, new_name)
    index = _selector_to_index(waypoints, old_selector)
    waypoint = waypoints[index]
    waypoint.name = new_name
    save_waypoints(db_path, waypoints)
    return waypoint


def _version_callback(value: bool):
    if value:
        console.print(f"waypoint version {__version__}")
        raise typer.Exit()

@app.command("set")
def cmd_set(
    name: Optional[str] = typer.Argument(
        None,
        help="Optional name for the waypoint (must not start with a digit).",
    )
) -> None:
    """
    Set a waypoint at the current directory.

    Example:
    - wp set
    - wp set proj
    """
    db_path = get_db_path()
    current_dir = Path.cwd()

    try:
        waypoint = add_waypoint(db_path, current_dir, name)
    except ValueError as error:
        typer.secho(str(error), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if waypoint.name:
        console.print(
            f"[green]Set waypoint[/green] {waypoint.name!r} -> {waypoint.directory}"
        )
    else:
        console.print(f"[green]Set anonymous waypoint[/green] -> {waypoint.directory}")


@app.command("get")
def cmd_get(
    target: Optional[str] = typer.Argument(
        None,
        help="Index or name of waypoint. Omit to use the last waypoint.",
    )
) -> None:
    """
    Print the directory for a waypoint.

    Intended usage in shell:
      cd \"$(wp get <index|name>)\"
    """
    db_path = get_db_path()

    selector: Selector = target
    try:
        waypoint = get_waypoint(db_path, selector)
    except (IndexError, KeyError) as error:
        typer.secho(str(error), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # IMPORTANT: Only print the directory, nothing else, to stdout.
    sys.stdout.write(waypoint.directory)
    sys.stdout.flush()
    
@app.command("rename")
def cmd_rename(
    target: str = typer.Argument(
        None,
        help="Index or name of waypoint to rename.",
    ),
    new_name: str = typer.Argument(
        None,
        help="New name for the waypoint"
    )
) -> None:
    """
    Rename a waypoint.
    """
    db_path = get_db_path()

    selector: Selector = target
    try:
        rename_waypoint(db_path, selector, new_name)
    except (IndexError, KeyError) as error:
        typer.secho(str(error), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command("list")
def cmd_list() -> None:
    """
    List all waypoints as a table.
    """
    db_path = get_db_path()
    waypoints = load_waypoints(db_path)
    if not waypoints:
        console.print("[yellow]No waypoints defined.[/yellow]")
        return

    table = Table(
        title=None,
        show_header=True,
        header_style="bold",
        show_edge=False,
        show_lines=False,
        box=None,
    )

    table.add_column("Index", justify="right")
    table.add_column("Name", justify="left")
    table.add_column("Directory", justify="left")

    for index, waypoint in enumerate(waypoints, start=1):
        table.add_row(str(index), waypoint.name or "", waypoint.directory)

    console.print(table)


@app.command("del")
def cmd_del(
    target: str = typer.Argument(
        ...,
        help="Index or name of waypoint to delete.",
    )
) -> None:
    """
    Delete a waypoint by index or name.
    """
    db_path = get_db_path()

    selector: Selector = target
    try:
        waypoint = delete_waypoint(db_path, selector)
    except (IndexError, KeyError) as error:
        typer.secho(str(error), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if waypoint.name:
        console.print(
            f"[green]Deleted waypoint[/green] {waypoint.name!r} -> {waypoint.directory}"
        )
    else:
        console.print(
            f"[green]Deleted anonymous waypoint[/green] -> {waypoint.directory}"
        )


@app.command("clear")
def cmd_clear() -> None:
    """
    Clear all waypoints.
    """
    db_path = get_db_path()
    save_waypoints(db_path, [])
    console.print("[green]Cleared all waypoints.[/green]")


@app.command("install-shell")
def cmd_install_shell() -> None:
    """
    Install per-user shell integration:

    - Writes ~/.config/profile.d/wp.sh (wrapper function)
    - Ensures ~/.bashrc sources ~/.config/profile.d/*.sh

    Run this once after `pipx install wp`, and again after upgrades if needed.
    """
    profile_dir = PROFILE_D_DIR_DEFAULT
    bashrc_path = BASHRC_PATH_DEFAULT

    wp_script = write_wp_wrapper(profile_dir)
    updated_bashrc = ensure_bashrc_profile_block(bashrc_path)

    console.print(f"[green]Installed wp shell wrapper:[/green] {wp_script}")

    if updated_bashrc:
        console.print(
            f"[green]Updated[/green] {bashrc_path} to source ~/.config/profile.d/*.sh"
        )
    else:
        console.print(
            f"{bashrc_path} already configured to source ~/.config/profile.d/*.sh"
        )

    console.print(
        "Restart your shell or run: [bold]source ~/.bashrc[/bold] to activate `wp`."
    )


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit",
    )):
    pass


if __name__ == "__main__":
    app()