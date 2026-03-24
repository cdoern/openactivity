"""Performance tests for FIT import pipeline (T040, T041, T042)."""

from __future__ import annotations

import time
import zipfile
from datetime import datetime, timedelta
from pathlib import Path  # noqa: TC003 - used at runtime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from openactivity.db.models import Base
from openactivity.providers.garmin.fit_parser import parse_fit_file
from openactivity.providers.garmin.importer import import_from_directory, import_from_zip
from tests.fixtures.fit_generator import write_fit_file


@pytest.fixture()
def session():
    """Create an in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    s = factory()
    yield s
    s.close()


class TestImportPerformance:
    """T040: Test import performance with many FIT files."""

    def test_import_100_files_under_threshold(self, session, tmp_path: Path) -> None:
        """100 FIT files should import in under 30 seconds."""
        base_time = datetime(2020, 1, 1, 6, 0, 0)
        for i in range(100):
            write_fit_file(
                tmp_path / f"act_{i:04d}.fit",
                sport="running",
                distance=5000.0 + i * 10,
                start_time=base_time + timedelta(hours=i),
            )

        start = time.monotonic()
        result = import_from_directory(session, tmp_path)
        elapsed = time.monotonic() - start

        assert result.activities_imported == 100
        assert result.activities_errors == 0
        assert elapsed < 30, f"Import took {elapsed:.1f}s, expected < 30s"

    def test_single_fit_parse_under_100ms(self, tmp_path: Path) -> None:
        """T042: A single FIT file should parse in under 100ms."""
        fit_path = write_fit_file(tmp_path / "single.fit")

        start = time.monotonic()
        for _ in range(10):
            parse_fit_file(fit_path)
        elapsed = time.monotonic() - start

        avg_ms = (elapsed / 10) * 1000
        assert avg_ms < 100, f"Average parse time {avg_ms:.1f}ms, expected < 100ms"


class TestZipImportPerformance:
    """T041: Test memory and performance for ZIP imports."""

    def test_zip_with_100_files(self, session, tmp_path: Path) -> None:
        """ZIP with 100 files should extract and import efficiently."""
        fit_dir = tmp_path / "fits"
        fit_dir.mkdir()

        base_time = datetime(2021, 1, 1, 6, 0, 0)
        zip_path = tmp_path / "bulk_export.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for i in range(100):
                fit_path = fit_dir / f"act_{i:04d}.fit"
                write_fit_file(
                    fit_path,
                    sport="running",
                    distance=5000.0 + i * 10,
                    start_time=base_time + timedelta(hours=i),
                )
                zf.write(fit_path, f"Activities/act_{i:04d}.fit")

        start = time.monotonic()
        result = import_from_zip(session, zip_path)
        elapsed = time.monotonic() - start

        assert result.activities_imported == 100
        assert result.activities_errors == 0
        assert elapsed < 60, f"ZIP import took {elapsed:.1f}s, expected < 60s"
