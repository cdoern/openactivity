"""Provider-agnostic analyze commands for cross-provider insights."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from openactivity.cli.root import get_global_state
from openactivity.db.database import get_session, init_db
from openactivity.output.json import print_json

console = Console()

app = typer.Typer(
    name="analyze",
    help=(
        "Analyze performance trends across all providers.\n\n"
        "Examples:\n\n"
        "  openactivity analyze fitness\n"
        "  openactivity analyze fitness --last 1y --type Run\n"
        "  openactivity analyze fitness --chart\n"
    ),
    no_args_is_help=True,
)


@app.command("fitness")
def analyze_fitness_cmd(
    last: str = typer.Option("6m", "--last", help='Time range: "30d", "90d", "6m", "1y", "all".'),
    activity_type: str | None = typer.Option(
        None, "--type", help='Filter by activity type (e.g., "Run", "Ride").'
    ),
    chart: bool = typer.Option(False, "--chart", help="Generate a fitness chart as PNG."),
    output: str = typer.Option(
        "fitness_chart.png", "--output", help="Chart output file path."
    ),
) -> None:
    """Fitness / Fatigue / Form analysis (ATL / CTL / TSB).

    Computes Training Stress Score (TSS) per activity from heart rate data,
    then derives daily Fitness (CTL), Fatigue (ATL), and Form (TSB).
    Uses data from all providers (Strava, Garmin).

    Examples:
        openactivity analyze fitness
        openactivity analyze fitness --last 1y --type Run
        openactivity analyze fitness --chart --output my_chart.png
        openactivity analyze fitness --json
    """
    state = get_global_state()
    use_json = state.get("json", False)

    init_db()
    session = get_session()

    try:
        from openactivity.analysis.fitness import (
            analyze_fitness as run_fitness,
            generate_fitness_chart,
        )

        result = run_fitness(session, last=last, activity_type=activity_type)

        if "error" in result:
            error = result["error"]
            meta = result.get("meta", {})
            if error == "no_hr_data":
                if use_json:
                    print_json(result)
                else:
                    console.print(
                        "[red]No activities with heart rate data found.[/red] "
                        "TSS requires HR data."
                    )
                    if meta.get("activities_without_hr", 0) > 0:
                        console.print(
                            f"  ({meta['activities_without_hr']} activities found, "
                            "but none have HR data)"
                        )
                raise typer.Exit(code=1)
            if error == "no_data":
                if use_json:
                    print_json(result)
                else:
                    console.print(
                        "[red]No activities found.[/red] "
                        "Run 'strava sync' or 'garmin import' first."
                    )
                raise typer.Exit(code=1)

        # Generate chart if requested
        if chart:
            daily_data = result.get("daily", [])
            if daily_data:
                try:
                    chart_path = generate_fitness_chart(daily_data, output)
                    if not use_json:
                        console.print(f"\n[green]Chart saved to {chart_path}[/green]")
                except ImportError:
                    if not use_json:
                        console.print(
                            "[red]Chart generation requires matplotlib.[/red] "
                            "Install with: pip install matplotlib"
                        )
                    raise typer.Exit(code=1)

        if use_json:
            print_json(result)
            return

        # Rich terminal output
        current = result["current"]
        meta = result["meta"]
        status = result["status"]
        daily = result.get("daily", [])

        # Status label with icon
        status_icons = {
            "peaking": "[green]PEAKING ▲[/green]",
            "maintaining": "[yellow]MAINTAINING →[/yellow]",
            "overreaching": "[red]OVERREACHING ▼[/red]",
            "detraining": "[dim]DETRAINING ↘[/dim]",
            "unknown": "[dim]UNKNOWN[/dim]",
        }
        status_display = status_icons.get(status, status.upper())

        console.print("\n[bold]Fitness / Fatigue / Form[/bold]\n")
        console.print(f"  Status: {status_display}\n")

        # CTL with 14-day change
        ctl_change = current["ctl_change"]
        ctl_arrow = "[green]▲[/green]" if ctl_change > 0 else "[red]▼[/red]" if ctl_change < 0 else "→"
        console.print(
            f"  Fitness (CTL):  {current['ctl']:6.1f}  "
            f"{ctl_arrow} {ctl_change:+.1f} from 14d ago"
        )
        console.print(f"  Fatigue (ATL):  {current['atl']:6.1f}")

        # TSB with freshness label
        tsb = current["tsb"]
        if tsb > 15:
            tsb_label = "(very fresh)"
        elif tsb > 5:
            tsb_label = "(fresh)"
        elif tsb > -10:
            tsb_label = "(neutral)"
        elif tsb > -20:
            tsb_label = "(tired)"
        else:
            tsb_label = "(very tired)"
        console.print(f"  Form (TSB):     {tsb:6.1f}  {tsb_label}")

        console.print(
            f"\n  Based on {meta['activities_with_hr']} activities with HR data "
            f"({meta['activities_without_hr']} skipped, no HR)"
        )
        console.print(f"  Max HR used: {meta['max_hr']} bpm (observed)")
        console.print(
            f"  Time range: {meta['time_range_start']} → {meta['time_range_end']}"
        )
        if meta.get("activity_type_filter"):
            console.print(f"  Activity type: {meta['activity_type_filter']}")

        # Warn if insufficient data
        if len(daily) < 7:
            console.print(
                "\n  [yellow]⚠ Less than 7 days of data — "
                "ATL may not be reliable.[/yellow]"
            )

        # Recent 14-day trend table
        if daily:
            console.print("\n[bold]Recent Trend (last 14 days)[/bold]")
            trend_table = Table(show_header=True, header_style="bold")
            trend_table.add_column("Date")
            trend_table.add_column("CTL", justify="right")
            trend_table.add_column("ATL", justify="right")
            trend_table.add_column("TSB", justify="right")

            for entry in daily[-14:]:
                tsb_val = entry["tsb"]
                tsb_style = (
                    "green" if tsb_val > 5 else "red" if tsb_val < -15 else ""
                )
                tsb_str = f"[{tsb_style}]{tsb_val:6.1f}[/{tsb_style}]" if tsb_style else f"{tsb_val:6.1f}"
                trend_table.add_row(
                    entry["date"],
                    f"{entry['ctl']:.1f}",
                    f"{entry['atl']:.1f}",
                    tsb_str,
                )

            console.print(trend_table)
    finally:
        session.close()
