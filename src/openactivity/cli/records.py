"""Unified personal records commands — provider-agnostic."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from openactivity.cli.root import get_global_state
from openactivity.db.database import get_session, init_db
from openactivity.output.errors import exit_with_error
from openactivity.output.json import print_json
from openactivity.output.units import format_duration, format_speed_as_pace

console = Console()

app = typer.Typer(
    name="records",
    help=(
        "Personal records — scan, view, and track PRs.\n\n"
        "Examples:\n\n"
        "  openactivity records scan\n"
        "  openactivity records list\n"
        "  openactivity records list --type running\n"
        "  openactivity records history --distance 5K\n"
        "  openactivity records scan --provider strava\n"
    ),
    no_args_is_help=True,
)


@app.command("scan")
def scan_records(
    full: bool = typer.Option(False, "--full", help="Re-scan all activities (reset scan state)."),
    provider: str | None = typer.Option(None, "--provider", help='Filter by provider (e.g., "strava", "garmin"). Default: all.'),
) -> None:
    """Scan synced activities to detect personal records.

    Examples:
        openactivity records scan
        openactivity records scan --full
        openactivity records scan --provider garmin
        openactivity records scan --json
    """
    state = get_global_state()
    use_json = state.get("json", False)

    init_db()
    session = get_session()

    try:
        from openactivity.analysis.records import scan_all_activities

        if not use_json:
            with Progress() as progress:
                task = progress.add_task("Scanning activities...", total=None)
                result = scan_all_activities(session, full=full, provider=provider)
                progress.update(task, completed=True)
        else:
            result = scan_all_activities(session, full=full, provider=provider)

        if use_json:
            print_json(result)
            return

        console.print(f"\nScanned [bold]{result['scanned']}[/bold] activities.")
        if result["new_records"] > 0:
            console.print(f"  New PRs found: [green]{result['new_records']}[/green]")
        if result["updated_records"] > 0:
            console.print(f"  PRs updated: [yellow]{result['updated_records']}[/yellow]")
        if result["new_records"] == 0 and result["updated_records"] == 0:
            console.print("  No new personal records detected.")
    finally:
        session.close()


@app.command("list")
def list_records(
    record_type: str | None = typer.Option(
        None, "--type", help='Filter by "running" or "cycling".'
    ),
) -> None:
    """Show current personal records.

    Examples:
        openactivity records list
        openactivity records list --type running
        openactivity records list --json
    """
    state = get_global_state()
    use_json = state.get("json", False)
    units = state.get("units", "metric")

    init_db()
    session = get_session()

    try:
        from openactivity.analysis.records import (
            CYCLING_POWER_DURATIONS,
            DISTANCE_DISPLAY,
            RUNNING_DISTANCES,
            sort_records,
        )
        from openactivity.db.queries import get_custom_distances, get_personal_records

        db_type = None
        if record_type:
            rt = record_type.lower()
            if rt == "running":
                db_type = "distance"
            elif rt == "cycling":
                db_type = "power"
            else:
                exit_with_error(
                    "invalid_type",
                    f"Unknown record type: {record_type}",
                    'Use --type "running" or --type "cycling".',
                    use_json=use_json,
                )

        records = sort_records(get_personal_records(session, record_type=db_type))
        custom_labels = {cd.label for cd in get_custom_distances(session)}

        if use_json:
            json_records = []
            for r in records:
                entry = {
                    "distance_type": r.distance_type,
                    "record_type": r.record_type,
                    "value": r.value,
                    "activity_id": r.activity_id,
                    "activity_name": r.activity_name,
                    "achieved_date": r.achieved_date,
                }
                if r.record_type == "distance":
                    entry["time"] = format_duration(int(r.value))
                    entry["pace"] = format_speed_as_pace(
                        r.distance_meters / r.value if r.value > 0 else 0, units
                    )
                else:
                    entry["power"] = int(r.value)
                json_records.append(entry)
            print_json(json_records)
            return

        if not records:
            console.print(
                "No personal records found. "
                "Run 'openactivity records scan' first."
            )
            return

        # Split into running and cycling
        running_records = [r for r in records if r.record_type == "distance"]
        power_records = [r for r in records if r.record_type == "power"]

        if running_records and db_type != "power":
            table = Table(title="Personal Records — Running", show_header=True, header_style="bold")
            table.add_column("Distance")
            table.add_column("Time", justify="right")
            table.add_column("Pace", justify="right")
            table.add_column("Date")
            table.add_column("Activity")

            for r in running_records:
                label = DISTANCE_DISPLAY.get(r.distance_type, r.distance_type)
                if r.distance_type in custom_labels:
                    label += " *"
                pace_val = format_speed_as_pace(
                    r.distance_meters / r.value if r.value > 0 else 0, units
                )
                date_str = r.achieved_date.strftime("%Y-%m-%d") if r.achieved_date else "—"
                table.add_row(
                    label,
                    format_duration(int(r.value)),
                    pace_val,
                    date_str,
                    r.activity_name or "—",
                )
            console.print(table)
            if custom_labels & {r.distance_type for r in running_records}:
                console.print("  * = custom distance")

        if power_records and db_type != "distance":
            table = Table(
                title="Personal Records — Cycling Power", show_header=True, header_style="bold"
            )
            table.add_column("Duration")
            table.add_column("Power", justify="right")
            table.add_column("Date")
            table.add_column("Activity")

            for r in power_records:
                label = DISTANCE_DISPLAY.get(r.distance_type, r.distance_type)
                date_str = r.achieved_date.strftime("%Y-%m-%d") if r.achieved_date else "—"
                table.add_row(
                    label,
                    f"{int(r.value):,} W",
                    date_str,
                    r.activity_name or "—",
                )
            console.print(table)

        console.print(
            "\nView PR history: "
            "[bold]openactivity records history --distance <LABEL>[/bold]"
        )
        all_labels = [label for label, _ in RUNNING_DISTANCES]
        all_labels += [label for label, _ in CYCLING_POWER_DURATIONS]
        if custom_labels:
            all_labels += sorted(custom_labels)
        console.print(f"  Available: {', '.join(all_labels)}")
    finally:
        session.close()


@app.command("history")
def show_history(
    distance: str = typer.Option(
        ..., "--distance",
        help=(
            "Distance label. "
            "Running: 1mi, 5K, 10K, half, marathon. "
            "Cycling: 5s, 1min, 5min, 20min, 60min. "
            "Or any custom distance you've added."
        ),
    ),
) -> None:
    """Show PR progression for a specific distance or power duration.

    Examples:
        openactivity records history --distance 5K
        openactivity records history --distance 20min --json
    """
    state = get_global_state()
    use_json = state.get("json", False)
    units = state.get("units", "metric")

    init_db()
    session = get_session()

    try:
        from openactivity.analysis.records import DISTANCE_DISPLAY
        from openactivity.db.queries import get_records_by_distance

        records = get_records_by_distance(session, distance)

        if not records:
            if use_json:
                print_json({"distance": distance, "records": []})
            else:
                console.print(f"No records found for '{distance}'.")
            return

        display_name = DISTANCE_DISPLAY.get(distance, distance)
        is_power = records[0].record_type == "power"

        if use_json:
            json_records = []
            prev_value = None
            for i, r in enumerate(records):
                entry = {
                    "rank": i + 1,
                    "distance_type": r.distance_type,
                    "value": r.value,
                    "achieved_date": r.achieved_date,
                    "activity_name": r.activity_name,
                    "is_current": r.is_current,
                }
                if is_power:
                    entry["power"] = int(r.value)
                    entry["improvement"] = (
                        int(r.value - prev_value) if prev_value is not None else None
                    )
                else:
                    entry["time"] = format_duration(int(r.value))
                    entry["pace"] = format_speed_as_pace(
                        r.distance_meters / r.value if r.value > 0 else 0, units
                    )
                    entry["improvement"] = (
                        round(prev_value - r.value, 1) if prev_value is not None else None
                    )
                prev_value = r.value
                json_records.append(entry)
            print_json({"distance": distance, "records": json_records})
            return

        table = Table(title=f"{display_name} PR Progression", show_header=True, header_style="bold")
        table.add_column("#", justify="right")
        table.add_column("Date")
        if is_power:
            table.add_column("Power", justify="right")
        else:
            table.add_column("Time", justify="right")
            table.add_column("Pace", justify="right")
        table.add_column("Improvement", justify="right")
        table.add_column("Activity")

        prev_value = None
        for i, r in enumerate(records):
            rank = f"{i + 1}"
            if r.is_current:
                rank += " \u2605"

            date_str = r.achieved_date.strftime("%Y-%m-%d") if r.achieved_date else "—"

            if is_power:
                improvement = (
                    f"+{int(r.value - prev_value)} W" if prev_value is not None else "—"
                )
                table.add_row(
                    rank,
                    date_str,
                    f"{int(r.value):,} W",
                    improvement,
                    r.activity_name or "—",
                )
            else:
                pace_val = format_speed_as_pace(
                    r.distance_meters / r.value if r.value > 0 else 0, units
                )
                if prev_value is not None:
                    delta = prev_value - r.value
                    improvement = f"-{format_duration(int(abs(delta)))}"
                else:
                    improvement = "—"
                table.add_row(
                    rank,
                    date_str,
                    format_duration(int(r.value)),
                    pace_val,
                    improvement,
                    r.activity_name or "—",
                )
            prev_value = r.value

        console.print(table)
        console.print("  \u2605 = current PR")
    finally:
        session.close()


@app.command("add-distance")
def add_distance(
    label: str = typer.Argument(help='Distance label (e.g., "15K", "10mi").'),
    meters: float = typer.Option(None, "--meters", "-m", help="Distance in meters."),
    miles: float = typer.Option(None, "--miles", "-mi", help="Distance in miles."),
    km: float = typer.Option(None, "--km", "-k", help="Distance in kilometers."),
) -> None:
    """Add a custom distance for PR tracking.

    Examples:
        openactivity records add-distance 15K --km 15
        openactivity records add-distance 10mi --miles 10
        openactivity records add-distance 50K --meters 50000
    """
    state = get_global_state()
    use_json = state.get("json", False)

    specified = sum(v is not None for v in [meters, miles, km])
    if specified == 0:
        exit_with_error(
            "missing_distance", "No distance specified.",
            "Use --meters, --miles, or --km.", use_json=use_json,
        )
        return
    if specified > 1:
        exit_with_error(
            "multiple_distances", "Multiple distance units specified.",
            "Use only one of --meters, --miles, or --km.", use_json=use_json,
        )
        return

    if miles is not None:
        meters = miles * 1609.344
    elif km is not None:
        meters = km * 1000.0

    init_db()
    session = get_session()

    try:
        from openactivity.analysis.records import add_custom_distance

        cd = add_custom_distance(session, label, meters)
        if use_json:
            print_json({"label": cd.label, "distance_meters": cd.distance_meters})
        else:
            console.print(
                f"Added custom distance: [bold]{label}[/bold] ({meters:,.0f} m). "
                f"Run 'openactivity records scan' to detect PRs."
            )
    except ValueError as e:
        exit_with_error(
            "invalid_distance", str(e),
            "Check the label and try again.", use_json=use_json,
        )
    finally:
        session.close()


@app.command("remove-distance")
def remove_distance(
    label: str = typer.Argument(help="Distance label to remove."),
) -> None:
    """Remove a custom distance and its records.

    Examples:
        openactivity records remove-distance 15K
    """
    state = get_global_state()
    use_json = state.get("json", False)

    init_db()
    session = get_session()

    try:
        from openactivity.analysis.records import remove_custom_distance

        count = remove_custom_distance(session, label)
        if use_json:
            print_json({"label": label, "records_removed": count})
        else:
            console.print(f"Removed custom distance '{label}' and {count} associated records.")
    except ValueError as e:
        exit_with_error(
            "invalid_distance", str(e),
            "Check the label and try again.", use_json=use_json,
        )
    finally:
        session.close()
