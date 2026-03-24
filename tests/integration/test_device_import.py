"""Test import from device with mock mount point (T033)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path  # noqa: TC003 - used at runtime in type annotations
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from openactivity.db.models import Activity, Base
from openactivity.providers.garmin.importer import import_from_device
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


@pytest.fixture()
def mock_device(tmp_path: Path) -> Path:
    """Create a mock Garmin device mount point with FIT files."""
    activities_dir = tmp_path / "GARMIN" / "Garmin" / "Activities"
    activities_dir.mkdir(parents=True)

    write_fit_file(
        activities_dir / "2026-03-20-07-30-00.fit",
        sport="running", distance=5000.0,
        start_time=datetime(2026, 3, 20, 7, 30, 0),
    )
    write_fit_file(
        activities_dir / "2026-03-19-08-00-00.fit",
        sport="cycling", distance=15000.0,
        start_time=datetime(2026, 3, 19, 8, 0, 0),
    )
    return activities_dir


class TestImportFromDevice:
    @patch("openactivity.providers.garmin.importer.find_connected_device")
    def test_import_from_usb_mass_storage(self, mock_find, session, mock_device) -> None:
        """Test importing from a USB mass storage mounted device."""
        mock_find.return_value = mock_device

        result = import_from_device(session)
        assert result is not None
        assert result.activities_imported == 2
        assert session.query(Activity).count() == 2

    @patch("openactivity.providers.garmin.importer.find_connected_device")
    def test_no_device_found_no_mtp(self, mock_find, session) -> None:
        """Test behavior when no device is found and MTP not available."""
        mock_find.return_value = None

        with patch(
            "openactivity.providers.garmin.mtp.is_libmtp_available",
            return_value=False,
        ):
            result = import_from_device(session)
            assert result is None

    @patch("openactivity.providers.garmin.importer.find_connected_device")
    def test_device_with_no_activities(self, mock_find, session, tmp_path: Path) -> None:
        """Test device mount point exists but has no FIT files."""
        empty_activities = tmp_path / "Activities"
        empty_activities.mkdir()
        mock_find.return_value = empty_activities

        result = import_from_device(session)
        assert result is not None
        assert result.activities_imported == 0
        assert result.files_processed == 0

    @patch("openactivity.providers.garmin.importer.find_connected_device")
    def test_idempotent_device_import(self, mock_find, session, mock_device) -> None:
        """Importing from device twice should skip duplicates."""
        mock_find.return_value = mock_device

        r1 = import_from_device(session)
        r2 = import_from_device(session)

        assert r1.activities_imported == 2
        assert r2.activities_imported == 0
        assert session.query(Activity).count() == 2

    @patch("openactivity.providers.garmin.importer.find_connected_device")
    def test_custom_athlete_id(self, mock_find, session, mock_device) -> None:
        mock_find.return_value = mock_device

        result = import_from_device(session, athlete_id=99)
        assert result.activities_imported == 2

        activities = session.query(Activity).all()
        for a in activities:
            assert a.athlete_id == 99
