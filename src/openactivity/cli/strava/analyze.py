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
    format_speed,
    format_speed_as_pace,
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
        "  openactivity strava analyze compare --range1 2025-01-01:2025-03-31"
        " --range2 2026-01-01:2026-03-31\n"
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


@app.command("compare")
def analyze_compare(
    range1: str = typer.Option(
        ...,
        "--range1",
        help="First date range in YYYY-MM-DD:YYYY-MM-DD format.",
    ),
    range2: str = typer.Option(
        ...,
        "--range2",
        help="Second date range in YYYY-MM-DD:YYYY-MM-DD format.",
    ),
    activity_type: str | None = typer.Option(
        None, "--type", help='Filter by activity type (e.g., "Run", "Ride").'
    ),
) -> None:
    """Compare training metrics across two date ranges.

    Shows a side-by-side table with totals and averages for each range,
    plus deltas and percentage changes.

    Examples:
        openactivity strava analyze compare \\
          --range1 2025-01-01:2025-03-31 --range2 2026-01-01:2026-03-31

        openactivity strava analyze compare \\
          --range1 2025-01-01:2025-06-30 --range2 2026-01-01:2026-06-30 --type Run

        openactivity strava analyze compare \\
          --range1 2025-01-01:2025-12-31 --range2 2026-01-01:2026-03-31 --json
    """
    from openactivity.analysis.compare import (
        aggregate_range_metrics,
        comparison_to_dict,
        compute_comparison,
        detect_overlap,
        format_pct_change,
        parse_date_range,
    )
    from openactivity.output.errors import exit_with_error

    state = get_global_state()
    use_json = state.get("json", False)
    units = state.get("units", "metric")

    # Parse and validate date ranges
    try:
        r1_start, r1_end = parse_date_range(range1)
    except ValueError as e:
        exit_with_error(
            "invalid_range",
            str(e),
            "Use format: YYYY-MM-DD:YYYY-MM-DD (e.g., 2025-01-01:2025-03-31).",
            use_json=use_json,
        )
        return  # unreachable but helps type checker

    try:
        r2_start, r2_end = parse_date_range(range2)
    except ValueError as e:
        exit_with_error(
            "invalid_range",
            str(e),
            "Use format: YYYY-MM-DD:YYYY-MM-DD (e.g., 2025-01-01:2025-03-31).",
            use_json=use_json,
        )
        return

    overlap = detect_overlap((r1_start, r1_end), (r2_start, r2_end))

    init_db()
    session = get_session()

    try:
        r1_metrics = aggregate_range_metrics(
            session, start=r1_start, end=r1_end, activity_type=activity_type,
        )
        r2_metrics = aggregate_range_metrics(
            session, start=r2_start, end=r2_end, activity_type=activity_type,
        )

        comparison = compute_comparison(
            r1_metrics, r2_metrics,
            activity_type=activity_type,
            overlap=overlap,
        )

        # US2: no-results message for type-filtered queries
        if activity_type and r1_metrics.count == 0 and r2_metrics.count == 0:
            if use_json:
                print_json(comparison_to_dict(comparison, units=units))
            else:
                console.print(
                    f"No {activity_type} activities found in either range."
                )
            return

        # US3: JSON output
        if use_json:
            print_json(comparison_to_dict(comparison, units=units))
            return

        # US1: Rich table output
        title = "Training Comparison"
        if activity_type:
            title += f" ({activity_type})"

        table = Table(title=title, show_header=True, header_style="bold")
        table.add_column("Metric")
        table.add_column("Range 1", justify="right")
        table.add_column("Range 2", justify="right")
        table.add_column("Delta", justify="right")
        table.add_column("Change", justify="right")

        # Activities count
        _add_comparison_row(
            table, "Activities",
            str(r1_metrics.count), str(r2_metrics.count),
            comparison.deltas.get("count", 0),
            comparison.pct_changes.get("count"),
            fmt="int",
        )

        # Distance
        _add_comparison_row(
            table, "Distance",
            format_distance(r1_metrics.distance, units),
            format_distance(r2_metrics.distance, units),
            comparison.deltas.get("distance_m", 0),
            comparison.pct_changes.get("distance_m"),
            fmt="distance", units=units,
        )

        # Moving Time
        _add_comparison_row(
            table, "Moving Time",
            format_duration(r1_metrics.moving_time),
            format_duration(r2_metrics.moving_time),
            comparison.deltas.get("moving_time_s", 0),
            comparison.pct_changes.get("moving_time_s"),
            fmt="duration",
        )

        # Elevation
        _add_comparison_row(
            table, "Elevation",
            format_elevation(r1_metrics.elevation_gain, units),
            format_elevation(r2_metrics.elevation_gain, units),
            comparison.deltas.get("elevation_gain_m", 0),
            comparison.pct_changes.get("elevation_gain_m"),
            fmt="elevation", units=units,
        )

        # Avg Pace (if present)
        if "avg_pace_s_per_km" in comparison.deltas:
            p1 = r1_metrics.avg_pace
            p2 = r2_metrics.avg_pace
            table.add_row(
                "Avg Pace",
                format_speed_as_pace(1.0 / p1, units) if p1 and p1 > 0 else "N/A",
                format_speed_as_pace(1.0 / p2, units) if p2 and p2 > 0 else "N/A",
                _format_delta_duration(comparison.deltas["avg_pace_s_per_km"]),
                format_pct_change(comparison.pct_changes.get("avg_pace_s_per_km")),
            )

        # Avg Speed (if present)
        if "avg_speed_m_s" in comparison.deltas:
            s1 = r1_metrics.avg_speed
            s2 = r2_metrics.avg_speed
            table.add_row(
                "Avg Speed",
                format_speed(s1, units) if s1 else "N/A",
                format_speed(s2, units) if s2 else "N/A",
                _format_delta_speed(comparison.deltas["avg_speed_m_s"], units),
                format_pct_change(comparison.pct_changes.get("avg_speed_m_s")),
            )

        # Avg HR (if present)
        if "avg_heartrate" in comparison.deltas:
            hr1 = r1_metrics.avg_heartrate
            hr2 = r2_metrics.avg_heartrate
            delta_hr = comparison.deltas["avg_heartrate"]
            sign = "+" if delta_hr > 0 else ""
            table.add_row(
                "Avg Heart Rate",
                f"{hr1:.0f} bpm" if hr1 else "N/A",
                f"{hr2:.0f} bpm" if hr2 else "N/A",
                f"{sign}{delta_hr:.0f}",
                format_pct_change(comparison.pct_changes.get("avg_heartrate")),
            )

        console.print(table)

        # Range metadata footer
        console.print(
            f"  Range 1: {r1_start} → {r1_end}"
        )
        console.print(
            f"  Range 2: {r2_start} → {r2_end}"
        )
        if overlap:
            console.print(
                "[yellow]  ⚠ Ranges overlap — shared activities contribute to both sides.[/yellow]"
            )

    finally:
        session.close()


