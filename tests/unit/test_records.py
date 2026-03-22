"""Unit tests for personal records scanning and management."""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from openactivity.analysis.records import (
    RUNNING_DISTANCES,
    find_best_effort_for_distance,
    find_best_power_for_duration,
    scan_activity_for_records,
)
from openactivity.db.models import (
    Activity,
    ActivityStream,
    Base,
    PersonalRecord,
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


# === Sliding Window Algorithm Tests ===


class TestFindBestEffortForDistance:
    def test_basic_effort(self) -> None:
        # 10 points, each 100m apart, each 10s apart => 1000m in 100s
        distance = [float(i * 100) for i in range(11)]
        time = [float(i * 10) for i in range(11)]
        result = find_best_effort_for_distance(distance, time, 500.0)
        assert result == 50.0

    def test_activity_too_short(self) -> None:
        distance = [0.0, 100.0, 200.0]
        time = [0.0, 10.0, 20.0]
        result = find_best_effort_for_distance(distance, time, 500.0)
        assert result is None

    def test_exact_distance_match(self) -> None:
        distance = [0.0, 250.0, 500.0]
        time = [0.0, 30.0, 60.0]
        result = find_best_effort_for_distance(distance, time, 500.0)
        assert result == 60.0

    def test_finds_fastest_segment(self) -> None:
        # Slow start, fast middle
        distance = [0.0, 100.0, 200.0, 400.0, 600.0, 700.0, 800.0]
        time = [0.0, 20.0, 40.0, 50.0, 60.0, 80.0, 100.0]
        result = find_best_effort_for_distance(distance, time, 400.0)
        # Best 400m: indices 2->4 (200m to 600m) in 20s
        assert result == 20.0

    def test_empty_streams(self) -> None:
        assert find_best_effort_for_distance([], [], 500.0) is None

    def test_mismatched_lengths(self) -> None:
        assert find_best_effort_for_distance([0.0, 100.0], [0.0], 50.0) is None

    def test_single_point(self) -> None:
        assert find_best_effort_for_distance([0.0], [0.0], 100.0) is None


class TestFindBestPowerForDuration:
    def test_basic_power(self) -> None:
        watts = [200.0] * 10
        result = find_best_power_for_duration(watts, 5)
        assert result == 200

    def test_finds_best_window(self) -> None:
        watts = [100.0] * 5 + [300.0] * 5 + [100.0] * 5
        result = find_best_power_for_duration(watts, 5)
        assert result == 300

    def test_stream_too_short(self) -> None:
        watts = [200.0, 300.0]
        result = find_best_power_for_duration(watts, 5)
        assert result is None

    def test_empty_stream(self) -> None:
        assert find_best_power_for_duration([], 5) is None

    def test_exact_length(self) -> None:
        watts = [250.0] * 5
        result = find_best_power_for_duration(watts, 5)
        assert result == 250


# === Record Management Tests ===


class TestScanActivityForRecords:
    def _make_activity(self, session: Session, **kwargs) -> Activity:
        defaults = {
            "id": 1,
            "athlete_id": 1,
            "name": "Test Run",
            "type": "Run",
            "start_date": datetime(2026, 1, 15),
            "distance": 5500.0,
            "moving_time": 1500,
            "elapsed_time": 1600,
        }
        defaults.update(kwargs)
        activity = Activity(**defaults)
        session.add(activity)
        session.flush()
        return activity

    def _add_stream(self, session: Session, activity_id: int, stream_type: str, data: list) -> None:
        import json

        stream = ActivityStream(
            activity_id=activity_id,
            stream_type=stream_type,
            data=json.dumps(data).encode(),
        )
        session.add(stream)
        session.flush()

    def test_new_pr_inserted(self, session: Session) -> None:
        activity = self._make_activity(session)
        # 5K in 1500s (25:00)
        distance = [float(i * 50) for i in range(101)]  # 0 to 5000m
        time = [float(i * 15) for i in range(101)]  # 0 to 1500s
        self._add_stream(session, activity.id, "distance", distance)
        self._add_stream(session, activity.id, "time", time)

        distances = [("5K", 5000.0)]
        result = scan_activity_for_records(session, activity, distances)

        assert result["new_records"] == 1
        assert result["updated_records"] == 0

        pr = session.query(PersonalRecord).filter_by(distance_type="5K").first()
        assert pr is not None
        assert pr.is_current is True
        assert pr.value == 1500.0
        assert pr.activity_id == activity.id

    def test_faster_pr_updates(self, session: Session) -> None:
        # First activity: 5K in 1500s
        a1 = self._make_activity(session, id=1, start_date=datetime(2026, 1, 1))
        dist1 = [float(i * 50) for i in range(101)]
        time1 = [float(i * 15) for i in range(101)]
        self._add_stream(session, a1.id, "distance", dist1)
        self._add_stream(session, a1.id, "time", time1)
        scan_activity_for_records(session, a1, [("5K", 5000.0)])

        # Second activity: 5K in 1200s (faster)
        a2 = self._make_activity(session, id=2, name="Fast Run", start_date=datetime(2026, 2, 1))
        dist2 = [float(i * 50) for i in range(101)]
        time2 = [float(i * 12) for i in range(101)]
        self._add_stream(session, a2.id, "distance", dist2)
        self._add_stream(session, a2.id, "time", time2)
        result = scan_activity_for_records(session, a2, [("5K", 5000.0)])

        assert result["updated_records"] == 1

        records = session.query(PersonalRecord).filter_by(distance_type="5K").all()
        assert len(records) == 2

        current = [r for r in records if r.is_current]
        assert len(current) == 1
        assert current[0].value == 1200.0
        assert current[0].activity_name == "Fast Run"

    def test_slower_effort_not_recorded(self, session: Session) -> None:
        # First: 5K in 1200s
        a1 = self._make_activity(session, id=1, start_date=datetime(2026, 1, 1))
        dist = [float(i * 50) for i in range(101)]
        time_fast = [float(i * 12) for i in range(101)]
        self._add_stream(session, a1.id, "distance", dist)
        self._add_stream(session, a1.id, "time", time_fast)
        scan_activity_for_records(session, a1, [("5K", 5000.0)])

        # Second: 5K in 1500s (slower)
        a2 = self._make_activity(session, id=2, start_date=datetime(2026, 2, 1))
        time_slow = [float(i * 15) for i in range(101)]
        self._add_stream(session, a2.id, "distance", dist)
        self._add_stream(session, a2.id, "time", time_slow)
        result = scan_activity_for_records(session, a2, [("5K", 5000.0)])

        assert result["new_records"] == 0
        assert result["updated_records"] == 0

        records = session.query(PersonalRecord).filter_by(distance_type="5K").all()
        assert len(records) == 1

    def test_power_pr(self, session: Session) -> None:
        activity = self._make_activity(session, type="Ride", has_power=True)
        watts = [300.0] * 60
        self._add_stream(session, activity.id, "watts", watts)

        scan_activity_for_records(session, activity, [])

        pr = session.query(PersonalRecord).filter_by(distance_type="1min").first()
        assert pr is not None
        assert pr.record_type == "power"
        assert pr.value == 300
        assert pr.is_current is True

    def test_no_streams_no_crash(self, session: Session) -> None:
        activity = self._make_activity(session)
        result = scan_activity_for_records(session, activity, RUNNING_DISTANCES)
        assert result["new_records"] == 0
        assert result["updated_records"] == 0
