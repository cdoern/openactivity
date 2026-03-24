"""Strava sync command."""

from __future__ import annotations

import os
import sys
import time

import typer
from rich.console import Console

from openactivity.auth.keyring import has_tokens
from openactivity.cli.root import get_global_state
from openactivity.db.database import get_session, init_db
from openactivity.output.errors import exit_with_error
from openactivity.output.json import print_json
from openactivity.providers.strava.sync import sync_activities, sync_athlete, sync_segments

console = Console()

app = typer.Typer(name="sync")

_LOG_DIR = os.path.expanduser("~/.local/share/openactivity")
_LOG_FILE = os.path.join(_LOG_DIR, "sync.log")


def _run_sync(*, full: bool, detail: bool, use_json: bool) -> dict:
    """Run the actual sync. Returns result dict."""
    init_db()
    session = get_session()

    start = time.monotonic()

    try:
        if not use_json:
            console.print("Syncing athlete profile...")
        athlete_id = sync_athlete(session)

        result = sync_activities(session, athlete_id, full=full, detail=detail)
    finally:
        session.close()

    elapsed = int(time.monotonic() - start)
    result["duration_seconds"] = elapsed
    return result


@app.callback(invoke_without_command=True)
def sync(
    ctx: typer.Context,
    full: bool = typer.Option(False, "--full", help="Re-sync all data (ignore last sync time)."),
    detail: bool = typer.Option(
        True,
        "--detail/--no-detail",
        help="Fetch detailed data (streams, laps, zones).",
    ),
    background: bool = typer.Option(
        False,
        "--background",
        help="Run sync in the background and return immediately.",
    ),
) -> None:
    """Sync activity data from Strava to local storage.

    By default, only fetches new or updated activities since last sync.
    Use --full to re-sync everything. Use --no-detail to skip streams,
    laps, and zones for faster sync. Use --background to run in the
    background while you use other commands.

    Examples:
        openactivity strava sync
        openactivity strava sync --full
        openactivity strava sync --no-detail
        openactivity strava sync --background
    """
    if ctx.invoked_subcommand is not None:
        return

    state = get_global_state()
    use_json = state.get("json", False)

    if not has_tokens():
        exit_with_error(
            "authentication_required",
            "No stored credentials found for Strava.",
            "Run 'openactivity strava auth' to connect your account.",
            use_json=use_json,
        )

    if background:
        _start_background_sync(full=full, detail=detail, use_json=use_json)
        return

    try:
        result = _run_sync(full=full, detail=detail, use_json=use_json)
    except RuntimeError as e:
        exit_with_error(
            "sync_error",
            f"Sync failed: {e}",
            "Check your credentials with 'openactivity strava auth'.",
            use_json=use_json,
        )
    except Exception as e:
        exit_with_error(
            "sync_error",
            f"Sync failed: {e}",
            "Try again or run with --no-detail for a faster sync.",
            use_json=use_json,
        )

    if use_json:
        print_json(result)
    else:
        console.print(
            f"[green]✓[/green] Synced {result['synced']} activities "
            f"({result['new']} new, {result['updated']} updated)"
        )
        if result["errors"]:
            console.print(f"  [yellow]{result['errors']} errors[/yellow]")
        console.print(f"  Last sync: {result['last_sync']}")
        if result.get("link_linked", 0) > 0 or result.get("link_checked", 0) > 0:
            console.print(
                f"  Cross-provider linking: {result['link_linked']} of "
                f"{result['link_checked']} new activities matched to Garmin"
            )


def _start_background_sync(*, full: bool, detail: bool, use_json: bool) -> None:
    """Fork a background process for sync."""
    os.makedirs(_LOG_DIR, exist_ok=True)

    pid = os.fork()
    if pid > 0:
        # Parent — report and exit
        if use_json:
            print_json(
                {
                    "status": "started",
                    "pid": pid,
                    "log": _LOG_FILE,
                }
            )
        else:
            console.print(f"[green]✓[/green] Sync started in background (PID {pid})")
            console.print(f"  Log: {_LOG_FILE}")
            console.print("  You can use other commands while sync runs.")
        return

    # Child — detach and run sync
    os.setsid()

    with open(_LOG_FILE, "a") as log:
        # Redirect stdout/stderr to log file
        os.dup2(log.fileno(), sys.stdout.fileno())
        os.dup2(log.fileno(), sys.stderr.fileno())

        log.write(f"\n--- Sync started at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        log.flush()

        try:
            result = _run_sync(full=full, detail=detail, use_json=False)
            log.write(
                f"Synced {result['synced']} activities "
                f"({result['new']} new, {result['updated']} updated) "
                f"in {result['duration_seconds']}s\n"
            )
        except Exception as e:
            log.write(f"Sync failed: {e}\n")

        log.write(f"--- Sync finished at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")

    os._exit(0)


@app.command("segments")
def sync_segments_command() -> None:
    """Sync only starred segments and their efforts.

    Much faster than full sync - only fetches your starred segments
    from Strava without re-syncing all activities.

    Examples:
        openactivity strava sync segments
        openactivity strava sync segments --json
    """
    state = get_global_state()
    use_json = state.get("json", False)

    if not has_tokens():
        exit_with_error(
            "authentication_required",
            "No stored credentials found for Strava.",
            "Run 'openactivity strava auth' to connect your account.",
            use_json=use_json,
        )

    init_db()
    session = get_session()

    try:
        if not use_json:
            console.print("Syncing starred segments...")

        result = sync_segments(session)

        if use_json:
            print_json(result)
        else:
            console.print(
                f"[green]✓[/green] Synced {result['segments']} starred segments "
                f"with {result['efforts']} total efforts"
            )
    except Exception as e:
        exit_with_error(
            "sync_error",
            f"Segment sync failed: {e}",
            "Check your credentials with 'openactivity strava auth'.",
            use_json=use_json,
        )
    finally:
        session.close()
