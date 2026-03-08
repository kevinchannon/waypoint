# waypoint – Developer Guide

This document is for contributors / maintainers of `waypoint` (`wp`).

---

## Project layout

```text
pyproject.toml
uv.lock
src/
  waypoint/
    __init__.py
    cli.py
scripts/
  waypoint.sh           # (optional) prototype shell wrapper
test/
  test_wp_core.py
  test_install_shell.py
```
- src layout package: waypoint lives under src/waypoint.
- CLI entry point: wp → waypoint.cli:app (Typer app).
- Dependency / env management: uv.

## Setup (dev environment)
Install dependencies (runtime + dev):

```bash
uv sync --extra dev
```
This will:

1. Create / update the project environment.
2. Install waypoint in editable mode.
3. Install dev deps (e.g. pytest, parameterized).

You can then run commands in the env via:

```bash
uv run <command> ...
```
## Running tests
From the project root:

```bash
uv run pytest
```
You can also target a specific test file:

```bash
uv run pytest test/test_wp_core.py
```
## Building distributions
Build wheel + sdist
```bash
uv build
```
Artifacts will be written to dist/, e.g.:

```
dist/waypoint-<version>-py3-none-any.whl
dist/waypoint-<version>.tar.gz
```
(uv uses the build backend configured in pyproject.toml, e.g. uv_build.)

## Local installation / manual testing
Install into the current uv-managed environment:

```bash
uv sync --no-default-groups --no-dev
```
Or install the built wheel into some other venv:

```bash
python -m venv .venv
source .venv/bin/activate
pip install dist/waypoint-<version>-py3-none-any.whl
```
Then:

```bash
wp --help
````

## Shell integration (for dev testing)
During development, you can use the same shell hook as users:

```bash
uv run wp install-shell
source ~/.bashrc
```
Now changes to waypoint/cli.py are picked up immediately (editable install via uv sync).