"""Strava activities list and detail commands."""

from __future__ import annotations

from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table

from openactivity.cli.root import get_global_state
from openactivity.db.database import get_session, init_db
from openactivity.db.queries import (
    bulk_link_activities,
    count_activities,
    get_activities,
    get_activity_by_id,
    get_activity_streams,
    get_activity_zones,
    get_gear,
    get_laps,
    get_provider_badge,
    unlink_activity,
)
from openactivity.output.errors import exit_with_error
from openactivity.output.json import print_json
from openactivity.output.units import (
    format_distance,
    format_duration,
    format_elevation,
    format_speed_as_pace,
)

console = Console()

app = typer.Typer(
    name="activities",
    help=(
        "Browse and search activities.\n\n"
        "Examples:\n\n"
        "  openactivity strava activities list\n"
        "  openactivity strava activities list --type run --limit 10\n"
    ),
    no_args_is_help=True,
)


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as e:
        raise typer.BadParameter(
            f"Invalid date format: '{value}'. Use ISO format (YYYY-MM-DD)."
        ) from e


@app.command("list")
def list_activities(
    activity_type: str | None = typer.Option(
        None, "--type", help='Filter by type (e.g., "Run", "Ride").'
    ),
    after: str | None = typer.Option(
        None, "--after", help="Show activities after date (YYYY-MM-DD)."
    ),
    before: str | None = typer.Option(
        None, "--before", help="Show activities before date (YYYY-MM-DD)."
    ),
    search: str | None = typer.Option(None, "--search", help="Search by activity name."),
    limit: int = typer.Option(20, "--limit", help="Max results."),
    offset: int = typer.Option(0, "--offset", help="Skip first N results."),
    sort: str = typer.Option(
        "date",
        "--sort",
        help='Sort by: "date", "distance", "duration".',
    ),
    provider: str | None = typer.Option(
        None,
        "--provider",
        help='Filter by provider: "strava" or "garmin".',
    ),
) -> None:
    """List activities from local storage with optional filters.

    Examples:
        openactivity strava activities list
        openactivity strava activities list --type Run --after 2026-01-01
        openactivity strava activities list --search "morning" --sort distance
        openactivity strava activities list --provider garmin
        openactivity strava activities list --json
    """
    state = get_global_state()
    use_json = state.get("json", False)
    units = state.get("units", "metric")

    init_db()
    session = get_session()

    try:
        after_dt = _parse_date(after)
        before_dt = _parse_date(before)

        activities = get_activities(
            session,
            activity_type=activity_type,
            after=after_dt,
            before=before_dt,
            search=search,
            provider=provider,
            sort=sort,
            limit=limit,
            offset=offset,
        )

        total = count_activities(
            session,
            activity_type=activity_type,
            after=after_dt,
            before=before_dt,
            search=search,
            provider=provider,
        )

        if not activities:
            if use_json:
                print_json([])
            else:
                console.print("No activities found matching your filters.")
            return

        if use_json:
            data = []
            for a in activities:
                data.append(
                    {
                        "id": a.id,
                        "name": a.name,
                        "type": a.type,
                        "provider": a.provider,
                        "start_date": a.start_date,
                        "distance": a.distance,
                        "moving_time": a.moving_time,
                        "total_elevation_gain": a.total_elevation_gain,
                        "average_speed": a.average_speed,
                        "average_heartrate": a.average_heartrate,
                        "average_watts": a.average_watts,
                    }
                )
            print_json(data)
            return

        table = Table(show_header=True, header_style="bold")
        table.add_column("ID")
        table.add_column("Provider")
        table.add_column("Date")
        table.add_column("Type")
        table.add_column("Name")
        table.add_column("Distance", justify="right")
        table.add_column("Time", justify="right")
        table.add_column("Elev", justify="right")

        for a in activities:
            date_str = a.start_date.strftime("%Y-%m-%d") if a.start_date else ""
            badge = get_provider_badge(session, a)
            table.add_row(
                str(a.id),
                badge,
                date_str,
                a.type or "",
                (a.name or "")[:30],
                format_distance(a.distance, units),
                format_duration(a.moving_time),
                format_elevation(a.total_elevation_gain, units),
            )

        console.print(table)
        console.print(
            f"\nShowing {len(activities)} of {total} activities. "
            f"Use --limit and --offset for pagination."
        )
    finally:
        session.close()


