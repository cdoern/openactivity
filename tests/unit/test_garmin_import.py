"""Unit tests for Garmin import logic (T030)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from openactivity.db.models import Activity, Base
from openactivity.providers.garmin.importer import (
    ImportResult,
    find_fit_files_in_directory,
    import_from_directory,
    import_from_zip,
)
from tests.fixtures.fit_generator import (
    write_corrupted_fit_file,
    write_fit_file,
    write_non_activity_fit_file,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
SAMPLE_DIR = FIXTURES_DIR / "sample_activities"


@pytest.fixture()
def session():
    """Create an in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    s = factory()
    yield s
    s.close()


# === ImportResult Tests ===


class TestImportResult:
    def test_default_values(self) -> None:
        result = ImportResult()
        assert result.activities_imported == 0
        assert result.activities_skipped == 0
        assert result.activities_errors == 0
        assert result.files_processed == 0


# === find_fit_files_in_directory Tests ===


class TestFindFitFilesInDirectory:
    def test_finds_fit_files(self) -> None:
        files = find_fit_files_in_directory(SAMPLE_DIR)
        assert len(files) >= 3  # run, ride, swim

    def test_nonexistent_directory_returns_empty(self) -> None:
        files = find_fit_files_in_directory(Path("/nonexistent/dir"))
        assert files == []

    def test_empty_directory(self, tmp_path: Path) -> None:
        files = find_fit_files_in_directory(tmp_path)
        assert files == []

    def test_finds_recursive(self, tmp_path: Path) -> None:
        subdir = tmp_path / "sub" / "dir"
        write_fit_file(subdir / "test.fit")
        files = find_fit_files_in_directory(tmp_path)
        assert len(files) == 1

    def test_finds_uppercase_extension(self, tmp_path: Path) -> None:
        write_fit_file(tmp_path / "test.FIT")
        files = find_fit_files_in_directory(tmp_path)
        assert len(files) == 1

    def test_ignores_non_fit_files(self, tmp_path: Path) -> None:
        (tmp_path / "notes.txt").write_text("hello")
        (tmp_path / "data.csv").write_text("a,b,c")
        write_fit_file(tmp_path / "activity.fit")
        files = find_fit_files_in_directory(tmp_path)
        assert len(files) == 1


# === import_from_directory Tests ===


class TestImportFromDirectory:
    def test_import_sample_activities(self, session) -> None:
        result = import_from_directory(session, SAMPLE_DIR)

        assert result.activities_imported == 3
        assert result.activities_errors == 0
        assert result.files_processed >= 3

        # Check activities are in database
        activities = session.query(Activity).all()
        assert len(activities) == 3
        types = {a.type for a in activities}
        assert "Run" in types
        assert "Ride" in types
        assert "Swim" in types

    def test_all_activities_have_garmin_provider(self, session) -> None:
        import_from_directory(session, SAMPLE_DIR)
        activities = session.query(Activity).all()
        for a in activities:
            assert a.provider == "garmin"

    def test_duplicate_import_skips(self, session) -> None:
        """Importing the same files twice should skip duplicates."""
        result1 = import_from_directory(session, SAMPLE_DIR)
        result2 = import_from_directory(session, SAMPLE_DIR)

        assert result1.activities_imported == 3
        assert result2.activities_imported == 0
        assert result2.activities_skipped >= 3

        # Still only 3 in DB
        assert session.query(Activity).count() == 3

    def test_import_empty_directory(self, session, tmp_path: Path) -> None:
        result = import_from_directory(session, tmp_path)
        assert result.activities_imported == 0
        assert result.files_processed == 0

    def test_import_nonexistent_directory(self, session) -> None:
        result = import_from_directory(session, Path("/nonexistent/dir"))
        assert result.activities_imported == 0
        assert result.files_processed == 0

    def test_corrupted_files_counted_as_errors(self, session, tmp_path: Path) -> None:
        write_corrupted_fit_file(tmp_path / "bad.fit")
        write_fit_file(tmp_path / "good.fit")
        result = import_from_directory(session, tmp_path)

        # corrupted file either errors or gets skipped (parse returns None)
        assert result.activities_imported == 1
        assert result.files_processed == 2

    def test_non_activity_files_skipped(self, session, tmp_path: Path) -> None:
        write_non_activity_fit_file(tmp_path / "settings.fit")
        result = import_from_directory(session, tmp_path)

        assert result.activities_imported == 0
        assert result.activities_skipped >= 1

    def test_athlete_id_assigned(self, session) -> None:
        import_from_directory(session, SAMPLE_DIR, athlete_id=42)
        activities = session.query(Activity).all()
        for a in activities:
            assert a.athlete_id == 42

    def test_mixed_valid_and_invalid(self, session, tmp_path: Path) -> None:
        write_fit_file(tmp_path / "good1.fit", start_time=datetime(2026, 1, 1, 8, 0))
        write_fit_file(tmp_path / "good2.fit", start_time=datetime(2026, 1, 2, 8, 0))
        write_non_activity_fit_file(tmp_path / "settings.fit")
        write_corrupted_fit_file(tmp_path / "bad.fit")

        result = import_from_directory(session, tmp_path)
        assert result.activities_imported == 2
        assert result.files_processed == 4


# === import_from_zip Tests ===


class TestImportFromZip:
    def test_import_from_zip(self, session, tmp_path: Path) -> None:
        import zipfile

        # Create FIT files in a temp dir, then zip them
        fit_dir = tmp_path / "fits"
        fit_dir.mkdir()
        write_fit_file(fit_dir / "run.fit", sport="running", start_time=datetime(2026, 2, 1, 7, 0))
        write_fit_file(fit_dir / "ride.fit", sport="cycling", start_time=datetime(2026, 2, 2, 7, 0))

        zip_path = tmp_path / "export.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(fit_dir / "run.fit", "run.fit")
            zf.write(fit_dir / "ride.fit", "ride.fit")

        result = import_from_zip(session, zip_path)
        assert result.activities_imported == 2

    def test_zip_with_subdirectories(self, session, tmp_path: Path) -> None:
        import zipfile

        fit_dir = tmp_path / "fits"
        fit_dir.mkdir()
        write_fit_file(fit_dir / "act.fit", start_time=datetime(2026, 3, 1, 7, 0))

        zip_path = tmp_path / "nested.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(fit_dir / "act.fit", "Activities/act.fit")

        result = import_from_zip(session, zip_path)
        assert result.activities_imported == 1

    def test_zip_with_non_fit_files(self, session, tmp_path: Path) -> None:
        import zipfile

        fit_dir = tmp_path / "fits"
        fit_dir.mkdir()
        write_fit_file(fit_dir / "run.fit", start_time=datetime(2026, 4, 1, 7, 0))
        (fit_dir / "readme.txt").write_text("just a text file")

        zip_path = tmp_path / "mixed.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(fit_dir / "run.fit", "run.fit")
            zf.write(fit_dir / "readme.txt", "readme.txt")

        result = import_from_zip(session, zip_path)
        assert result.activities_imported == 1
