"""Unified race prediction CLI command — provider-agnostic."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from openactivity.cli.root import get_global_state
from openactivity.db.database import get_session, init_db
from openactivity.output.json import print_json
from openactivity.output.units import format_duration, format_speed_as_pace

console = Console()

app = typer.Typer(
    name="predict",
    help=(
        "Predict race times and assess readiness.\n\n"
        "Uses the Riegel formula with your personal records to predict\n"
        "finish times at target distances. Includes a readiness score\n"
        "(0-100) based on training consistency, volume, taper, and PR\n"
        "recency.\n\n"
        "Supported distances: 1mi, 5K, 10K, half, marathon\n\n"
        "Examples:\n\n"
        "  openactivity predict --distance 10K\n"
        "  openactivity predict --distance half --provider strava\n"
        "  openactivity predict --distance marathon --race-date 2026-06-15\n"
        "  openactivity --json predict --distance 5K\n"
    ),
    invoke_without_command=True,
)


def _bar(score: int, width: int = 10) -> str:
    """Render a simple bar chart."""
    filled = round(score / 100 * width)
    return "\u2588" * filled + "\u2591" * (width - filled)


def _format_time(seconds: float) -> str:
    """Format seconds to human-readable time."""
    return format_duration(int(seconds))


def _pace_from_seconds_per_km(seconds_per_km: float, units: str) -> str:
    """Convert seconds/km to m/s then format as pace."""
    if seconds_per_km <= 0:
        return "N/A"
    m_per_s = 1000.0 / seconds_per_km
    return format_speed_as_pace(m_per_s, units)


@app.callback(invoke_without_command=True)
def predict_race(
    distance: str = typer.Option(
        ...,
        "--distance",
        help='Target distance: 1mi, 5K, 10K, half, marathon.',
    ),
    race_date: str | None = typer.Option(
        None,
        "--race-date",
        help="Race date (YYYY-MM-DD) for countdown and phase context.",
    ),
    activity_type: str = typer.Option(
        "Run",
        "--type",
        help='Activity type filter (e.g., "Run").',
    ),
    provider: str | None = typer.Option(
        None,
        "--provider",
        help='Filter by provider (e.g., "strava", "garmin"). Default: all.',
    ),
) -> None:
    """Predict race time and assess readiness.

    Uses the Riegel formula from your personal records to predict
    finish times. Shows a readiness score based on recent training.

    Supported distances: 1mi, 5K, 10K, half, marathon
    """
    state = get_global_state()
    use_json = state.get("json", False)
    units = state.get("units", "metric")

    init_db()
    session = get_session()

    try:
        from openactivity.analysis.predict import predict

        result = predict(
            session,
            target_distance=distance,
            activity_type=activity_type,
            race_date=race_date,
            provider=provider,
        )

        if use_json:
            _render_json(result)
        elif "error" in result:
            _render_error(result)
        else:
            _render_human(result, units)
    finally:
        session.close()


def _render_error(result: dict) -> None:
    """Render error output."""
    console.print()
    console.print(f"[bold red]{result.get('message', 'Unknown error')}[/bold red]")

    if result.get("error") == "insufficient_data":
        efforts = result.get("efforts_found", 0)
        console.print(f"\n  Efforts found: {efforts}")
        console.print(
            "\n  Tip: Run `openactivity records scan` to detect PRs,"
        )
        console.print("  then try again.")

    if result.get("error") == "invalid_distance":
        console.print("\n  Supported: 1mi, 5K, 10K, half, marathon")

    console.print()


def _render_human(result: dict, units: str) -> None:
    """Render human-readable prediction output."""
    pred = result["prediction"]
    target = result["target_distance_display"]

    console.print()
    console.print(f"[bold]Race Prediction: {target}[/bold]")
    console.print()

    # Prediction
    console.print(
        f"  Predicted Time:  [bold green]{_format_time(pred['predicted_time'])}[/bold green]"
    )
    console.print(
        f"  Predicted Pace:  {_pace_from_seconds_per_km(pred['predicted_pace'], units)}"
    )
    console.print(
        f"  Confidence:      {_format_time(pred['confidence_low'])} — "
        f"{_format_time(pred['confidence_high'])} "
        f"(±{pred['confidence_pct']}%)"
    )

    # Show existing PR if available
    if result.get("target_pr"):
        pr = result["target_pr"]
        console.print(
            f"  Your PR:         {_format_time(pr['time_seconds'])} "
            f"({pr['days_ago']}d ago)"
        )

    # Reference efforts table
    efforts = pred.get("reference_efforts", [])
    if efforts:
        console.print()
        console.print("[bold]Reference Efforts:[/bold]")

        table = Table(show_header=True, box=None, padding=(0, 2))
        table.add_column("Distance", style="cyan")
        table.add_column("Time", justify="right")
        table.add_column("Date")
        table.add_column("Age", justify="right", style="dim")

        for e in efforts:
            table.add_row(
                e.get("distance_display", e["distance_label"]),
                _format_time(e["time_seconds"]),
                e["activity_date"].strftime("%Y-%m-%d") if e.get("activity_date") else "—",
                f"{e['days_ago']}d ago",
            )
        console.print(table)

    # Readiness score
    readiness = result.get("readiness")
    if readiness:
        console.print()
        overall = readiness["overall"]
        label = readiness["label"]

        style = "green" if overall >= 80 else "yellow" if overall >= 60 else "red"
        console.print(
            f"[bold]Readiness Score: [{style}]{overall}/100 — {label}[/{style}][/bold]"
        )
        console.print()

        components = readiness["components"]
        for name, comp in components.items():
            display_name = name.replace("_", " ").title()
            bar = _bar(comp["score"])
            console.print(
                f"  {display_name:<16} {bar}  {comp['score']:>3}  "
                f"({comp['description']})"
            )
    else:
        console.print()
        console.print(
            "[dim]Readiness score unavailable — need 4+ weeks of training data.[/dim]"
        )

    # Race date context
    if result.get("days_until_race") is not None:
        console.print()
        console.print(
            f"[bold]Race Date:[/bold] {result['race_date']} "
            f"({result['days_until_race']} days away)"
        )
        phase = result.get("current_phase", "unknown")
        phase_desc = result.get("current_phase_description", "")
        console.print(f"  Training Phase: {phase.title()} — {phase_desc}")

        days = result["days_until_race"]
        if days <= 14:
            console.print("  [green]Final taper period — maintain intensity, reduce volume[/green]")
        elif days <= 28:
            console.print("  [yellow]Consider beginning taper — reduce volume 20-30%[/yellow]")
        elif days <= 42:
            console.print("  [cyan]Peak training window — last chance for key workouts[/cyan]")

    # Current phase (when no race date)
    elif result.get("current_phase") and result["current_phase"] != "unknown":
        console.print()
        phase = result["current_phase"]
        desc = result.get("current_phase_description", "")
        console.print(f"[dim]Current Phase: {phase.title()} — {desc}[/dim]")

    console.print()


def _render_json(result: dict) -> None:
    """Render JSON output."""
    output = {}

    if "error" in result:
        output = {
            "error": result["error"],
            "message": result["message"],
            "target_distance": result.get("target_distance"),
            "efforts_found": result.get("efforts_found", 0),
        }
    else:
        pred = result["prediction"]
        output = {
            "target_distance": result["target_distance"],
            "target_distance_meters": result["target_distance_meters"],
            "activity_type": result["activity_type"],
            "prediction": {
                "predicted_time_seconds": round(pred["predicted_time"], 1),
                "predicted_time_formatted": _format_time(pred["predicted_time"]),
                "predicted_pace_seconds": round(pred["predicted_pace"], 1),
                "confidence_low_seconds": round(pred["confidence_low"], 1),
                "confidence_high_seconds": round(pred["confidence_high"], 1),
                "confidence_low_formatted": _format_time(pred["confidence_low"]),
                "confidence_high_formatted": _format_time(pred["confidence_high"]),
                "confidence_pct": pred["confidence_pct"],
                "prediction_source": pred["prediction_source"],
            },
            "reference_efforts": [
                {
                    "distance_label": e["distance_label"],
                    "distance_meters": e["distance_meters"],
                    "time_seconds": e["time_seconds"],
                    "time_formatted": _format_time(e["time_seconds"]),
                    "activity_date": (
                        e["activity_date"].strftime("%Y-%m-%d")
                        if e.get("activity_date")
                        else None
                    ),
                    "days_ago": e["days_ago"],
                }
                for e in pred.get("reference_efforts", [])
            ],
        }

        if result.get("readiness"):
            r = result["readiness"]
            output["readiness"] = {
                "overall": r["overall"],
                "label": r["label"],
                "components": {
                    name: {
                        "score": comp["score"],
                        "weight": comp["weight"],
                        "description": comp["description"],
                    }
                    for name, comp in r["components"].items()
                },
            }

        if result.get("target_pr"):
            pr = result["target_pr"]
            output["target_pr"] = {
                "time_seconds": pr["time_seconds"],
                "time_formatted": _format_time(pr["time_seconds"]),
                "days_ago": pr["days_ago"],
            }

        if result.get("race_date"):
            output["race_date"] = result["race_date"]
            output["days_until_race"] = result["days_until_race"]

        output["current_phase"] = result.get("current_phase")
        output["current_phase_description"] = result.get("current_phase_description")

    print_json(output)
