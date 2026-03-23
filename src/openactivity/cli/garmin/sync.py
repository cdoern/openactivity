"""Garmin Connect sync CLI command."""

from __future__ import annotations

import typer
from rich.console import Console

from openactivity.db.database import get_session
from openactivity.providers.garmin import auth
from openactivity.providers.garmin.sync import sync_all

console = Console()


def garmin_sync(
    full: bool = typer.Option(False, "--full", help="Full sync (ignore last sync time)"),
    activities_only: bool = typer.Option(False, "--activities-only", help="Sync only activities"),
    health_only: bool = typer.Option(False, "--health-only", help="Sync only health data"),
) -> None:
    """Sync activities and health data from Garmin Connect.

    By default, performs incremental sync (only new data since last sync).
    Use --full to re-sync all data.
    """
    # Check authentication
    if not auth.is_authenticated():
        console.print("[red]Error: Not authenticated with Garmin Connect[/red]")
        console.print("Run 'openactivity garmin auth' first.")
        raise typer.Exit(1)

    # Get authenticated client
    client, error = auth.get_authenticated_client()
    if not client:
        console.print("[red]Error: Failed to authenticate with stored credentials[/red]")

        if error == "rate_limit":
            console.print("\n[yellow]⚠ Rate Limit Exceeded[/yellow]")
            console.print("Garmin is temporarily blocking requests. Wait 15-30 minutes and try again.")
        elif error == "no_credentials":
            console.print("Run 'openactivity garmin auth' to authenticate.")
        else:
            console.print("Run 'openactivity garmin auth' to re-authenticate.")

        raise typer.Exit(1)

    # Warning for full sync
    if full:
        console.print("[yellow]Warning: Full sync will re-download all data from Garmin Connect[/yellow]")
        console.print("This may take several minutes.")
        proceed = typer.confirm("Continue?", default=True)
        if not proceed:
            console.print("Sync cancelled")
            return

    # Perform sync
    console.print("Syncing from Garmin Connect...\n")

    session = get_session()
    try:
        result = sync_all(
            session,
            client,
            full=full,
            activities_only=activities_only,
            health_only=health_only,
        )

        # Display results
        if not health_only:
            console.print("[bold]Syncing activities...[/bold]")
            console.print(f"  ✓ Fetched {result.activities_new} new activities")
            if result.activities_updated > 0:
                console.print(f"  ✓ Updated {result.activities_updated} existing activities")
            if result.duplicates_detected > 0:
                console.print(f"  ✓ Linked {result.duplicates_detected} duplicate activities with Strava")
            if result.activities_errors > 0:
                console.print(f"  ⚠ {result.activities_errors} activities had errors")
            console.print()

        if not activities_only:
            console.print("[bold]Syncing health data...[/bold]")
            console.print(f"  ✓ Synced daily summaries for {result.health_daily_summaries} days")
            console.print(f"  ✓ Synced {result.health_sleep_sessions} sleep sessions")
            console.print()

        console.print("[green]Sync complete[/green]")
        console.print(f"  Duration: {int(result.duration_seconds)} seconds")

        if not health_only:
            console.print(f"  Activities: {result.activities_new} new, {result.activities_updated} updated")
        if not activities_only:
            console.print(f"  Health days: {result.health_daily_summaries}")
        if result.duplicates_detected > 0:
            console.print(f"  Duplicates detected: {result.duplicates_detected}")

    except Exception as e:
        console.print(f"[red]Error: Sync failed[/red]")
        console.print(f"{e}")
        raise typer.Exit(1)
    finally:
        session.close()
