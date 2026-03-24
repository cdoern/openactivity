"""Garmin FIT file import CLI command."""

from __future__ import annotations

from pathlib import Path

import click
import typer
from rich.console import Console

from openactivity.db.database import get_session, init_db
from openactivity.providers.garmin import importer

console = Console()


def _import_from_device(session) -> importer.ImportResult:
    """Handle --from-device with USB mass storage and MTP fallback."""
    from rich.progress import Progress

    from openactivity.providers.garmin.mtp import (
        MTPError,
        detect_garmin_device,
        get_install_command,
        is_libmtp_available,
        list_activity_files,
    )

    # Try USB mass storage first (older devices)
    console.print("Looking for connected Garmin device...")
    mass_storage_path = importer.find_connected_device()
    if mass_storage_path:
        console.print(f"Found device at {mass_storage_path}")
        return importer.import_from_directory(session, mass_storage_path)

    # Check if MTP tools are available
    if not is_libmtp_available():
        # Check if a Garmin is connected via USB at all
        if importer.is_mtp_device_connected():
            console.print(
                "[yellow]Garmin device detected, but MTP tools are not installed.[/yellow]"
            )
            console.print()
            console.print("Newer Garmin watches (Forerunner 265/965, Fenix 7+, etc.) use MTP")
            console.print("to transfer files. Install MTP support with:")
            console.print()
            console.print(f"  [bold]{get_install_command()}[/bold]")
            console.print()
            console.print("Then re-run this command.")
        else:
            console.print("[yellow]No Garmin device found[/yellow]")
            console.print()
            console.print("[bold]Troubleshooting:[/bold]")
            console.print("  1. Connect your Garmin device via USB cable")
            console.print("  2. Quit Garmin Express if it's running")
            console.print("  3. Re-run this command")
        raise typer.Exit(1)

    # Try MTP
    device_info = detect_garmin_device()
    if not device_info:
        console.print("[yellow]No Garmin device found[/yellow]")
        console.print()
        console.print("[bold]Troubleshooting:[/bold]")
        console.print("  1. Connect your Garmin device via USB cable")
        console.print("  2. Quit Garmin Express (it grabs exclusive USB access)")
        console.print("  3. Re-run this command")
        raise typer.Exit(1)

    model = device_info.get("model", "Garmin device")
    console.print(f"Found [bold]{model}[/bold] via MTP")

    # List activity files
    console.print("Scanning device for activities...")
    try:
        activity_files = list_activity_files()
    except MTPError as e:
        console.print(f"[red]Error reading device: {e}[/red]")
        console.print("Try quitting Garmin Express and re-running.")
        raise typer.Exit(1) from None

    if not activity_files:
        console.print("[yellow]No activity files found on device[/yellow]")
        raise typer.Exit(1)

    console.print(f"Found {len(activity_files)} activities on device")
    console.print("Downloading FIT files from device...")

    # Download with progress bar
    import tempfile

    dest_dir = Path(tempfile.mkdtemp(prefix="garmin_activities_"))

    with Progress(console=console) as progress:
        task = progress.add_task("Downloading...", total=len(activity_files))

        def on_progress(current, total, filename):
            progress.update(task, completed=current, description=f"Downloading {filename}")

        from openactivity.providers.garmin.mtp import download_activity_files

        downloaded = download_activity_files(
            activity_files, dest_dir, progress_callback=on_progress,
        )

    console.print(f"Downloaded {downloaded} files from device")

    # Import the downloaded files
    console.print("Importing activities...")
    return importer.import_from_directory(session, dest_dir)


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

    init_db()
    session = get_session()

    try:
        # Import from device
        if from_device:
            result = _import_from_device(session)

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

            if zip_path.suffix.lower() != ".zip":
                console.print(f"[red]Error: File does not appear to be a ZIP: {from_zip}[/red]")
                console.print("Expected a .zip file from Garmin bulk export.")
                raise typer.Exit(1)

            console.print(f"Importing from ZIP: {zip_path.name}...")
            console.print("Extracting and parsing FIT files...")
            result = importer.import_from_zip(session, zip_path)

        # Import from custom directory
        elif from_directory:
            dir_path = Path(from_directory)
            if not dir_path.exists():
                console.print(f"[red]Error: Directory not found: {from_directory}[/red]")
                raise typer.Exit(1)

            if not dir_path.is_dir():
                console.print(f"[red]Error: Path is not a directory: {from_directory}[/red]")
                console.print("Use --from-zip for ZIP files.")
                raise typer.Exit(1)

            fit_files = importer.find_fit_files_in_directory(dir_path)
            console.print(f"Importing from directory: {dir_path}...")
            console.print(f"Found {len(fit_files)} FIT files to process...")
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

    except click.exceptions.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error during import: {e}[/red]")
        raise typer.Exit(1) from None
    finally:
        session.close()
