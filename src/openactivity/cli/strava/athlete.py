"""Strava athlete profile command."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from openactivity.cli.root import get_global_state
from openactivity.db.database import get_session, init_db
from openactivity.db.queries import get_athlete, get_athlete_stats
from openactivity.output.errors import exit_with_error
from openactivity.output.json import print_json
from openactivity.output.units import format_distance, format_duration

console = Console()


def show_athlete() -> None:
    """Show authenticated user's profile and cumulative stats.

    Displays year-to-date and all-time totals for runs, rides, and swims
    from local data.

    Examples:
        openactivity strava athlete
        openactivity strava athlete --json
    """
    state = get_global_state()
    use_json = state.get("json", False)
    units = state.get("units", "metric")

    init_db()
    session = get_session()

    try:
        athlete = get_athlete(session)
        if not athlete:
            exit_with_error(
                "no_data",
                "No athlete data found.",
                "Run 'openactivity strava sync' to fetch your profile.",
                use_json=use_json,
            )

        stats = get_athlete_stats(session, athlete.id)

        if use_json:
            data = {
                "id": athlete.id,
                "name": f"{athlete.firstname or ''} {athlete.lastname or ''}".strip(),
                "city": athlete.city,
                "state": athlete.state,
                "country": athlete.country,
                "stats": [
                    {
                        "stat_type": s.stat_type,
                        "activity_type": s.activity_type,
                        "count": s.count,
                        "distance": s.distance,
                        "moving_time": s.moving_time,
                        "elevation_gain": s.elevation_gain,
                    }
                    for s in stats
                ],
            }
            print_json(data)
            return

        name = f"{athlete.firstname or ''} {athlete.lastname or ''}".strip()
        location_parts = [p for p in [athlete.city, athlete.state, athlete.country] if p]
        location = ", ".join(location_parts)

        console.print(f"\n[bold]{name}[/bold]")
        if location:
            console.print(f"  Location: {location}")

        # Build stats tables by stat_type
        ytd = {s.activity_type: s for s in stats if s.stat_type == "ytd"}
        all_time = {s.activity_type: s for s in stats if s.stat_type == "all_time"}

        if not ytd and not all_time:
            console.print(
                "\n[dim]No stats available. Run 'openactivity strava sync' to fetch.[/dim]"
            )
            return

        table = Table(show_header=True, header_style="bold")
        table.add_column("Type")
        table.add_column("YTD Count", justify="right")
        table.add_column("YTD Distance", justify="right")
        table.add_column("YTD Time", justify="right")
        table.add_column("All Count", justify="right")
        table.add_column("All Distance", justify="right")
        table.add_column("All Time", justify="right")

        for atype in ["run", "ride", "swim"]:
            y = ytd.get(atype)
            a = all_time.get(atype)
            if not y and not a:
                continue
            table.add_row(
                atype.title(),
                str(y.count) if y else "-",
                format_distance(y.distance, units) if y else "-",
                format_duration(y.moving_time) if y else "-",
                str(a.count) if a else "-",
                format_distance(a.distance, units) if a else "-",
                format_duration(a.moving_time) if a else "-",
            )

        console.print()
        console.print(table)
    finally:
        session.close()
