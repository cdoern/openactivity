"""Strava-specific records commands — thin alias over top-level records.

All commands delegate to the unified ``openactivity records`` commands
with ``--provider strava`` applied implicitly where applicable.
"""

from __future__ import annotations

import typer

from openactivity.cli import records as _records

app = typer.Typer(
    name="records",
    help=(
        "Personal records — Strava data.\n\n"
        "Aliases for 'openactivity records' with --provider strava.\n\n"
        "Examples:\n\n"
        "  openactivity strava records scan\n"
        "  openactivity strava records list\n"
    ),
    no_args_is_help=True,
)


@app.command("scan")
def scan_records(
    full: bool = typer.Option(False, "--full", help="Re-scan all activities."),
) -> None:
    """Scan Strava activities for personal records."""
    _records.scan_records(full=full, provider="strava")


@app.command("list")
def list_records(
    record_type: str | None = typer.Option(None, "--type", help='Filter by "running" or "cycling".'),
) -> None:
    """Show current personal records."""
    _records.list_records(record_type=record_type)


@app.command("history")
def show_history(
    distance: str = typer.Option(..., "--distance", help="Distance label."),
) -> None:
    """Show PR progression for a distance."""
    _records.show_history(distance=distance)


@app.command("add-distance")
def add_distance(
    label: str = typer.Argument(help='Distance label.'),
    meters: float = typer.Option(None, "--meters", "-m", help="Distance in meters."),
    miles: float = typer.Option(None, "--miles", "-mi", help="Distance in miles."),
    km: float = typer.Option(None, "--km", "-k", help="Distance in kilometers."),
) -> None:
    """Add a custom distance for PR tracking."""
    _records.add_distance(label=label, meters=meters, miles=miles, km=km)


@app.command("remove-distance")
def remove_distance(
    label: str = typer.Argument(help="Distance label to remove."),
) -> None:
    """Remove a custom distance and its records."""
    _records.remove_distance(label=label)
