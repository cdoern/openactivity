"""Test import from ZIP files (T034)."""

from __future__ import annotations

import zipfile
from datetime import datetime
from pathlib import Path  # noqa: TC003 - used at runtime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from openactivity.db.models import Activity, Base
from openactivity.providers.garmin.importer import import_from_zip
from tests.fixtures.fit_generator import (
    write_corrupted_fit_file,
    write_fit_file,
    write_non_activity_fit_file,
)


@pytest.fixture()
def session():
    """Create an in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    s = factory()
    yield s
    s.close()


def _create_zip(tmp_path: Path, files: dict[str, Path]) -> Path:
    """Create a ZIP file from a dict of archive_name -> source_path."""
    zip_path = tmp_path / "export.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for name, path in files.items():
            zf.write(path, name)
    return zip_path


class TestImportFromZip:
    def test_basic_zip_import(self, session, tmp_path: Path) -> None:
        """Import a ZIP with two valid FIT files."""
        fit_dir = tmp_path / "fits"
        fit_dir.mkdir()
        write_fit_file(fit_dir / "run.fit", sport="running", start_time=datetime(2026, 5, 1, 7, 0))
        write_fit_file(fit_dir / "ride.fit", sport="cycling", start_time=datetime(2026, 5, 2, 7, 0))

        zip_path = _create_zip(tmp_path, {
            "run.fit": fit_dir / "run.fit",
            "ride.fit": fit_dir / "ride.fit",
        })

        result = import_from_zip(session, zip_path)
        assert result.activities_imported == 2
        assert session.query(Activity).count() == 2

    def test_nested_directory_in_zip(self, session, tmp_path: Path) -> None:
        """ZIP with files in subdirectories should still find them."""
        fit_dir = tmp_path / "fits"
        fit_dir.mkdir()
        write_fit_file(fit_dir / "act.fit", start_time=datetime(2026, 6, 1, 7, 0))

        zip_path = _create_zip(tmp_path, {
            "DI_CONNECT/DI-Connect-Fitness/UploadedFiles_0-_-1/act.fit": fit_dir / "act.fit",
        })

        result = import_from_zip(session, zip_path)
        assert result.activities_imported == 1

    def test_zip_with_mixed_content(self, session, tmp_path: Path) -> None:
        """ZIP with FIT files, text files, and CSVs."""
        fit_dir = tmp_path / "fits"
        fit_dir.mkdir()
        write_fit_file(fit_dir / "run.fit", start_time=datetime(2026, 7, 1, 7, 0))

        txt_file = fit_dir / "readme.txt"
        txt_file.write_text("This is a Garmin export")

        csv_file = fit_dir / "health.csv"
        csv_file.write_text("date,steps\n2026-03-20,10000\n")

        zip_path = _create_zip(tmp_path, {
            "Activities/run.fit": fit_dir / "run.fit",
            "readme.txt": txt_file,
            "Health/health.csv": csv_file,
        })

        result = import_from_zip(session, zip_path)
        assert result.activities_imported == 1

    def test_zip_with_corrupted_fit(self, session, tmp_path: Path) -> None:
        """Corrupted FIT file in ZIP should not crash import."""
        fit_dir = tmp_path / "fits"
        fit_dir.mkdir()
        write_fit_file(fit_dir / "good.fit", start_time=datetime(2026, 8, 1, 7, 0))
        write_corrupted_fit_file(fit_dir / "bad.fit")

        zip_path = _create_zip(tmp_path, {
            "good.fit": fit_dir / "good.fit",
            "bad.fit": fit_dir / "bad.fit",
        })

        result = import_from_zip(session, zip_path)
        assert result.activities_imported == 1
        assert result.files_processed == 2

    def test_zip_with_non_activity_fit(self, session, tmp_path: Path) -> None:
        """Non-activity FIT files should be skipped."""
        fit_dir = tmp_path / "fits"
        fit_dir.mkdir()
        write_fit_file(fit_dir / "run.fit", start_time=datetime(2026, 9, 1, 7, 0))
        write_non_activity_fit_file(fit_dir / "settings.fit")

        zip_path = _create_zip(tmp_path, {
            "run.fit": fit_dir / "run.fit",
            "settings.fit": fit_dir / "settings.fit",
        })

        result = import_from_zip(session, zip_path)
        assert result.activities_imported == 1

    def test_empty_zip(self, session, tmp_path: Path) -> None:
        """Empty ZIP should produce zero imports."""
        zip_path = tmp_path / "empty.zip"
        with zipfile.ZipFile(zip_path, "w"):
            pass

        result = import_from_zip(session, zip_path)
        assert result.activities_imported == 0
        assert result.files_processed == 0

    def test_large_zip_import(self, session, tmp_path: Path) -> None:
        """Import 50 activities from a ZIP."""
        fit_dir = tmp_path / "fits"
        fit_dir.mkdir()

        files = {}
        for i in range(50):
            path = fit_dir / f"act_{i:03d}.fit"
            write_fit_file(path, sport="running", start_time=datetime(2026, 1, 1, i % 24, 0))
            files[f"Activities/act_{i:03d}.fit"] = path

        zip_path = _create_zip(tmp_path, files)

        result = import_from_zip(session, zip_path)
        # Some may share timestamps, so allow for dedup
        assert result.activities_imported >= 24  # at least unique hours
        assert result.activities_errors == 0

    def test_duplicate_zip_import(self, session, tmp_path: Path) -> None:
        """Importing same ZIP twice should skip all on second run."""
        fit_dir = tmp_path / "fits"
        fit_dir.mkdir()
        write_fit_file(fit_dir / "run.fit", start_time=datetime(2026, 10, 1, 7, 0))

        zip_path = _create_zip(tmp_path, {"run.fit": fit_dir / "run.fit"})

        r1 = import_from_zip(session, zip_path)
        r2 = import_from_zip(session, zip_path)

        assert r1.activities_imported == 1
        assert r2.activities_imported == 0
        assert session.query(Activity).count() == 1