def _add_comparison_row(
    table: Table,
    label: str,
    val1_str: str,
    val2_str: str,
    delta: float,
    pct: float | None,
    *,
    fmt: str = "float",
    units: str = "metric",
) -> None:
    """Add a row to the comparison table with formatted delta."""
    from openactivity.analysis.compare import format_pct_change

    if fmt == "int":
        sign = "+" if delta > 0 else ""
        delta_str = f"{sign}{int(delta)}"
    elif fmt == "distance":
        sign = "+" if delta > 0 else ""
        delta_str = f"{sign}{format_distance(abs(delta), units)}"
        if delta < 0:
            delta_str = f"-{format_distance(abs(delta), units)}"
    elif fmt == "duration":
        delta_str = _format_delta_duration(delta)
    elif fmt == "elevation":
        sign = "+" if delta > 0 else ""
        delta_str = f"{sign}{format_elevation(abs(delta), units)}"
        if delta < 0:
            delta_str = f"-{format_elevation(abs(delta), units)}"
    else:
        sign = "+" if delta > 0 else ""
        delta_str = f"{sign}{delta:.1f}"

    table.add_row(label, val1_str, val2_str, delta_str, format_pct_change(pct))


def _format_delta_duration(seconds: float) -> str:
    """Format a duration delta with sign."""
    sign = "+" if seconds > 0 else "-"
    abs_secs = int(abs(seconds))
    if abs_secs == 0:
        return "—"
    return f"{sign}{format_duration(abs_secs)}"


def _format_delta_speed(delta_m_s: float, units: str) -> str:
    """Format a speed delta with sign."""
    if delta_m_s == 0:
        return "—"
    sign = "+" if delta_m_s > 0 else "-"
    return f"{sign}{format_speed(abs(delta_m_s), units)}"


