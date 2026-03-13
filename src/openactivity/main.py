"""Entry point for the openactivity CLI."""

from __future__ import annotations

from openactivity.cli.root import app
from openactivity.cli.strava.app import app as strava_app

app.add_typer(strava_app, name="strava")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
