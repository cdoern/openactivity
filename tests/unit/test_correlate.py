"""Tests for cross-activity correlation engine."""

from __future__ import annotations

from datetime import datetime, timedelta

from openactivity.analysis.correlate import (
    classify_strength,
    compute_correlation,
    interpret_direction,
)


# ---- Tests for metric functions ----


def _make_activity(**kwargs):
    """Create a mock activity object."""

    class MockActivity:
        pass

    a = MockActivity()
    a.id = kwargs.get("id", 1)
    a.start_date = kwargs.get("start_date", datetime(2026, 1, 5, 10, 0))
    a.distance = kwargs.get("distance", 10000.0)
    a.moving_time = kwargs.get("moving_time", 3600)
    a.average_speed = kwargs.get("average_speed", 3.0)
    a.average_heartrate = kwargs.get("average_heartrate", None)
    a.max_heartrate = kwargs.get("max_heartrate", None)
    a.total_elevation_gain = kwargs.get("total_elevation_gain", 50.0)
    a.name = kwargs.get("name", "Test Run")
    a.type = kwargs.get("type", "Run")
    return a


def _make_week(**kwargs):
    """Create a mock week dict with activities."""
    base = datetime(2026, 1, 5)
    offset = kwargs.get("week_offset", 0)
    start = base + timedelta(weeks=offset)
    activities = kwargs.get("activities", [])
    return {
        "week_key": f"2026-W{offset + 1:02d}",
        "week_start": start,
        "week_end": start + timedelta(days=6),
        "total_distance": kwargs.get("total_distance", 30000.0),
        "total_duration": kwargs.get("total_duration", 10800),
        "activity_count": kwargs.get("activity_count", 3),
        "activities": activities,
    }


class TestMetricFunctions:
    def test_weekly_distance(self):
        from openactivity.analysis.correlate import _weekly_distance

        week = _make_week(total_distance=42000.0)
        assert _weekly_distance(week) == 42000.0

    def test_weekly_duration(self):
        from openactivity.analysis.correlate import _weekly_duration

        week = _make_week(total_duration=7200)
        assert _weekly_duration(week) == 7200.0

    def test_activity_count(self):
        from openactivity.analysis.correlate import _activity_count

        week = _make_week(activity_count=5)
        assert _activity_count(week) == 5.0

    def test_rest_days(self):
        from openactivity.analysis.correlate import _rest_days

        # 3 activities on different days
        activities = [
            _make_activity(start_date=datetime(2026, 1, 5)),
            _make_activity(start_date=datetime(2026, 1, 7)),
            _make_activity(start_date=datetime(2026, 1, 9)),
        ]
        week = _make_week(activities=activities)
        assert _rest_days(week) == 4.0  # 7 - 3 active days

    def test_rest_days_no_activities(self):
        from openactivity.analysis.correlate import _rest_days

        week = _make_week(activities=[])
        assert _rest_days(week) == 7.0

    def test_avg_hr_with_data(self):
        from openactivity.analysis.correlate import _avg_hr

        activities = [
            _make_activity(average_heartrate=150),
            _make_activity(average_heartrate=160),
        ]
        week = _make_week(activities=activities)
        assert _avg_hr(week) == 155.0

    def test_avg_hr_no_data(self):
        from openactivity.analysis.correlate import _avg_hr

        activities = [_make_activity(average_heartrate=None)]
        week = _make_week(activities=activities)
        assert _avg_hr(week) is None

    def test_longest_run(self):
        from openactivity.analysis.correlate import _longest_run

        activities = [
            _make_activity(distance=5000),
            _make_activity(distance=12000),
            _make_activity(distance=8000),
        ]
        week = _make_week(activities=activities)
        assert _longest_run(week) == 12000.0

    def test_avg_pace(self):
        from openactivity.analysis.correlate import _avg_pace

        activities = [
            _make_activity(distance=10000, moving_time=3000),  # 5:00/km
        ]
        week = _make_week(activities=activities)
        pace = _avg_pace(week)
        assert pace is not None
        assert abs(pace - 300.0) < 0.1  # 300 seconds per km


# ---- Tests for compute_correlation ----


class TestComputeCorrelation:
    def test_perfect_positive(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        result = compute_correlation(x, y)
        assert abs(result["pearson_r"] - 1.0) < 0.001
        assert result["pearson_p"] < 0.05

    def test_perfect_negative(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [10.0, 8.0, 6.0, 4.0, 2.0]
        result = compute_correlation(x, y)
        assert abs(result["pearson_r"] + 1.0) < 0.001

    def test_no_correlation(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [3.0, 1.0, 4.0, 2.0, 5.0]
        result = compute_correlation(x, y)
        assert abs(result["pearson_r"]) < 0.8  # Not strongly correlated

    def test_constant_array_returns_error(self):
        x = [5.0, 5.0, 5.0, 5.0]
        y = [1.0, 2.0, 3.0, 4.0]
        result = compute_correlation(x, y)
        assert "error" in result
        assert result["error"] == "zero_variance"

    def test_insufficient_data(self):
        x = [1.0, 2.0]
        y = [3.0, 4.0]
        result = compute_correlation(x, y)
        assert "error" in result
        assert result["error"] == "insufficient_data"

    def test_spearman_included(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        result = compute_correlation(x, y)
        assert "spearman_r" in result
        assert "spearman_p" in result


# ---- Tests for classify_strength ----


class TestClassifyStrength:
    def test_weak(self):
        assert classify_strength(0.1) == "weak"
        assert classify_strength(-0.2) == "weak"

    def test_moderate(self):
        assert classify_strength(0.5) == "moderate"
        assert classify_strength(-0.4) == "moderate"

    def test_strong(self):
        assert classify_strength(0.8) == "strong"
        assert classify_strength(-0.9) == "strong"

    def test_boundary_weak_moderate(self):
        assert classify_strength(0.29) == "weak"
        assert classify_strength(0.3) == "moderate"

    def test_boundary_moderate_strong(self):
        assert classify_strength(0.69) == "moderate"
        assert classify_strength(0.7) == "strong"


# ---- Tests for interpret_direction ----


class TestInterpretDirection:
    def test_positive_correlation(self):
        result = interpret_direction("weekly_distance", "avg_hr", 0.5)
        assert "More" in result
        assert "higher" in result

    def test_negative_correlation(self):
        result = interpret_direction("weekly_distance", "avg_hr", -0.5)
        assert "More" in result
        assert "lower" in result

    def test_pace_special_handling(self):
        # Negative correlation with pace means faster
        result = interpret_direction("weekly_distance", "avg_pace", -0.5)
        assert "faster" in result

    def test_no_meaningful_association(self):
        result = interpret_direction("weekly_distance", "avg_hr", 0.05)
        assert "No meaningful" in result