@app.command("effort")
def analyze_effort(
    last: str = typer.Option(
        "90d", "--last", help='Time window: "30d", "90d", "6m", "1y", "all".'
    ),
    activity_type: str = typer.Option(
        "Run", "--type", help='Activity type (e.g., "Run", "Ride").'
    ),
) -> None:
    """Grade-adjusted pace and effort score trend over time.

    Shows GAP (equivalent flat pace) and effort score for each activity,
    enabling fair comparison of efforts across varying terrain.

    Examples:
        openactivity strava analyze effort
        openactivity strava analyze effort --last 6m
        openactivity strava analyze effort --type Ride --last 1y
        openactivity strava analyze effort --json
    """
    state = get_global_state()
    use_json = state.get("json", False)
    units = state.get("units", "metric")

    init_db()
    session = get_session()

    try:
        from openactivity.analysis.gap import get_effort_trend

        result = get_effort_trend(
            session, time_window=last, activity_type=activity_type
        )

        if not result["activities"]:
            if use_json:
                print_json(result)
            else:
                console.print(
                    f"No {activity_type} activities found in the last {last}."
                )
            return

        # Format GAP values for display
        avg_gap = result["avg_gap"]
        if avg_gap:
            result["avg_gap_formatted"] = format_speed_as_pace(avg_gap, units)

        for entry in result["activities"]:
            gap = entry.get("gap")
            entry["actual_pace_formatted"] = (
                format_speed_as_pace(entry["actual_pace"], units)
                if entry.get("actual_pace")
                else None
            )
            entry["gap_formatted"] = (
                format_speed_as_pace(gap, units) if gap else None
            )

        if use_json:
            print_json(result)
            return

        # Rich table output
        trend_icon = {
            "improving": "[green]↗ Improving[/green]",
            "declining": "[red]↘ Declining[/red]",
            "stable": "[yellow]→ Stable[/yellow]",
        }

        table = Table(
            title=f"Effort Trend ({activity_type}, last {last})",
            show_header=True,
            header_style="bold",
        )
        table.add_column("Date")
        table.add_column("Activity")
        table.add_column("Distance", justify="right")
        table.add_column("Pace", justify="right")
        table.add_column("GAP", justify="right")
        table.add_column("Elev.", justify="right")
        table.add_column("Effort", justify="right")

        for entry in result["activities"][-30:]:  # Last 30
            date_str = entry["date"][:10] if entry["date"] else ""
            table.add_row(
                date_str,
                (entry["activity_name"] or "")[:20],
                format_distance(entry["distance"], units),
                entry.get("actual_pace_formatted") or "N/A",
                entry.get("gap_formatted") or "—",
                format_elevation(entry["elevation_gain"], units),
                str(entry["effort_score"]),
            )

        console.print(table)

        # Summary line
        trend_str = trend_icon.get(result["trend"], result["trend"])
        avg_gap_str = result.get("avg_gap_formatted") or "N/A"
        console.print(
            f"\n  Trend: {trend_str}  |  "
            f"Avg GAP: {avg_gap_str}  |  "
            f"Avg Effort: {result['avg_effort_score']}"
        )
    finally:
        session.close()


@app.command("blocks")
def analyze_blocks(
    last: str = typer.Option(
        "6m", "--last", help='Time window: "6m", "1y", "all".'
    ),
    activity_type: str = typer.Option(
        "Run", "--type", help='Activity type (e.g., "Run", "Ride").'
    ),
) -> None:
    """Detect training phases (base, build, peak, recovery) over time.

    Classifies weeks by volume and intensity patterns, then groups
    consecutive similar weeks into named training blocks.

    Phases:

      Base     — High volume, low intensity (building aerobic fitness)

      Build    — Rising volume and intensity (preparing for performance)

      Peak     — High intensity, tapering volume (race-ready sharpening)

      Recovery — Low volume, <70% of recent avg (rest and adaptation)

    Examples:
        openactivity strava analyze blocks
        openactivity strava analyze blocks --last 1y
        openactivity strava analyze blocks --type Ride --last all
        openactivity strava analyze blocks --json
    """
    state = get_global_state()
    use_json = state.get("json", False)
    units = state.get("units", "metric")

    init_db()
    session = get_session()

    try:
        from openactivity.analysis.blocks import PHASE_DESCRIPTIONS, detect_blocks

        result = detect_blocks(
            session, time_window=last, activity_type=activity_type
        )

        # Handle insufficient data
        if "error" in result:
            if use_json:
                print_json(result)
            else:
                console.print(result["message"])
            return

        # Format distances for display/JSON
        for block in result["blocks"]:
            block["avg_weekly_distance_formatted"] = format_distance(
                block["avg_weekly_distance"], units
            )
            block["start_date"] = (
                block["start_date"].strftime("%Y-%m-%d")
                if hasattr(block["start_date"], "strftime")
                else str(block["start_date"])
            )
            block["end_date"] = (
                block["end_date"].strftime("%Y-%m-%d")
                if hasattr(block["end_date"], "strftime")
                else str(block["end_date"])
            )

        if use_json:
            print_json(result)
            return

        # Rich table output
        table = Table(
            title=f"Training Blocks ({activity_type}, last {last})",
            show_header=True,
            header_style="bold",
        )
        table.add_column("Phase")
        table.add_column("Start")
        table.add_column("End")
        table.add_column("Weeks", justify="right")
        table.add_column("Avg Vol.", justify="right")
        table.add_column("Activities", justify="right")
        table.add_column("Intensity", justify="right")

        for block in result["blocks"]:
            phase_label = block["phase"].title()
            if block["is_current"]:
                phase_label += " ◀"

            table.add_row(
                phase_label,
                block["start_date"],
                block["end_date"],
                str(block["week_count"]),
                block["avg_weekly_distance_formatted"],
                str(block["activity_count"]),
                str(block["avg_intensity"]),
            )

        console.print(table)

        # Summary line
        current = result["current_phase"].title()
        desc = PHASE_DESCRIPTIONS.get(result["current_phase"], "")
        console.print(
            f"\n  Current Phase: [bold]{current}[/bold]  |  "
            f"Total Weeks: {result['total_weeks']}  |  "
            f"Activities: {result['total_activities']}"
        )
        if desc:
            console.print(f"  {desc}")
    finally:
        session.close()
