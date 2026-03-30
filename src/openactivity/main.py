"""Entry point for the openactivity CLI."""

from __future__ import annotations

from openactivity.cli.analyze import app as analyze_app
from openactivity.cli.config import app as config_app
from openactivity.cli.predict import app as predict_app
from openactivity.cli.records import app as records_app
from openactivity.cli.segments import segment_app, segments_app
from openactivity.cli.garmin.app import app as garmin_app
from openactivity.cli.root import app
from openactivity.cli.strava.activities import app as activities_app
from openactivity.cli.strava.activities import show_activity
from openactivity.cli.strava.app import app as strava_app

app.add_typer(strava_app, name="strava")
app.add_typer(garmin_app, name="garmin")
app.add_typer(config_app, name="config")

# Unified provider-agnostic commands at root level
app.add_typer(activities_app, name="activities")
app.add_typer(analyze_app, name="analyze")
app.add_typer(records_app, name="records")
app.add_typer(predict_app, name="predict")
app.add_typer(segments_app, name="segments")
app.add_typer(segment_app, name="segment")
app.command("activity")(show_activity)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
