"""Strava-specific predict command — thin alias over top-level predict."""

from __future__ import annotations

import typer

from openactivity.cli import predict as _predict

app = typer.Typer(
    name="predict",
    help=(
        "Predict race times (Strava data).\n\n"
        "Alias for 'openactivity predict' with --provider strava.\n"
    ),
    invoke_without_command=True,
)


@app.callback(invoke_without_command=True)
def predict_race(
    distance: str = typer.Option(..., "--distance", help='Target distance.'),
    race_date: str | None = typer.Option(None, "--race-date", help="Race date (YYYY-MM-DD)."),
    activity_type: str = typer.Option("Run", "--type", help='Activity type.'),
) -> None:
    """Predict race time (Strava only)."""
    _predict.predict_race(
        distance=distance, race_date=race_date,
        activity_type=activity_type, provider="strava",
    )
