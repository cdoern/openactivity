"""Tests for training block detection and classification."""

from __future__ import annotations

from datetime import datetime, timedelta

from openactivity.analysis.blocks import (
    BASE,
    BUILD,
    PEAK,
    RECOVERY,
    aggregate_weeks,
    classify_weeks,
    compute_week_intensity,
    group_into_blocks,
)


def _make_activity(**kwargs):
    """Create a mock activity object."""

    class MockActivity:
        pass

    a = MockActivity()
    a.id = kwargs.get("id", 1)
    a.start_date = kwargs.get("start_date", datetime(2026, 1, 5, 10, 0))  # Monday
    a.distance = kwargs.get("distance", 10000.0)
    a.moving_time = kwargs.get("moving_time", 3600)
    a.average_speed = kwargs.get("average_speed", 3.0)
    a.average_heartrate = kwargs.get("average_heartrate", None)
    a.max_heartrate = kwargs.get("max_heartrate", None)
    a.total_elevation_gain = kwargs.get("total_elevation_gain", 50.0)
    a.name = kwargs.get("name", "Test Run")
    a.type = kwargs.get("type", "Run")
    return a


def _make_week(distance=10000, intensity=50, classification=None, week_offset=0):
    """Create a mock WeekSummary dict."""
    base = datetime(2026, 1, 5)  # Monday
    start = base + timedelta(weeks=week_offset)
    return {
        "week_key": f"2026-W{week_offset + 1:02d}",
        "week_start": start,
        "week_end": start + timedelta(days=6),
        "total_distance": float(distance),
        "total_duration": 3600,
        "activity_count": 3,
        "activities": [],
        "avg_intensity": float(intensity),
        "intensity_source": "default",
        "classification": classification,
    }


# ---- Tests for aggregate_weeks ----


class TestAggregateWeeks:
    def test_empty_activities(self):
        assert aggregate_weeks([]) == []

    def test_single_week(self):
        a = _make_activity(start_date=datetime(2026, 1, 5), distance=5000)
        weeks = aggregate_weeks([a])
        assert len(weeks) == 1
        assert weeks[0]["total_distance"] == 5000
        assert weeks[0]["activity_count"] == 1

    def test_multi_week(self):
        a1 = _make_activity(start_date=datetime(2026, 1, 5), distance=5000)
        a2 = _make_activity(start_date=datetime(2026, 1, 12), distance=8000)
        weeks = aggregate_weeks([a1, a2])
        # Should have 2 weeks
        assert any(w["total_distance"] == 5000 for w in weeks)
        assert any(w["total_distance"] == 8000 for w in weeks)

    def test_same_week_aggregation(self):
        a1 = _make_activity(start_date=datetime(2026, 1, 5), distance=5000)
        a2 = _make_activity(start_date=datetime(2026, 1, 7), distance=3000)
        weeks = aggregate_weeks([a1, a2])
        # Both in same week
        week = [w for w in weeks if w["total_distance"] == 8000]
        assert len(week) == 1
        assert week[0]["activity_count"] == 2


# ---- Tests for compute_week_intensity ----


class TestComputeWeekIntensity:
    def test_hr_based_intensity(self):
        a = _make_activity(average_heartrate=152, max_heartrate=190)
        week = {"activities": [a]}
        intensity, source = compute_week_intensity(week, estimated_max_hr=190)
        assert source == "hr"
        assert 75 < intensity < 85  # 152/190 * 100 ≈ 80

    def test_pace_based_fallback(self):
        a = _make_activity(average_heartrate=None, average_speed=4.0)
        week = {"activities": [a]}
        distribution = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
        intensity, source = compute_week_intensity(
            week, pace_distribution=distribution
        )
        assert source == "pace"
        assert intensity > 0

    def test_default_when_no_data(self):
        week = {"activities": []}
        intensity, source = compute_week_intensity(week)
        assert source == "default"
        assert intensity == 0.0


# ---- Tests for classify_weeks ----


class TestClassifyWeeks:
    def test_recovery_low_volume(self):
        # 4 normal weeks then 1 low volume week
        weeks = [_make_week(distance=10000, week_offset=i) for i in range(4)]
        weeks.append(_make_week(distance=5000, intensity=40, week_offset=4))
        classify_weeks(weeks)
        assert weeks[4]["classification"] == RECOVERY

    def test_base_high_volume_low_intensity(self):
        weeks = [_make_week(distance=10000, intensity=45, week_offset=i) for i in range(5)]
        classify_weeks(weeks)
        # Steady volume, low intensity = base
        assert weeks[4]["classification"] == BASE

    def test_build_rising_volume_high_intensity(self):
        weeks = []
        for i in range(5):
            weeks.append(_make_week(
                distance=10000 + i * 2000,
                intensity=65,
                week_offset=i,
            ))
        classify_weeks(weeks)
        # Rising volume + high intensity = build
        assert weeks[4]["classification"] == BUILD

    def test_peak_high_intensity_tapering(self):
        weeks = [
            _make_week(distance=15000, intensity=72, week_offset=0),
            _make_week(distance=16000, intensity=72, week_offset=1),
            _make_week(distance=17000, intensity=72, week_offset=2),
            _make_week(distance=15000, intensity=75, week_offset=3),
            _make_week(distance=13000, intensity=75, week_offset=4),
        ]
        classify_weeks(weeks)
        assert weeks[4]["classification"] == PEAK


# ---- Tests for group_into_blocks ----


class TestGroupIntoBlocks:
    def test_single_phase_one_block(self):
        weeks = [_make_week(classification=BASE, week_offset=i) for i in range(5)]
        blocks = group_into_blocks(weeks)
        assert len(blocks) == 1
        assert blocks[0]["phase"] == BASE
        assert blocks[0]["week_count"] == 5

    def test_phase_change_creates_new_block(self):
        weeks = [
            _make_week(classification=BASE, week_offset=0),
            _make_week(classification=BASE, week_offset=1),
            _make_week(classification=BUILD, week_offset=2),
            _make_week(classification=BUILD, week_offset=3),
        ]
        blocks = group_into_blocks(weeks)
        assert len(blocks) == 2
        assert blocks[0]["phase"] == BASE
        assert blocks[1]["phase"] == BUILD

    def test_gap_forces_boundary(self):
        weeks = [
            _make_week(classification=BASE, week_offset=0),
            _make_week(classification=BASE, week_offset=5),  # 5 weeks later = gap
        ]
        # Manually set dates with >14 day gap
        weeks[1]["week_start"] = weeks[0]["week_end"] + timedelta(days=20)
        weeks[1]["week_end"] = weeks[1]["week_start"] + timedelta(days=6)
        blocks = group_into_blocks(weeks)
        assert len(blocks) == 2  # Gap forces separate blocks

    def test_last_block_marked_current(self):
        weeks = [_make_week(classification=BASE, week_offset=i) for i in range(3)]
        blocks = group_into_blocks(weeks)
        assert blocks[-1]["is_current"] is True
        if len(blocks) > 1:
            assert blocks[0]["is_current"] is False

    def test_empty_weeks(self):
        assert group_into_blocks([]) == []
