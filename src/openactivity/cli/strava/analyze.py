"""Strava analyze commands for performance trends."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from openactivity.cli.root import get_global_state
from openactivity.db.database import get_session, init_db
from openactivity.output.json import print_json
from openactivity.output.units import (
    format_distance,
    format_duration,
    format_elevation,
)

console = Console()

app = typer.Typer(
    name="analyze",
    help=(
        "Analyze performance trends from local data.\n\n"
        "Examples:\n\n"
        "  openactivity strava analyze summary\n"
        "  openactivity strava analyze pace --last 90d\n"
        "  openactivity strava analyze zones --zone-type heartrate\n"
        "  openactivity strava analyze power-curve\n"
    ),
    no_args_is_help=True,
)


@app.command("summary")
def analyze_summary(
    period: str = typer.Option(
        "weekly",
        "--period",
        help='Aggregation period: "daily", "weekly", "monthly".',
    ),
    last: str = typer.Option("90d", "--last", help='Time window (e.g., "30d", "6m", "1y").'),
    activity_type: str | None = typer.Option(
        None, "--type", help='Filter by activity type (e.g., "Run").'
    ),
) -> None:
    """Training volume summary over time.

    Shows distance, duration, elevation, and activity count aggregated
    by the chosen period.

    Examples:
        openactivity strava analyze summary
        openactivity strava analyze summary --period monthly --last 1y
        openactivity strava analyze summary --type Run --json
    """
    state = get_global_state()
    use_json = state.get("json", False)
    units = state.get("units", "metric")

    init_db()
    session = get_session()

    try:
        from openactivity.analysis.summary import compute_summary

        data = compute_summary(
            session,
            period=period,
            last=last,
            activity_type=activity_type,
        )

        if not data:
            if use_json:
                print_json([])
            else:
                console.print("No activities found in the specified time window.")
            return

        if use_json:
            print_json(data)
            return

        table = Table(
            title=f"Training Summary ({period}, last {last})",
            show_header=True,
            header_style="bold",
        )
        table.add_column("Period")
        table.add_column("Count", justify="right")
        table.add_column("Distance", justify="right")
        table.add_column("Time", justify="right")
        table.add_column("Elevation", justify="right")

        for row in data:
            table.add_row(
                row["period_start"],
                str(row["count"]),
                format_distance(row["distance"], units),
                format_duration(row["moving_time"]),
                format_elevation(row["elevation_gain"], units),
            )

        console.print(table)
    finally:
        session.close()


@app.command("pace")
def analyze_pace(
    last: str = typer.Option("90d", "--last", help='Time window (e.g., "30d", "6m", "1y").'),
    activity_type: str = typer.Option("Run", "--type", help='Activity type (e.g., "Run", "Ride").'),
) -> None:
    """Pace trend analysis over time.

    Shows average pace per activity and overall trend direction
    (improving, declining, or stable).

    Examples:
        openactivity strava analyze pace
        openactivity strava analyze pace --last 1y --type Run
        openactivity strava analyze pace --json
    """
    state = get_global_state()
    use_json = state.get("json", False)
    units = state.get("units", "metric")

    init_db()
    session = get_session()

    try:
        from openactivity.analysis.pace import compute_pace_trend

        result = compute_pace_trend(session, last=last, activity_type=activity_type)

        if not result["activities"]:
            if use_json:
                print_json(result)
            else:
                console.print(f"No {activity_type} activities found in the last {last}.")
            return

        if use_json:
            print_json(result)
            return

        trend_icon = {
            "improving": "[green]↗ Improving[/green]",
            "declining": "[red]↘ Declining[/red]",
            "stable": "[yellow]→ Stable[/yellow]",
        }

        console.print(f"\n[bold]Pace Trend ({activity_type}, last {last})[/bold]")
        console.print(f"  Trend: {trend_icon.get(result['trend'], result['trend'])}")

        avg_pace = result["avg_pace"]
        if avg_pace > 0:
            mins = int(avg_pace // 60)
            secs = int(avg_pace % 60)
            unit_label = "/km" if units == "metric" else "/mi"
            console.print(f"  Average pace: {mins}:{secs:02d} {unit_label}")

        table = Table(show_header=True, header_style="bold")
        table.add_column("Date")
        table.add_column("Name")
        table.add_column("Distance", justify="right")
        table.add_column("Pace", justify="right")

        for point in result["activities"][-20:]:  # Last 20
            pace = point["pace_per_km"]
            mins = int(pace // 60)
            secs = int(pace % 60)
            unit_label = "/km" if units == "metric" else "/mi"
            table.add_row(
                point["date"][:10],
                (point["name"] or "")[:25],
                format_distance(point["distance"], units),
                f"{mins}:{secs:02d} {unit_label}",
            )

        console.print(table)
    finally:
        session.close()


@app.command("zones")
def analyze_zones(
    zone_type: str = typer.Option(
        "heartrate",
        "--zone-type",
        help='"heartrate" or "power".',
    ),
    activity_type: str | None = typer.Option(None, "--type", help="Filter by activity type."),
    last: str = typer.Option("all", "--last", help='Time window (e.g., "90d", "all").'),
) -> None:
    """Heart rate or power zone distribution across activities.

    Aggregates time spent in each zone across all matching activities.

    Examples:
        openactivity strava analyze zones
        openactivity strava analyze zones --zone-type power --type Ride
        openactivity strava analyze zones --last 90d --json
    """
    state = get_global_state()
    use_json = state.get("json", False)

    init_db()
    session = get_session()

    try:
        from openactivity.analysis.zones import compute_zone_distribution

        data = compute_zone_distribution(
            session,
            zone_type=zone_type,
            activity_type=activity_type,
            last=last,
        )

        if not data:
            if use_json:
                print_json([])
            else:
                console.print(
                    f"No {zone_type} zone data found. Zone data may require Strava Premium."
                )
            return

        if use_json:
            print_json(data)
            return

        console.print(f"\n[bold]{zone_type.title()} Zone Distribution[/bold]")

        table = Table(show_header=True, header_style="bold")
        table.add_column("Zone")
        table.add_column("Range")
        table.add_column("Time", justify="right")
        table.add_column("%", justify="right")
        table.add_column("Bar")

        for row in data:
            max_str = str(row["max_value"]) if row["max_value"] >= 0 else "∞"
            bar = "█" * int(row["percentage"] / 2)
            table.add_row(
                f"Z{row['zone_index']}",
                f"{row['min_value']}-{max_str}",
                format_duration(row["total_seconds"]),
                f"{row['percentage']:.1f}",
                bar,
            )

        console.print(table)
    finally:
        session.close()


@app.command("power-curve")
def analyze_power_curve(
    last: str = typer.Option("90d", "--last", help='Time window (e.g., "90d", "1y").'),
) -> None:
    """Best average power for key durations.

    Shows peak power for 5s, 1min, 5min, 20min, and 60min from
    watts stream data.

    Examples:
        openactivity strava analyze power-curve
        openactivity strava analyze power-curve --last 1y
        openactivity strava analyze power-curve --json
    """
    state = get_global_state()
    use_json = state.get("json", False)

    init_db()
    session = get_session()

    try:
        from openactivity.analysis.power import compute_power_curve

        data = compute_power_curve(session, last=last)

        has_data = any(d["best_power"] is not None for d in data)

        if not has_data:
            if use_json:
                print_json(data)
            else:
                console.print(
                    "No power data found. Power data requires a power meter and synced stream data."
                )
            return

        if use_json:
            print_json(data)
            return

        console.print(f"\n[bold]Power Curve (last {last})[/bold]")

        table = Table(show_header=True, header_style="bold")
        table.add_column("Duration")
        table.add_column("Best Power", justify="right")
        table.add_column("Date")
        table.add_column("Activity")

        for row in data:
            if row["best_power"] is not None:
                table.add_row(
                    row["duration_label"],
                    f"{row['best_power']} W",
                    (row["date"] or "")[:10],
                    (row["activity_name"] or "")[:25],
                )
            else:
                table.add_row(row["duration_label"], "-", "-", "-")

        console.print(table)
    finally:
        session.close()
