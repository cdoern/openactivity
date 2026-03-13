"""Strava bulk export command."""

from __future__ import annotations

import typer
from rich.console import Console

from openactivity.cli.root import get_global_state
from openactivity.db.database import get_session, init_db
from openactivity.db.queries import get_activities
from openactivity.output.errors import exit_with_error
from openactivity.output.json import print_json

console = Console()

app = typer.Typer(name="export")


@app.callback(invoke_without_command=True)
def export_activities(
    ctx: typer.Context,
    fmt: str = typer.Option("csv", "--format", help='Export format: "csv" or "json".'),
    output: str = typer.Option(..., "--output", help="Output file path."),
    after: str | None = typer.Option(None, "--after", help="Filter: after date (YYYY-MM-DD)."),
    before: str | None = typer.Option(None, "--before", help="Filter: before date (YYYY-MM-DD)."),
    activity_type: str | None = typer.Option(None, "--type", help="Filter by activity type."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing file."),
) -> None:
    """Bulk export activities to CSV or JSON.

    Examples:
        openactivity strava activities export --format csv --output activities.csv
        openactivity strava activities export --format json --output data.json --type Run
        openactivity strava activities export --format csv --output all.csv --force
    """
    if ctx.invoked_subcommand is not None:
        return

    state = get_global_state()
    use_json = state.get("json", False)

    init_db()
    session = get_session()

    try:
        from datetime import datetime

        after_dt = datetime.fromisoformat(after) if after else None
        before_dt = datetime.fromisoformat(before) if before else None

        activities = get_activities(
            session,
            activity_type=activity_type,
            after=after_dt,
            before=before_dt,
            limit=100000,
            offset=0,
        )

        if not activities:
            if use_json:
                print_json({"status": "empty", "message": "No activities found."})
            else:
                console.print("No activities found matching your filters.")
            return

        from openactivity.export.file_utils import write_file

        if fmt == "csv":
            from openactivity.export.csv import activities_to_csv

            content = activities_to_csv(activities)
            write_file(output, content, force=force)
        elif fmt == "json":
            import json

            data = [
                {
                    "id": a.id,
                    "name": a.name,
                    "type": a.type,
                    "start_date": a.start_date.isoformat() if a.start_date else None,
                    "distance": a.distance,
                    "moving_time": a.moving_time,
                    "elapsed_time": a.elapsed_time,
                    "total_elevation_gain": a.total_elevation_gain,
                    "average_speed": a.average_speed,
                    "average_heartrate": a.average_heartrate,
                    "average_watts": a.average_watts,
                    "calories": a.calories,
                }
                for a in activities
            ]
            write_file(output, json.dumps(data, indent=2), force=force)
        else:
            exit_with_error(
                "invalid_format",
                f"Unsupported export format: '{fmt}'.",
                "Use --format csv or --format json.",
                use_json=use_json,
            )

        if use_json:
            print_json(
                {
                    "status": "exported",
                    "count": len(activities),
                    "format": fmt,
                    "output": output,
                }
            )
        else:
            console.print(f"[green]✓[/green] Exported {len(activities)} activities to {output}")
    finally:
        session.close()
