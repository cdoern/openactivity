"""Garmin Connect health data sync — pulls daily wellness metrics via API."""

from __future__ import annotations

import time
from datetime import date, timedelta

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from openactivity.auth.keyring import get_garmin_credentials, has_garmin_credentials
from openactivity.db.database import get_session, init_db
from openactivity.db.models import GarminDailySummary

console = Console()

# Rate-limit: pause between per-day API calls to avoid Garmin throttling.
_REQUEST_DELAY_SECS = 1.5

# Token cache — uses ~/.garminconnect per library convention.
# First login saves tokens there; subsequent calls load + auto-refresh.
_TOKEN_STORE = "~/.garminconnect"


def _login_garmin():
    """Authenticate with Garmin Connect, caching tokens for reuse.

    Uses the garminconnect library's recommended auth flow:
    - First call: full SSO login, tokens saved to ~/.garminconnect
    - Subsequent calls: loads tokens from disk, auto-refreshes if expired
    - Supports MFA via interactive prompt
    """
    from garminconnect import Garmin

    username, password = get_garmin_credentials()
    if not username or not password:
        console.print(
            "[red]No Garmin credentials found.[/red] "
            "Run 'openactivity garmin login' first."
        )
        raise typer.Exit(code=1)

    client = Garmin(
        username,
        password,
        prompt_mfa=lambda: input("Enter MFA code: "),
    )

    try:
        client.login(_TOKEN_STORE)
    except Exception as exc:
        console.print(f"[red]Garmin login failed:[/red] {exc}")
        console.print(
            "Try 'openactivity garmin login' to re-enter your credentials."
        )
        raise typer.Exit(code=1)

    return client


def _safe_int(value, lo=None, hi=None) -> int | None:
    """Convert value to int if valid, clamping to constraint range."""
    if value is None:
        return None
    try:
        v = int(round(float(value)))
    except (ValueError, TypeError):
        return None
    if lo is not None and v < lo:
        return None
    if hi is not None and v > hi:
        return None
    return v


def _safe_float(value, lo=None, hi=None) -> float | None:
    """Convert value to float if valid, clamping to constraint range."""
    if value is None:
        return None
    try:
        v = float(value)
    except (ValueError, TypeError):
        return None
    if lo is not None and v < lo:
        return None
    if hi is not None and v > hi:
        return None
    return v


def _fetch_day(client, day: date) -> dict:
    """Fetch all health metrics for a single day. Returns a dict of fields.

    Makes up to 4 API calls per day (stats, hrv, sleep, stress).
    Body battery is fetched separately in batch.
    """
    date_str = day.isoformat()
    result: dict = {"date": day}

    # 1. Daily stats — resting HR, steps, respiration, SpO2
    try:
        stats = client.get_stats(date_str)
        if stats:
            result["resting_hr"] = _safe_int(
                stats.get("restingHeartRate"), lo=30, hi=200
            )
            result["steps"] = _safe_int(stats.get("totalSteps"), lo=0)
            result["respiration_avg"] = _safe_float(
                stats.get("averageRespirationValue"), lo=0, hi=60
            )
            result["spo2_avg"] = _safe_float(
                stats.get("averageSpo2"), lo=70, hi=100
            )
    except Exception:
        pass
    time.sleep(_REQUEST_DELAY_SECS)

    # 2. HRV
    try:
        hrv = client.get_hrv_data(date_str)
        if hrv:
            # The API nests HRV summary differently; try common paths
            summary = hrv.get("hrvSummary") or hrv
            avg = summary.get("weeklyAvg") or summary.get("lastNightAvg")
            if avg is None:
                # Some responses use lastNight5MinHigh
                avg = summary.get("lastNight5MinHigh")
            result["hrv_avg"] = _safe_int(avg, lo=0, hi=300)
    except Exception:
        pass
    time.sleep(_REQUEST_DELAY_SECS)

    # 3. Sleep
    try:
        sleep = client.get_sleep_data(date_str)
        if sleep:
            score = sleep.get("dailySleepDTO", {}).get("sleepScores", {}).get(
                "overall", {}
            ).get("value")
            if score is None:
                score = sleep.get("dailySleepDTO", {}).get("sleepScore")
            result["sleep_score"] = _safe_int(score, lo=0, hi=100)
    except Exception:
        pass
    time.sleep(_REQUEST_DELAY_SECS)

    # 4. Stress
    try:
        stress = client.get_stress_data(date_str)
        if stress:
            avg = stress.get("overallStressLevel")
            if avg is None:
                avg = stress.get("avgStressLevel")
            result["stress_avg"] = _safe_int(avg, lo=0, hi=100)
    except Exception:
        pass

    return result


