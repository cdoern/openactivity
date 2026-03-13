"""Strava command group."""

from __future__ import annotations

import typer

app = typer.Typer(
    name="strava",
    help="Interact with your Strava data. Run 'openactivity strava --help' to see available commands.",
    no_args_is_help=True,
)
