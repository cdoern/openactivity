"""Strava command group."""

from __future__ import annotations

import typer

from openactivity.cli.strava.activities import app as activities_app
from openactivity.cli.strava.activities import show_activity
from openactivity.cli.strava.analyze import app as analyze_app
from openactivity.cli.strava.athlete import show_athlete
from openactivity.cli.strava.auth import app as auth_app
from openactivity.cli.strava.export import app as export_app
from openactivity.cli.strava.predict import app as predict_app
from openactivity.cli.strava.records import app as records_app
from openactivity.cli.strava.segments import (
    app as segments_app,
)
from openactivity.cli.strava.segments import (
    show_segment_efforts,
    show_segment_leaderboard,
)
from openactivity.cli.strava.sync import app as sync_app

app = typer.Typer(
    name="strava",
    help="Interact with your Strava data. Run 'openactivity strava --help' for commands.",
    no_args_is_help=True,
)

app.add_typer(auth_app, name="auth")
app.add_typer(sync_app, name="sync")
app.add_typer(activities_app, name="activities")
app.add_typer(analyze_app, name="analyze")
app.add_typer(segments_app, name="segments")
app.add_typer(predict_app, name="predict")
app.add_typer(records_app, name="records")

# Register the export app under "activities export"
activities_app.add_typer(export_app, name="export")

# Top-level commands
app.command("activity")(show_activity)
app.command("athlete")(show_athlete)

# Segment subcommands as top-level for cleaner UX
segment_app = typer.Typer(name="segment", no_args_is_help=True)
segment_app.command("efforts")(show_segment_efforts)
segment_app.command("leaderboard")(show_segment_leaderboard)
app.add_typer(segment_app, name="segment")
