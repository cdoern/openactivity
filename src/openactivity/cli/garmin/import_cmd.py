"""Garmin FIT file import CLI command."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from openactivity.db.database import get_session
from openactivity.providers.garmin import importer

console = Console()


def garmin_import(
    from_device: bool = typer.Option(
        False,
        "--from-device",
        help="Import from connected Garmin device",
    ),
    from_connect: bool = typer.Option(
        False,
        "--from-connect",
        help="Import from Garmin Connect local folder",
    ),
    from_zip: str | None = typer.Option(
        None,
        "--from-zip",
        help="Import from Garmin bulk export ZIP file",
    ),
    from_directory: str | None = typer.Option(
        None,
        "--from-directory",
        help="Import from custom directory containing FIT files",
    ),
) -> None:
    """Import activities from Garmin FIT files.

    Supports multiple import sources:
    - Connected Garmin device (--from-device)
    - Garmin Connect local folder (--from-connect)
    - Garmin bulk export ZIP (--from-zip PATH)
    - Custom directory (--from-directory PATH)

    FIT files contain activity data (GPS, HR, power, etc.) but NOT
    advanced health metrics (HRV, Body Battery, detailed sleep).
    For health data, use Garmin's bulk export and import the CSVs separately.
    """
    # Check that at least one source is specified
    sources = [from_device, from_connect, from_zip is not None, from_directory is not None]
    if not any(sources):
        console.print("[red]Error: No import source specified[/red]")
        console.print()
        console.print("[bold]Available options:[/bold]")
        console.print("  --from-device          Import from connected Garmin device")
        console.print("  --from-connect         Import from Garmin Connect local folder")
        console.print("  --from-zip PATH        Import from bulk export ZIP")
        console.print("  --from-directory PATH  Import from custom directory")
        console.print()
        console.print("Example:")
        console.print("  openactivity garmin import --from-device")
        raise typer.Exit(1)

    # Check that only one source is specified
    if sum(sources) > 1:
        console.print("[red]Error: Multiple import sources specified[/red]")
        console.print("Please specify only one source at a time.")
        raise typer.Exit(1)

    console.print("[bold]Garmin FIT File Import[/bold]\n")

    session = get_session()

    try:
        # Import from device
        if from_device:
            console.print("Looking for connected Garmin device...")
            result = importer.import_from_device(session)

            if result is None:
                console.print("[yellow]⚠ No Garmin device found[/yellow]")
                console.print()
                console.print("[bold]Troubleshooting:[/bold]")
                console.print("  1. Connect your Garmin device via USB")
                console.print("  2. Make sure it's mounted/accessible")
                console.print("  3. Check that the device appears in file manager")
                console.print()
                console.print("Common mount points:")
                console.print("  Linux:   /media/GARMIN/")
                console.print("  macOS:   /Volumes/GARMIN/")
                console.print("  Windows: D:/ or E:/")
                raise typer.Exit(1)

        # Import from Garmin Connect folder
        elif from_connect:
            console.print("Looking for Garmin Connect local folder...")
            result = importer.import_from_garmin_connect(session)

            if result is None:
                console.print("[yellow]⚠ Garmin Connect folder not found[/yellow]")
                console.print()
                console.print("[bold]This folder is created when you:[/bold]")
                console.print("  1. Install Garmin Express (desktop app)")
                console.print("  2. Sync your device using Garmin Express")
                console.print()
                console.print("Common locations:")
                console.print("  macOS:   ~/Library/Application Support/Garmin/GarminConnect/")
                console.print("  Windows: %LOCALAPPDATA%\\Garmin\\GarminConnect\\")
                console.print()
                console.print("Alternative: Use --from-device instead")
                raise typer.Exit(1)

        # Import from ZIP
        elif from_zip:
            zip_path = Path(from_zip)
            if not zip_path.exists():
                console.print(f"[red]Error: ZIP file not found: {from_zip}[/red]")
                raise typer.Exit(1)

            console.print(f"Importing from ZIP: {zip_path.name}...")
            result = importer.import_from_zip(session, zip_path)

        # Import from custom directory
        elif from_directory:
            dir_path = Path(from_directory)
            if not dir_path.exists():
                console.print(f"[red]Error: Directory not found: {from_directory}[/red]")
                raise typer.Exit(1)

            console.print(f"Importing from directory: {dir_path}...")
            result = importer.import_from_directory(session, dir_path)

        # Display results
        console.print()
        console.print("[green]✓ Import complete[/green]")
        console.print()
        console.print(f"  Files processed: {result.files_processed}")
        console.print(f"  Activities imported: {result.activities_imported}")
        console.print(f"  Activities skipped (already imported): {result.activities_skipped}")
        if result.activities_errors > 0:
            console.print(f"  Errors: {result.activities_errors}")

        if result.activities_imported == 0 and result.activities_skipped == 0:
            console.print()
            console.print("[yellow]⚠ No FIT files found[/yellow]")
            console.print("Make sure FIT files exist in the specified location.")

    except Exception as e:
        console.print(f"[red]Error during import: {e}[/red]")
        raise typer.Exit(1)
    finally:
        session.close()