def _fetch_body_battery_batch(
    client, start: date, end: date
) -> dict[date, tuple[int | None, int | None]]:
    """Fetch body battery for a date range in one API call.

    Returns {date: (max, min)} mapping.
    """
    try:
        data = client.get_body_battery(start.isoformat(), end.isoformat())
    except Exception:
        return {}

    if not data:
        return {}

    # Group by date and find min/max charged values per day
    from collections import defaultdict

    daily: dict[date, list[int]] = defaultdict(list)
    for entry in data:
        # entry may have 'date' or 'calendarDate' and 'charged' value
        ts = entry.get("date") or entry.get("calendarDate")
        val = entry.get("charged") or entry.get("bodyBatteryLevel")
        if ts is None or val is None:
            continue
        try:
            if isinstance(ts, str):
                day = date.fromisoformat(ts[:10])
            else:
                # epoch ms
                from datetime import datetime

                day = datetime.fromtimestamp(ts / 1000).date()
            daily[day].append(int(val))
        except (ValueError, TypeError):
            continue

    result = {}
    for day, values in daily.items():
        bb_max = _safe_int(max(values), lo=0, hi=100)
        bb_min = _safe_int(min(values), lo=0, hi=100)
        result[day] = (bb_max, bb_min)
    return result


def garmin_sync(
    days: int = typer.Option(
        14,
        "--days",
        help="Number of days to sync (default 14). More days = more API calls.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Re-sync days that already have data.",
    ),
) -> None:
    """Sync daily health metrics from Garmin Connect.

    Pulls HRV, sleep score, body battery, stress, resting HR, steps,
    respiration, and SpO2 from the Garmin Connect API into the local database.

    Rate-limited to ~1 request per 1.5 seconds to avoid throttling.

    Examples:
        openactivity garmin sync
        openactivity garmin sync --days 30
        openactivity garmin sync --days 90 --force
    """
    if not has_garmin_credentials():
        console.print(
            "[red]No Garmin credentials found.[/red] "
            "Run 'openactivity garmin login' first."
        )
        raise typer.Exit(code=1)

    init_db()
    session = get_session()

    try:
        # Determine date range
        end = date.today()
        start = end - timedelta(days=days - 1)

        # Check which days already have data
        if not force:
            existing = (
                session.query(GarminDailySummary.date)
                .filter(
                    GarminDailySummary.date >= start,
                    GarminDailySummary.date <= end,
                )
                .all()
            )
            existing_dates = {row[0] for row in existing}
        else:
            existing_dates = set()

        dates_to_sync = [
            start + timedelta(days=i)
            for i in range(days)
            if (start + timedelta(days=i)) not in existing_dates
        ]

        if not dates_to_sync:
            console.print("[green]All days already synced.[/green] Use --force to re-sync.")
            return

        console.print(f"Syncing {len(dates_to_sync)} days of health data from Garmin Connect...")
        console.print(
            f"[dim]Rate limited to ~{_REQUEST_DELAY_SECS}s between requests. "
            f"Estimated time: ~{len(dates_to_sync) * 4 * _REQUEST_DELAY_SECS / 60:.0f} min[/dim]"
        )

        # Login
        client = _login_garmin()

        # Batch fetch body battery (single API call for whole range)
        console.print("[dim]Fetching body battery data...[/dim]")
        bb_data = _fetch_body_battery_batch(client, dates_to_sync[0], dates_to_sync[-1])
        time.sleep(_REQUEST_DELAY_SECS)

        # Fetch per-day metrics with progress
        synced = 0
        skipped = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Syncing...", total=len(dates_to_sync))

            for day in dates_to_sync:
                progress.update(task, description=f"Syncing {day.isoformat()}...")

                data = _fetch_day(client, day)

                # Merge body battery
                if day in bb_data:
                    data["body_battery_max"], data["body_battery_min"] = bb_data[day]

                # Check if we got any actual data
                fields = [
                    "resting_hr", "hrv_avg", "body_battery_max",
                    "stress_avg", "sleep_score", "steps",
                    "respiration_avg", "spo2_avg",
                ]
                has_data = any(data.get(f) is not None for f in fields)

                if not has_data:
                    skipped += 1
                    progress.advance(task)
                    continue

                # Upsert
                existing = (
                    session.query(GarminDailySummary)
                    .filter_by(date=day)
                    .first()
                )
                if existing:
                    for f in fields:
                        if data.get(f) is not None:
                            setattr(existing, f, data[f])
                else:
                    row = GarminDailySummary(
                        date=day,
                        resting_hr=data.get("resting_hr"),
                        hrv_avg=data.get("hrv_avg"),
                        body_battery_max=data.get("body_battery_max"),
                        body_battery_min=data.get("body_battery_min"),
                        stress_avg=data.get("stress_avg"),
                        sleep_score=data.get("sleep_score"),
                        steps=data.get("steps"),
                        respiration_avg=data.get("respiration_avg"),
                        spo2_avg=data.get("spo2_avg"),
                    )
                    session.add(row)

                synced += 1
                progress.advance(task)

                # Extra delay between days to be safe
                time.sleep(_REQUEST_DELAY_SECS)

        session.commit()

        console.print(f"\n[green]Synced {synced} days of health data.[/green]")
        if skipped:
            console.print(f"[dim]Skipped {skipped} days with no data.[/dim]")

    finally:
        session.close()
