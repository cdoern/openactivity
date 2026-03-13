"""Root Typer app with global options."""

from __future__ import annotations

from typing import Optional

import typer

from openactivity.config.config import get_config_path, load_config

app = typer.Typer(
    name="openactivity",
    help="CLI tool for pulling, analyzing, and exporting fitness activity data.",
    no_args_is_help=True,
)

# Global state shared across commands
_global_state: dict = {}


def get_global_state() -> dict:
    """Get the global CLI state (json mode, unit system, config)."""
    return _global_state


@app.callback()
def main(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON to stdout."),
    units: Optional[str] = typer.Option(
        None, "--units", help='Unit system: "metric" or "imperial".'
    ),
    config: Optional[str] = typer.Option(
        None, "--config", help="Path to config file override."
    ),
) -> None:
    """OpenActivity — fitness data at your fingertips."""
    config_path = get_config_path(config)
    cfg = load_config(config_path)
    unit_system = units or cfg.get("units", {}).get("system", "metric")

    _global_state["json"] = json_output
    _global_state["units"] = unit_system
    _global_state["config"] = cfg
    _global_state["config_path"] = config_path
