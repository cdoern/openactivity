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
        Path.home() / ".wine" / "drive_c" / "Users" / "Public" / "Documents" / "Garmin" / "GarminConnect",
    ]

    for path in possible_paths:
        if path.exists():
            return path

    return None


def find_connected_device() -> Path | None:
    """Find a connected Garmin device.

    Returns:
        Path to device's Garmin directory, or None if not found
    """
    # Common mount points for Garmin devices
    possible_paths = [
        # Linux
        Path("/media") / "GARMIN" / "Garmin",
        Path("/run/media") / Path.home().name / "GARMIN" / "Garmin",
        # macOS
        Path("/Volumes") / "GARMIN" / "Garmin",
        # Windows
        Path("D:/Garmin"),
        Path("E:/Garmin"),
        Path("F:/Garmin"),
    ]

    for path in possible_paths:
        if path.exists() and (path / "Activities").exists():
            return path / "Activities"

    return None


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

    fit_files = find_fit_files_in_directory(directory)

    for fit_file in fit_files:
        result.files_processed += 1

        try:
            # Parse FIT file
            activity_data = parse_fit_file(fit_file)

            if not activity_data:
                result.activities_skipped += 1
                continue

            # Check if already imported
            provider_id = activity_data["provider_id"]
            existing = (
                session.query(Activity)
                .filter_by(provider="garmin", provider_id=provider_id)
                .first()
            )

            if existing:
                result.activities_skipped += 1
                continue

            # Create new activity
            activity_data["athlete_id"] = athlete_id
            new_activity = Activity(**activity_data)
            session.add(new_activity)
            result.activities_imported += 1

        except Exception:
            result.activities_errors += 1
            continue

    session.commit()
    return result


def import_from_device(
    session: Session,
    athlete_id: int = 1,
) -> ImportResult | None:
    """Import FIT files from a connected Garmin device.

    Args:
        session: Database session
        athlete_id: Athlete ID to assign to activities

    Returns:
        ImportResult with statistics, or None if no device found
    """
    device_path = find_connected_device()

    if not device_path:
        return None

    return import_from_directory(session, device_path, athlete_id)


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
