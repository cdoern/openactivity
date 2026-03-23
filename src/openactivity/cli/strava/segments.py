"""Strava segments commands."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from openactivity.analysis.segments import (
    compute_segment_trend,
    compute_segment_trend_indicator,
)
from openactivity.cli.root import get_global_state
from openactivity.db.database import get_session, init_db
from openactivity.db.queries import get_segment_efforts, get_starred_segments
from openactivity.output.errors import exit_with_error
from openactivity.output.json import print_json
from openactivity.output.units import format_distance, format_duration

console = Console()

app = typer.Typer(
    name="segments",
    help=(
        "View segment performance.\n\n"
        "Examples:\n\n"
        "  openactivity strava segments list\n"
        "  openactivity strava segment 12345 efforts\n"
        "  openactivity strava segment 12345 trend\n"
    ),
    no_args_is_help=True,
)


@app.command("list")
def list_segments(
    activity_type: str | None = typer.Option(None, "--type", help='Filter: "Ride" or "Run".'),
    limit: int = typer.Option(20, "--limit", help="Max results."),
) -> None:
    """List starred segments from local data with trend indicators.

    Examples:
        openactivity strava segments list
        openactivity strava segments list --type Run
        openactivity strava segments list --json
    """
    state = get_global_state()
    use_json = state.get("json", False)
    units = state.get("units", "metric")

    init_db()
    session = get_session()

    try:
        segments = get_starred_segments(session, activity_type=activity_type, limit=limit)

        if not segments:
            if use_json:
                print_json([])
            else:
                console.print("No starred segments found. Run 'openactivity strava sync' to fetch.")
            return

        if use_json:
            rows = []
            for s in segments:
                indicator, rate = compute_segment_trend_indicator(session, s.id)
                rows.append({
                    "id": s.id,
                    "name": s.name,
                    "activity_type": s.activity_type,
                    "distance": s.distance,
                    "average_grade": s.average_grade,
                    "pr_time": s.pr_time,
                    "effort_count": s.effort_count,
                    "trend": indicator,
                    "trend_rate": rate,
                })
            print_json(rows)
            return

        table = Table(show_header=True, header_style="bold")
        table.add_column("ID")
        table.add_column("Name")
        table.add_column("Type")
        table.add_column("Distance", justify="right")
        table.add_column("Grade", justify="right")
        table.add_column("PR", justify="right")
        table.add_column("Efforts", justify="right")
        table.add_column("Trend", justify="center")
        table.add_column("Rate", justify="right")

        for s in segments:
            pr_str = format_duration(s.pr_time) if s.pr_time else "-"
            indicator, rate = compute_segment_trend_indicator(session, s.id)
            table.add_row(
                str(s.id),
                (s.name or "")[:30],
                s.activity_type or "",
                format_distance(s.distance, units),
                f"{s.average_grade:.1f}%",
                pr_str,
                str(s.effort_count),
                indicator,
                rate,
            )

        console.print(table)
    finally:
        session.close()


def show_segment_efforts(
    segment_id: int = typer.Argument(..., help="Strava segment ID."),
    limit: int = typer.Option(20, "--limit", help="Max results."),
) -> None:
    """View all efforts on a segment.

    Examples:
        openactivity strava segment 12345 efforts
        openactivity strava segment 12345 efforts --limit 50
        openactivity strava segment 12345 efforts --json
    """
    state = get_global_state()
    use_json = state.get("json", False)

    init_db()
    session = get_session()

    try:
        efforts = get_segment_efforts(session, segment_id, limit=limit)

        if not efforts:
            if use_json:
                print_json([])
            else:
                console.print(
                    f"No efforts found for segment {segment_id}. "
                    "Run 'openactivity strava sync' to fetch."
                )
            return

        if use_json:
            print_json(
                [
                    {
                        "id": e.id,
                        "start_date": e.start_date,
                        "elapsed_time": e.elapsed_time,
                        "moving_time": e.moving_time,
                        "pr_rank": e.pr_rank,
                        "average_heartrate": e.average_heartrate,
                        "average_watts": e.average_watts,
                    }
                    for e in efforts
                ]
            )
            return

        table = Table(
            title=f"Efforts on Segment {segment_id}",
            show_header=True,
            header_style="bold",
        )
        table.add_column("Date")
        table.add_column("Time", justify="right")
        table.add_column("Moving", justify="right")
        table.add_column("PR Rank", justify="right")
        table.add_column("HR", justify="right")

        for e in efforts:
            date_str = e.start_date.strftime("%Y-%m-%d") if e.start_date else ""
            hr_str = f"{e.average_heartrate:.0f}" if e.average_heartrate else "-"
            rank_str = f"#{e.pr_rank}" if e.pr_rank else "-"
            table.add_row(
                date_str,
                format_duration(e.elapsed_time),
                format_duration(e.moving_time),
                rank_str,
                hr_str,
            )

        console.print(table)
    finally:
        session.close()


def show_segment_leaderboard(
    segment_id: int = typer.Argument(..., help="Strava segment ID."),
    gender: str | None = typer.Option(None, "--gender", help='Filter: "M" or "F".'),
    age_group: str | None = typer.Option(None, "--age-group", help='Filter: e.g., "25_34".'),
    friends: bool = typer.Option(False, "--friends", help="Show only friends."),
    limit: int = typer.Option(10, "--limit", help="Max results."),
) -> None:
    """View segment leaderboard (requires live API call).

    Examples:
        openactivity strava segment 12345 leaderboard
        openactivity strava segment 12345 leaderboard --friends
        openactivity strava segment 12345 leaderboard --gender M --json
    """
    state = get_global_state()
    use_json = state.get("json", False)

    try:
        from openactivity.providers.strava.client import get_strava_client

        client = get_strava_client()
        leaderboard = client.get_segment_leaderboard(
            segment_id,
            gender=gender,
            age_group=age_group,
            following=friends or None,
            top_results_limit=limit,
        )
    except Exception as e:
        exit_with_error(
            "leaderboard_error",
            f"Failed to fetch leaderboard: {e}",
            "Check your authentication and try again.",
            use_json=use_json,
        )
        return

    entries = list(leaderboard)

    if use_json:
        print_json(
            [
                {
                    "rank": e.rank,
                    "athlete_name": e.athlete_name,
                    "elapsed_time": int(e.elapsed_time.total_seconds()) if e.elapsed_time else None,
                    "start_date": str(e.start_date) if e.start_date else None,
                }
                for e in entries
            ]
        )
        return

    table = Table(
        title=f"Leaderboard — Segment {segment_id}",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Rank", justify="right")
    table.add_column("Athlete")
    table.add_column("Time", justify="right")
    table.add_column("Date")

    for e in entries:
        elapsed = format_duration(int(e.elapsed_time.total_seconds())) if e.elapsed_time else "-"
        table.add_row(
            str(e.rank),
            e.athlete_name or "",
            elapsed,
            str(e.start_date)[:10] if e.start_date else "",
        )

    console.print(table)
