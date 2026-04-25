"""Garmin Connect command group - FIT file import and health data sync."""

from __future__ import annotations

import typer

from openactivity.cli.garmin.import_cmd import garmin_import
from openactivity.cli.garmin.login_cmd import garmin_login
from openactivity.cli.garmin.sync_cmd import garmin_sync

app = typer.Typer(help="Garmin Connect commands (login, import activities, sync health data)")

# Register subcommands
app.command("login")(garmin_login)
app.command("import")(garmin_import)
app.command("sync")(garmin_sync)