@app.command("link")
def link_command(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview matches without creating links."
    ),
    unlink_id: int | None = typer.Option(
        None, "--unlink", help="Remove the link for this activity ID."
    ),
) -> None:
    """Link matching activities across providers (Strava + Garmin).

    Scans for activities recorded on both platforms and links them.
    Linked activities show a [Strava+Garmin] badge in activity listings.

    Examples:
        openactivity activities link
        openactivity activities link --dry-run
        openactivity activities link --unlink 42
        openactivity activities link --json
    """
    state = get_global_state()
    use_json = state.get("json", False)

    init_db()
    session = get_session()

    try:
        # Handle unlink
        if unlink_id is not None:
            info = unlink_activity(session, unlink_id)
            if not info:
                if use_json:
                    print_json({"error": "no_link", "activity_id": unlink_id})
                else:
                    console.print(
                        f"[red]Activity #{unlink_id} is not linked to another provider.[/red]"
                    )
                raise typer.Exit(1)

            if use_json:
                print_json({"unlinked": info})
            else:
                strava_name = info.get("strava_name") or "Unknown"
                garmin_name = info.get("garmin_name") or "Unknown"
                console.print(
                    f"[green]✓[/green] Removed link for activity #{unlink_id} "
                    f"(Strava: {strava_name} ↔ Garmin: {garmin_name})"
                )
            return

        # Check we have activities from both providers
        from openactivity.db.models import Activity

        strava_count = session.query(Activity).filter_by(provider="strava").count()
        garmin_count = session.query(Activity).filter_by(provider="garmin").count()

        if strava_count == 0 and garmin_count == 0:
            if use_json:
                print_json({"error": "no_activities"})
            else:
                console.print(
                    "[red]No activities found.[/red] "
                    "Run `strava sync` or `garmin import` first."
                )
            raise typer.Exit(1)

        if strava_count == 0 or garmin_count == 0:
            present = "strava" if strava_count > 0 else "garmin"
            if use_json:
                print_json({"error": "single_provider", "provider": present})
            else:
                console.print(
                    f"Only [bold]{present}[/bold] activities found. "
                    "Import from another provider to enable linking."
                )
            return

        # Run bulk linking
        if not use_json:
            action = "Previewing" if dry_run else "Scanning for"
            console.print(f"{action} cross-provider matches...\n")

        result = bulk_link_activities(session, dry_run=dry_run)

        if use_json:
            print_json(result)
            return

        # Display matches
        matches = result["matches"]
        if matches:
            table = Table(show_header=True, header_style="bold")
            table.add_column("#", justify="right")
            table.add_column("Strava Activity")
            table.add_column("Garmin Activity")
            table.add_column("Date")
            table.add_column("Confidence", justify="right")

            for i, m in enumerate(matches, 1):
                date_str = m["strava_date"][:10] if m["strava_date"] else ""
                conf_str = f"{m['confidence']:.0%}"
                ambig = " ⚠" if m.get("ambiguous") else ""
                table.add_row(
                    str(i),
                    f"{m['strava_name'] or 'Untitled'} (#{m['strava_activity_id']})",
                    f"{m['garmin_name'] or 'Untitled'} (#{m['garmin_activity_id']})",
                    date_str,
                    conf_str + ambig,
                )

            console.print(table)
            console.print()

        # Summary
        action_word = "Would link" if dry_run else "Links created"
        link_count = result["matches_found"] if dry_run else result["links_created"]
        console.print("[bold]Summary[/bold]")
        console.print(
            f"  Scanned: {result['scanned_strava']} strava + "
            f"{result['scanned_garmin']} garmin activities"
        )
        console.print(f"  Matches found: {result['matches_found']}")
        console.print(f"  {action_word}: {link_count}")
        console.print(f"  Already linked: {result['already_linked']}")

        if any(m.get("ambiguous") for m in matches):
            console.print(
                "\n[yellow]⚠ Some matches had multiple candidates — "
                "highest confidence was selected.[/yellow]"
            )

    finally:
        session.close()


