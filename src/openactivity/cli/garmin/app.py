"""Garmin Connect command group."""

from __future__ import annotations

import typer

from openactivity.cli.garmin.auth import garmin_auth
from openactivity.cli.garmin.sync import garmin_sync

app = typer.Typer(help="Garmin Connect commands")

# Register subcommands
app.command("auth")(garmin_auth)
app.command("sync")(garmin_sync)
