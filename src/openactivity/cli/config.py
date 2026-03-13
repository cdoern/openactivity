"""Persistent configuration management commands."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from openactivity.cli.root import get_global_state
from openactivity.config.config import load_config, save_config
from openactivity.output.json import print_json

console = Console()

app = typer.Typer(
    name="config",
    help=(
        "View and update persistent configuration.\n\n"
        "Examples:\n\n"
        "  openactivity config list\n"
        "  openactivity config get units.system\n"
        "  openactivity config set units.system imperial\n"
    ),
    no_args_is_help=True,
)


def _get_nested(d: dict, key: str) -> str | None:
    """Get a value from a nested dict using dot notation."""
    parts = key.split(".")
    current = d
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return str(current) if current is not None else None


def _set_nested(d: dict, key: str, value: str) -> None:
    """Set a value in a nested dict using dot notation."""
    parts = key.split(".")
    current = d
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]

    # Try to preserve types
    final_key = parts[-1]
    existing = current.get(final_key)
    if isinstance(existing, bool):
        current[final_key] = value.lower() in ("true", "1", "yes")
    elif isinstance(existing, int):
        try:
            current[final_key] = int(value)
        except ValueError:
            current[final_key] = value
    else:
        current[final_key] = value


def _flatten(d: dict, prefix: str = "") -> list[tuple[str, str]]:
    """Flatten a nested dict into dot-notation key-value pairs."""
    items = []
    for k, v in d.items():
        key = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
        if isinstance(v, dict):
            items.extend(_flatten(v, key))
        else:
            items.append((key, str(v)))
    return items


@app.command("list")
def config_list() -> None:
    """Show all configuration values.

    Examples:
        openactivity config list
        openactivity config list --json
    """
    state = get_global_state()
    use_json = state.get("json", False)
    config_path = state.get("config_path")

    cfg = load_config(config_path)

    if use_json:
        print_json(cfg)
        return

    items = _flatten(cfg)
    if not items:
        console.print("No configuration values set.")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Key")
    table.add_column("Value")

    for key, value in items:
        table.add_row(key, value)

    console.print(table)
    console.print(f"\n[dim]Config file: {config_path}[/dim]")


@app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Config key (dot notation, e.g., units.system)."),
) -> None:
    """Get a configuration value.

    Examples:
        openactivity config get units.system
        openactivity config get sync.detail
    """
    state = get_global_state()
    use_json = state.get("json", False)
    config_path = state.get("config_path")

    cfg = load_config(config_path)
    value = _get_nested(cfg, key)

    if value is None:
        if use_json:
            print_json({"key": key, "value": None})
        else:
            console.print(f"Key '{key}' not found.")
        return

    if use_json:
        print_json({"key": key, "value": value})
    else:
        console.print(value)


@app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Config key (dot notation)."),
    value: str = typer.Argument(..., help="Value to set."),
) -> None:
    """Set a configuration value persistently.

    Examples:
        openactivity config set units.system imperial
        openactivity config set units.system metric
        openactivity config set sync.detail false
    """
    state = get_global_state()
    use_json = state.get("json", False)
    config_path = state.get("config_path")

    cfg = load_config(config_path)
    _set_nested(cfg, key, value)
    save_config(cfg, config_path)

    if use_json:
        print_json({"key": key, "value": value, "status": "saved"})
    else:
        console.print(f"[green]✓[/green] Set {key} = {value}")
        console.print(f"  [dim]Saved to {config_path}[/dim]")