def show_activity(
    activity_id: int = typer.Argument(..., help="Strava activity ID."),
    export: str | None = typer.Option(None, "--export", help='Export format: "gpx" or "csv".'),
    output: str | None = typer.Option(None, "--output", help="Output file path (for export)."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing file."),
) -> None:
    """Show detailed information for a single activity.

    Examples:
        openactivity strava activity 12345678
        openactivity strava activity 12345678 --json
        openactivity strava activity 12345678 --export gpx --output run.gpx
    """
    state = get_global_state()
    use_json = state.get("json", False)
    units = state.get("units", "metric")

    init_db()
    session = get_session()

    try:
        activity = get_activity_by_id(session, activity_id)
        if not activity:
            exit_with_error(
                "not_found",
                f"Activity {activity_id} not found.",
                "Run 'openactivity strava sync' or 'openactivity garmin import' to fetch activities.",
                use_json=use_json,
            )

        laps = get_laps(session, activity_id)
        zones = get_activity_zones(session, activity_id)
        gear = get_gear(session, activity.gear_id) if activity.gear_id else None

        # Handle export
        if export:
            out_path = output or f"activity_{activity_id}.{export}"
            from openactivity.export.file_utils import write_file

            if export == "gpx":
                streams = get_activity_streams(session, activity_id)
                from openactivity.export.gpx import generate_gpx, gpx_to_string

                try:
                    gpx = generate_gpx(activity, streams)
                    write_file(out_path, gpx_to_string(gpx), force=force)
                except ValueError as e:
                    exit_with_error(
                        "export_error",
                        str(e),
                        "This activity may not have GPS data (e.g., treadmill).",
                        use_json=use_json,
                    )
            elif export == "csv":
                from openactivity.export.csv import activities_to_csv

                write_file(out_path, activities_to_csv([activity]), force=force)
            else:
                exit_with_error(
                    "invalid_format",
                    f"Unsupported export format: '{export}'.",
                    "Use --export gpx or --export csv.",
                    use_json=use_json,
                )
            return

        # Compute TSS if activity has HR data
        activity_tss = None
        if activity.average_heartrate and activity.moving_time:
            from openactivity.analysis.fitness import (
                compute_activity_tss,
                estimate_max_hr,
                estimate_rest_hr,
            )

            max_hr = estimate_max_hr(session)
            rest_hr = estimate_rest_hr(session)
            activity_tss = compute_activity_tss(activity, max_hr, rest_hr)

        if use_json:
            from openactivity.analysis.gap import compute_gap

            json_gap = compute_gap(activity, session)

            data = {
                "id": activity.id,
                "name": activity.name,
                "type": activity.type,
                "provider": activity.provider,
                "sport_type": activity.sport_type,
                "start_date": activity.start_date,
                "distance": activity.distance,
                "moving_time": activity.moving_time,
                "elapsed_time": activity.elapsed_time,
                "total_elevation_gain": activity.total_elevation_gain,
                "average_speed": activity.average_speed,
                "max_speed": activity.max_speed,
                "average_heartrate": activity.average_heartrate,
                "max_heartrate": activity.max_heartrate,
                "average_cadence": activity.average_cadence,
                "average_watts": activity.average_watts,
                "max_watts": activity.max_watts,
                "calories": activity.calories,
                "description": activity.description,
                "gap": json_gap.overall_gap,
                "gap_formatted": (
                    format_speed_as_pace(json_gap.overall_gap, units)
                    if json_gap.available and json_gap.overall_gap
                    else None
                ),
                "gap_available": json_gap.available,
                "tss": activity_tss,
                "gear": {"id": gear.id, "name": gear.name} if gear else None,
                "laps": [
                    {
                        "index": lap.lap_index,
                        "name": lap.name,
                        "distance": lap.distance,
                        "moving_time": lap.moving_time,
                        "average_speed": lap.average_speed,
                        "average_heartrate": lap.average_heartrate,
                        "gap": (
                            json_gap.lap_gaps[i]
                            if i < len(json_gap.lap_gaps)
                            else None
                        ),
                        "gap_formatted": (
                            format_speed_as_pace(json_gap.lap_gaps[i], units)
                            if i < len(json_gap.lap_gaps) and json_gap.lap_gaps[i]
                            else None
                        ),
                    }
                    for i, lap in enumerate(laps)
                ],
                "zones": [
                    {
                        "type": z.zone_type,
                        "index": z.zone_index,
                        "min": z.min_value,
                        "max": z.max_value,
                        "time_seconds": z.time_seconds,
                    }
                    for z in zones
                ],
            }
            print_json(data)
            return

        # Summary section
        date_str = (
            activity.start_date.strftime("%Y-%m-%d %H:%M") if activity.start_date else "Unknown"
        )
        badge = get_provider_badge(session, activity)
        console.print(
            f"\n[bold]{activity.name or 'Untitled'}[/bold]  ({activity.type or 'Unknown'})  {badge}"
        )
        console.print(f"  Date: {date_str}")
        console.print(f"  Distance: {format_distance(activity.distance, units)}")
        console.print(
            f"  Time: {format_duration(activity.moving_time)} "
            f"(elapsed: {format_duration(activity.elapsed_time)})"
        )
        console.print(f"  Elevation: {format_elevation(activity.total_elevation_gain, units)}")
        console.print(f"  Pace: {format_speed_as_pace(activity.average_speed, units)}")

        # Grade-Adjusted Pace
        from openactivity.analysis.gap import compute_gap

        gap_result = compute_gap(activity, session)
        if gap_result.available and gap_result.overall_gap:
            console.print(
                f"  GAP: {format_speed_as_pace(gap_result.overall_gap, units)}"
                "   (grade-adjusted)"
            )
        else:
            gap_result = None  # type: ignore[assignment]

        if activity.average_heartrate:
            console.print(
                f"  Heart Rate: {activity.average_heartrate:.0f} avg "
                f"/ {activity.max_heartrate:.0f} max bpm"
            )
        if activity_tss is not None:
            console.print(f"  TSS: {activity_tss:.1f}")
        if activity.average_watts:
            console.print(
                f"  Power: {activity.average_watts:.0f} avg W"
                + (f" / {activity.max_watts} max W" if activity.max_watts else "")
            )
        if activity.calories:
            console.print(f"  Calories: {activity.calories:.0f}")
        if gear:
            console.print(f"  Gear: {gear.name}")
        if activity.description:
            console.print(f"  Description: {activity.description}")

        # Laps section
        if laps:
            console.print("\n[bold]Laps[/bold]")
            lap_table = Table(show_header=True, header_style="bold")
            lap_table.add_column("#", justify="right")
            lap_table.add_column("Distance", justify="right")
            lap_table.add_column("Time", justify="right")
            lap_table.add_column("Pace", justify="right")
            if gap_result and gap_result.available:
                lap_table.add_column("GAP", justify="right")
            lap_table.add_column("HR", justify="right")

            for idx, lap in enumerate(laps):
                hr_str = f"{lap.average_heartrate:.0f}" if lap.average_heartrate else "-"
                row = [
                    str(lap.lap_index),
                    format_distance(lap.distance, units),
                    format_duration(lap.moving_time),
                    format_speed_as_pace(lap.average_speed, units),
                ]
                if gap_result and gap_result.available:
                    lap_gap = (
                        gap_result.lap_gaps[idx]
                        if idx < len(gap_result.lap_gaps) and gap_result.lap_gaps[idx]
                        else None
                    )
                    row.append(
                        format_speed_as_pace(lap_gap, units) if lap_gap else "—"
                    )
                row.append(hr_str)
                lap_table.add_row(*row)
            console.print(lap_table)

        # Zones section
        if zones:
            # Group by zone type
            zone_types: dict[str, list] = {}
            for z in zones:
                zone_types.setdefault(z.zone_type, []).append(z)

            for zone_type, zone_list in zone_types.items():
                total_time = sum(z.time_seconds for z in zone_list)
                console.print(f"\n[bold]{zone_type.title()} Zones[/bold]")
                zt = Table(show_header=True, header_style="bold")
                zt.add_column("Zone")
                zt.add_column("Range")
                zt.add_column("Time", justify="right")
                zt.add_column("%", justify="right")

                for z in zone_list:
                    max_str = str(z.max_value) if z.max_value >= 0 else "∞"
                    pct = f"{z.time_seconds / total_time * 100:.1f}" if total_time > 0 else "0"
                    zt.add_row(
                        f"Z{z.zone_index}",
                        f"{z.min_value}-{max_str}",
                        format_duration(z.time_seconds),
                        pct,
                    )
                console.print(zt)

        if not activity.synced_detail and activity.provider == "strava":
            console.print(
                "\n[dim]Note: Detailed data (laps, zones, streams) "
                "not yet synced. Run 'openactivity strava sync' "
                "to fetch.[/dim]"
            )
    finally:
        session.close()
