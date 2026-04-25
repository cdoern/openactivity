"""Strava-specific analyze commands — thin alias over top-level analyze.

All commands delegate to the unified ``openactivity analyze`` commands
with ``--provider strava`` applied implicitly.
"""

from __future__ import annotations

import typer

from openactivity.cli import analyze as _analyze

app = typer.Typer(
    name="analyze",
    help=(
        "Analyze performance trends from Strava data.\n\n"
        "These are aliases for 'openactivity analyze' with --provider strava.\n\n"
        "Examples:\n\n"
        "  openactivity strava analyze summary\n"
        "  openactivity strava analyze pace --last 90d\n"
    ),
    no_args_is_help=True,
)


# ── Thin wrappers — delegate to top-level commands with provider="strava" ──


@app.command("summary")
def analyze_summary(
    period: str = typer.Option("weekly", "--period", help='Aggregation period.'),
    last: str = typer.Option("90d", "--last", help='Time window.'),
    activity_type: str | None = typer.Option(None, "--type", help='Activity type filter.'),
) -> None:
    """Training volume summary (Strava only)."""
    _analyze.analyze_summary(period=period, last=last, activity_type=activity_type, provider="strava")


@app.command("pace")
def analyze_pace(
    last: str = typer.Option("90d", "--last", help='Time window.'),
    activity_type: str = typer.Option("Run", "--type", help='Activity type.'),
) -> None:
    """Pace trend analysis (Strava only)."""
    _analyze.analyze_pace(last=last, activity_type=activity_type, provider="strava")


@app.command("zones")
def analyze_zones(
    zone_type: str = typer.Option("heartrate", "--zone-type", help='"heartrate" or "power".'),
    activity_type: str | None = typer.Option(None, "--type", help="Activity type filter."),
    last: str = typer.Option("all", "--last", help='Time window.'),
) -> None:
    """Zone distribution (Strava only)."""
    _analyze.analyze_zones(zone_type=zone_type, activity_type=activity_type, last=last)


@app.command("power-curve")
def analyze_power_curve(
    last: str = typer.Option("90d", "--last", help='Time window.'),
) -> None:
    """Power curve (Strava only)."""
    _analyze.analyze_power_curve(last=last)


@app.command("compare")
def analyze_compare(
    range1: str = typer.Option(..., "--range1", help="First date range (YYYY-MM-DD:YYYY-MM-DD)."),
    range2: str = typer.Option(..., "--range2", help="Second date range (YYYY-MM-DD:YYYY-MM-DD)."),
    activity_type: str | None = typer.Option(None, "--type", help='Activity type filter.'),
) -> None:
    """Compare two date ranges (Strava only)."""
    _analyze.analyze_compare(range1=range1, range2=range2, activity_type=activity_type, provider="strava")


@app.command("effort")
def analyze_effort(
    last: str = typer.Option("90d", "--last", help='Time window.'),
    activity_type: str = typer.Option("Run", "--type", help='Activity type.'),
) -> None:
    """Effort trend (Strava only)."""
    _analyze.analyze_effort(last=last, activity_type=activity_type, provider="strava")


@app.command("blocks")
def analyze_blocks(
    last: str = typer.Option("6m", "--last", help='Time window.'),
    activity_type: str = typer.Option("Run", "--type", help='Activity type.'),
) -> None:
    """Training blocks (Strava only)."""
    _analyze.analyze_blocks(last=last, activity_type=activity_type, provider="strava")


@app.command("correlate")
def analyze_correlate(
    x_metric: str = typer.Option(..., "--x", help="X-axis metric."),
    y_metric: str = typer.Option(..., "--y", help="Y-axis metric."),
    lag: int = typer.Option(0, "--lag", help="Lag offset in weeks."),
    last: str = typer.Option("1y", "--last", help='Time window.'),
    activity_type: str = typer.Option("Run", "--type", help='Activity type.'),
) -> None:
    """Correlate two metrics (Strava only)."""
    _analyze.analyze_correlate(
        x_metric=x_metric, y_metric=y_metric, lag=lag, last=last,
        activity_type=activity_type, provider="strava",
    )


@app.command("fitness")
def analyze_fitness_cmd(
    last: str = typer.Option("6m", "--last", help='Time range.'),
    activity_type: str | None = typer.Option(None, "--type", help='Activity type filter.'),
    chart: bool = typer.Option(False, "--chart", help="Generate fitness chart."),
    output: str = typer.Option("fitness_chart.png", "--output", help="Chart output path."),
) -> None:
    """Fitness / Fatigue / Form (Strava only)."""
    _analyze.analyze_fitness_cmd(
        last=last, activity_type=activity_type, chart=chart, output=output, provider="strava",
    )


@app.command("readiness")
def analyze_readiness(
    last: str | None = typer.Option(None, "--last", help='Time window for trend.'),
) -> None:
    """Daily recovery & readiness score (Strava only)."""
    _analyze.analyze_readiness(last=last, provider="strava")
