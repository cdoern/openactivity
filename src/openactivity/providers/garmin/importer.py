"""Garmin FIT file importer - finds and imports activities from various sources."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

from openactivity.db.models import Activity
from openactivity.providers.garmin.fit_parser import parse_fit_file

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class ImportResult:
    """Result of an import operation."""

    def __init__(self):
        self.activities_imported = 0
        self.activities_skipped = 0
        self.activities_errors = 0
        self.files_processed = 0
        self.activities_linked = 0
        self.activities_link_checked = 0


def get_imported_filenames(session: Session) -> set[str]:
    """Return the set of source_filenames already imported for Garmin."""
    rows = (
        session.query(Activity.source_filename)
        .filter(Activity.provider == "garmin", Activity.source_filename.isnot(None))
        .all()
    )
    return {r[0] for r in rows}


def filter_new_activity_files(
    session: Session, file_list: list[dict],
) -> list[dict]:
    """Filter an MTP file list to only files not already imported."""
    imported = get_imported_filenames(session)
    return [f for f in file_list if f.get("filename", "") not in imported]


def find_fit_files_in_directory(directory: Path) -> list[Path]:
    """Find all FIT files in a directory recursively.

    Args:
        directory: Directory to search

    Returns:
        List of paths to .fit files
    """
    if not directory.exists():
        return []

    return list(directory.rglob("*.fit")) + list(directory.rglob("*.FIT"))


def find_garmin_connect_directory() -> Path | None:
    """Find the Garmin Connect data directory on this system.

    Returns:
        Path to Garmin Connect directory, or None if not found
    """
    # Common locations for Garmin Connect data
    possible_paths = [
        # macOS
        Path.home() / "Library" / "Application Support" / "Garmin" / "GarminConnect",
        # Windows
        Path.home() / "AppData" / "Local" / "Garmin" / "GarminConnect",
        Path.home() / "AppData" / "Roaming" / "Garmin" / "GarminConnect",
        # Linux (if using Wine or similar)
        Path.home()
        / ".wine" / "drive_c" / "Users" / "Public" / "Documents" / "Garmin" / "GarminConnect",
    ]

    for path in possible_paths:
        if path.exists():
            return path

    return None


def find_connected_device() -> Path | None:
    """Find a connected Garmin device mounted as USB mass storage.

    Note: Newer Garmin devices (Forerunner 965, Fenix 7+, etc.) use MTP
    instead of USB mass storage and will NOT appear as a mounted volume.
    For MTP devices, use --from-zip with a Garmin Connect bulk export.

    Returns:
        Path to device's Activity directory, or None if not found
    """
    import platform

    possible_paths = []

    if platform.system() == "Darwin":
        # macOS: check /Volumes for any Garmin-like mount
        volumes = Path("/Volumes")
        if volumes.exists():
            for vol in volumes.iterdir():
                garmin_dir = vol / "Garmin" / "Activities"
                if garmin_dir.exists():
                    return garmin_dir
                # Some devices mount with Activities at root
                garmin_dir = vol / "Activities"
                if garmin_dir.exists():
                    return garmin_dir
        # Standard path
        possible_paths.append(Path("/Volumes") / "GARMIN" / "Garmin" / "Activities")
    elif platform.system() == "Linux":
        # Linux: check common mount points
        for base in [Path("/media"), Path("/run/media") / Path.home().name]:
            if base.exists():
                for mount in base.iterdir():
                    garmin_dir = mount / "Garmin" / "Activities"
                    if garmin_dir.exists():
                        return garmin_dir
        possible_paths.extend([
            Path("/media") / "GARMIN" / "Garmin" / "Activities",
            Path("/run/media") / Path.home().name / "GARMIN" / "Garmin" / "Activities",
        ])
    else:
        # Windows
        for drive in "DEFGH":
            possible_paths.append(Path(f"{drive}:/Garmin/Activities"))

    for path in possible_paths:
        if path.exists():
            return path

    return None


def is_mtp_device_connected() -> bool:
    """Check if a Garmin device is connected via MTP (not mass storage).

    Newer Garmin watches use MTP and are grabbed by Garmin Express.
    Returns True if we detect a Garmin MTP device.
    """
    import platform
    import subprocess

    if platform.system() == "Darwin":
        try:
            result = subprocess.run(
                ["ioreg", "-p", "IOUSB", "-l"],
                capture_output=True, text=True, timeout=5,
            )
            # Garmin Express grabs the device as exclusive owner
            if "Garmin" in result.stdout:
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
    elif platform.system() == "Linux":
        try:
            result = subprocess.run(
                ["lsusb"], capture_output=True, text=True, timeout=5,
            )
            # Garmin vendor ID is 091e
            if "091e" in result.stdout.lower() or "garmin" in result.stdout.lower():
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    return False


def import_from_directory(
    session: Session,
    directory: Path,
    athlete_id: int = 1,
) -> ImportResult:
    """Import all FIT files from a directory.

    Args:
        session: Database session
        directory: Directory containing FIT files
        athlete_id: Athlete ID to assign to activities

    Returns:
        ImportResult with statistics
    """
    result = ImportResult()
    new_activities = []

    fit_files = find_fit_files_in_directory(directory)

    # Bulk-load already-imported filenames and provider_ids to skip without parsing
    imported_filenames = get_imported_filenames(session)
    existing_provider_ids = {
        r[0]
        for r in session.query(Activity.provider_id).filter_by(provider="garmin").all()
        if r[0] is not None
    }

    for fit_file in fit_files:
        if fit_file.name in imported_filenames:
            result.activities_skipped += 1
            continue

        result.files_processed += 1

        try:
            # Parse FIT file
            activity_data = parse_fit_file(fit_file)

            if not activity_data:
                result.activities_skipped += 1
                continue

            # Check if already imported (handles files with different names but same activity)
            provider_id = activity_data["provider_id"]
            if provider_id in existing_provider_ids:
                # Backfill source_filename on the existing row so future runs skip by filename
                existing = (
                    session.query(Activity)
                    .filter_by(provider="garmin", provider_id=provider_id)
                    .first()
                )
                if existing and not existing.source_filename:
                    existing.source_filename = fit_file.name
                result.activities_skipped += 1
                continue

            # Create new activity
            activity_data["athlete_id"] = athlete_id
            activity_data["source_filename"] = fit_file.name
            new_activity = Activity(**activity_data)
            session.add(new_activity)
            new_activities.append(new_activity)
            result.activities_imported += 1

        except Exception:
            result.activities_errors += 1
            continue

    session.commit()

    # Auto-link new activities against other providers
    if new_activities:
        from openactivity.db.queries import auto_link_new_activities

        link_stats = auto_link_new_activities(session, new_activities)
        result.activities_linked = link_stats["linked"]
        result.activities_link_checked = link_stats["checked"]

    return result


def import_from_device(
    session: Session,
    athlete_id: int = 1,
    *,
    progress_callback: callable | None = None,
) -> ImportResult | None:
    """Import FIT files from a connected Garmin device.

    First tries USB mass storage mount, then falls back to MTP protocol.

    Args:
        session: Database session
        athlete_id: Athlete ID to assign to activities
        progress_callback: Optional callback for MTP download progress

    Returns:
        ImportResult with statistics, or None if no device found
    """
    # Try USB mass storage first (older devices)
    device_path = find_connected_device()
    if device_path:
        return import_from_directory(session, device_path, athlete_id)

    # Try MTP (newer devices like FR 965, Fenix 7+)
    from openactivity.providers.garmin.mtp import (
        MTPError,
        download_all_activities,
        is_libmtp_available,
    )

    if not is_libmtp_available():
        return None  # Caller handles messaging

    try:
        download_dir = download_all_activities(progress_callback=progress_callback)
        return import_from_directory(session, download_dir, athlete_id)
    except MTPError:
        return None


def import_from_garmin_connect(
    session: Session,
    athlete_id: int = 1,
) -> ImportResult | None:
    """Import FIT files from Garmin Connect local folder.

    This imports activities that have been synced to Garmin Connect via
    Garmin Express or mobile app.

    Args:
        session: Database session
        athlete_id: Athlete ID to assign to activities

    Returns:
        ImportResult with statistics, or None if folder not found
    """
    gc_path = find_garmin_connect_directory()

    if not gc_path:
        return None

    return import_from_directory(session, gc_path, athlete_id)


def import_from_zip(
    session: Session,
    zip_path: Path,
    athlete_id: int = 1,
) -> ImportResult:
    """Import FIT files from a Garmin bulk export ZIP.

    Args:
        session: Database session
        zip_path: Path to Garmin bulk export ZIP file
        athlete_id: Athlete ID to assign to activities

    Returns:
        ImportResult with statistics
    """
    result = ImportResult()

    # Extract ZIP to temp directory
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Extract ZIP
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_path)

        # Import from extracted directory
        result = import_from_directory(session, temp_path, athlete_id)

    return result
