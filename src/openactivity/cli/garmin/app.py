"""Garmin Connect command group - FIT file import."""

from __future__ import annotations

import typer

from openactivity.cli.garmin.import_cmd import garmin_import

app = typer.Typer(help="Garmin Connect commands (FIT file import)")

# Register subcommands
app.command("import")(garmin_import)
