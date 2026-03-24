"""End-to-end import tests with sample FIT files (T032)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from openactivity.db.models import Activity, Base
from openactivity.providers.garmin.importer import import_from_directory
from tests.fixtures.fit_generator import write_fit_file

SAMPLE_DIR = Path(__file__).parent.parent / "fixtures" / "sample_activities"


@pytest.fixture()
def session():
    """Create an in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    s = factory()
    yield s
    s.close()


class TestEndToEndImport:
    """Full pipeline: FIT file -> parse -> import -> query."""

    def test_parse_then_import_run(self, session) -> None:
        """Parse a running FIT file and verify it becomes a valid Activity."""
        result = import_from_directory(session, SAMPLE_DIR)
        assert result.activities_imported >= 1

        run = (
            session.query(Activity)
            .filter_by(type="Run", provider="garmin")
            .first()
        )
        assert run is not None
        assert run.distance == pytest.approx(5000.0, rel=0.01)
        assert run.moving_time == 1750
        assert run.elapsed_time == 1800
        assert run.average_heartrate == 155
        assert run.max_heartrate == 180
        assert run.has_heartrate is True
        assert run.provider_id is not None

    def test_parse_then_import_ride(self, session) -> None:
        import_from_directory(session, SAMPLE_DIR)

        ride = (
            session.query(Activity)
            .filter_by(type="Ride", provider="garmin")
            .first()
        )
        assert ride is not None
        assert ride.distance == pytest.approx(30000.0, rel=0.01)
        assert ride.sport_type == "cycling"

    def test_parse_then_import_swim(self, session) -> None:
        import_from_directory(session, SAMPLE_DIR)

        swim = (
            session.query(Activity)
            .filter_by(type="Swim", provider="garmin")
            .first()
        )
        assert swim is not None
        assert swim.distance == pytest.approx(1500.0, rel=0.01)

    def test_multiple_imports_idempotent(self, session) -> None:
        """Running import twice should not create duplicates."""
        r1 = import_from_directory(session, SAMPLE_DIR)
        r2 = import_from_directory(session, SAMPLE_DIR)

        assert r1.activities_imported == 3
        assert r2.activities_imported == 0
        assert session.query(Activity).count() == 3

    def test_large_batch_import(self, session, tmp_path: Path) -> None:
        """Import a batch of 20 activities."""
        for i in range(20):
            write_fit_file(
                tmp_path / f"activity_{i:03d}.fit",
                sport="running",
                distance=5000.0 + i * 100,
                start_time=datetime(2026, 1, 1 + i, 7, 0, 0),
            )

        result = import_from_directory(session, tmp_path)
        assert result.activities_imported == 20
        assert result.activities_errors == 0
        assert session.query(Activity).count() == 20

    def test_garmin_and_strava_coexist(self, session) -> None:
        """Garmin activities should not conflict with Strava activities."""
        # Manually add a Strava activity
        strava_act = Activity(
            id=999999,
            athlete_id=1,
            provider="strava",
            provider_id=12345,
            name="Morning Run",
            type="Run",
            distance=5000.0,
            moving_time=1800,
            elapsed_time=1800,
        )
        session.add(strava_act)
        session.commit()

        # Import Garmin activities
        result = import_from_directory(session, SAMPLE_DIR)
        assert result.activities_imported == 3

        # Both should exist
        total = session.query(Activity).count()
        assert total == 4  # 1 strava + 3 garmin

        strava = session.query(Activity).filter_by(provider="strava").count()
        garmin = session.query(Activity).filter_by(provider="garmin").count()
        assert strava == 1
        assert garmin == 3
