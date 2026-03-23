"""Tests for segment trend analysis."""

from __future__ import annotations

from datetime import datetime, timedelta

from openactivity.analysis.segments import (
    MIN_EFFORTS,
    STABLE_THRESHOLD,
    _build_effort_summary,
    _classify_trend,
    _compute_hr_adjusted_trend,
    _compute_trend,
    compute_segment_trend_indicator,
)


# ---- Helpers ----


def _make_effort(**kwargs):
    """Create a mock SegmentEffort object."""

    class MockEffort:
        pass

    e = MockEffort()
    e.id = kwargs.get("id", 1)
    e.segment_id = kwargs.get("segment_id", 100)
    e.activity_id = kwargs.get("activity_id", 1000)
    e.elapsed_time = kwargs.get("elapsed_time", 300)
    e.moving_time = kwargs.get("moving_time", 290)
    e.start_date = kwargs.get("start_date", datetime(2026, 1, 15, 10, 0))
    e.pr_rank = kwargs.get("pr_rank", None)
    e.average_heartrate = kwargs.get("average_heartrate", None)
    e.average_watts = kwargs.get("average_watts", None)
    return e


# ---- Tests for _classify_trend ----


class TestClassifyTrend:
    def test_improving(self):
        assert _classify_trend(-3.0) == "improving"

    def test_declining(self):
        assert _classify_trend(3.0) == "declining"

    def test_stable_positive(self):
        assert _classify_trend(0.5) == "stable"

    def test_stable_negative(self):
        assert _classify_trend(-0.5) == "stable"

    def test_stable_zero(self):
        assert _classify_trend(0.0) == "stable"

    def test_boundary_improving(self):
        assert _classify_trend(-1.0) == "stable"
        assert _classify_trend(-1.01) == "improving"

    def test_boundary_declining(self):
        assert _classify_trend(1.0) == "stable"
        assert _classify_trend(1.01) == "declining"


# ---- Tests for _build_effort_summary ----


class TestBuildEffortSummary:
    def test_basic(self):
        effort = _make_effort(elapsed_time=300, start_date=datetime(2026, 1, 15))
        summary = _build_effort_summary(effort, best_time=250)
        assert summary["elapsed_time"] == 300
        assert summary["delta_from_best"] == 50
        assert summary["date"] == datetime(2026, 1, 15)

    def test_with_hr(self):
        effort = _make_effort(elapsed_time=300, average_heartrate=150)
        summary = _build_effort_summary(effort, best_time=300)
        assert summary["hr_normalized_time"] == round(300 / 150, 4)

    def test_no_hr(self):
        effort = _make_effort(elapsed_time=300, average_heartrate=None)
        summary = _build_effort_summary(effort, best_time=300)
        assert summary["hr_normalized_time"] is None

    def test_best_effort_zero_delta(self):
        effort = _make_effort(elapsed_time=250)
        summary = _build_effort_summary(effort, best_time=250)
        assert summary["delta_from_best"] == 0


# ---- Tests for _compute_trend ----


class TestComputeTrend:
    def test_improving_trend(self):
        # Times decreasing over days
        x_days = [0.0, 30.0, 60.0, 90.0, 120.0]
        y_times = [300.0, 290.0, 280.0, 270.0, 260.0]
        result = _compute_trend(x_days, y_times)
        assert result["direction"] == "improving"
        assert result["rate_of_change"] < -STABLE_THRESHOLD
        assert result["r_squared"] > 0.9

    def test_declining_trend(self):
        # Times increasing over days
        x_days = [0.0, 30.0, 60.0, 90.0, 120.0]
        y_times = [260.0, 270.0, 280.0, 290.0, 300.0]
        result = _compute_trend(x_days, y_times)
        assert result["direction"] == "declining"
        assert result["rate_of_change"] > STABLE_THRESHOLD

    def test_stable_trend(self):
        # Times mostly constant
        x_days = [0.0, 30.0, 60.0, 90.0, 120.0]
        y_times = [300.0, 300.5, 299.5, 300.0, 300.2]
        result = _compute_trend(x_days, y_times)
        assert result["direction"] == "stable"
        assert abs(result["rate_of_change"]) <= STABLE_THRESHOLD

    def test_result_has_required_fields(self):
        x_days = [0.0, 30.0, 60.0]
        y_times = [300.0, 290.0, 280.0]
        result = _compute_trend(x_days, y_times)
        assert "direction" in result
        assert "rate_of_change" in result
        assert "rate_unit" in result
        assert "r_squared" in result
        assert result["rate_unit"] == "seconds/month"


# ---- Tests for _compute_hr_adjusted_trend ----


class TestComputeHRAdjustedTrend:
    def test_with_sufficient_hr_data(self):
        base = datetime(2026, 1, 1)
        # Large time differences with constant HR so normalized trend is clear
        efforts = [
            _make_effort(
                elapsed_time=600 - i * 100,
                average_heartrate=150,
                start_date=base + timedelta(days=i * 30),
            )
            for i in range(5)
        ]
        result = _compute_hr_adjusted_trend(efforts)
        assert result is not None
        assert result["rate_of_change"] < 0  # Getting faster
        assert result["effort_count"] == 5

    def test_insufficient_hr_data(self):
        base = datetime(2026, 1, 1)
        efforts = [
            _make_effort(
                elapsed_time=300,
                average_heartrate=150,
                start_date=base + timedelta(days=i * 30),
            )
            for i in range(2)
        ]
        result = _compute_hr_adjusted_trend(efforts)
        assert result is None

    def test_mixed_hr_data(self):
        base = datetime(2026, 1, 1)
        efforts = [
            _make_effort(
                elapsed_time=300 - i * 10,
                average_heartrate=150 if i % 2 == 0 else None,
                start_date=base + timedelta(days=i * 30),
            )
            for i in range(6)
        ]
        result = _compute_hr_adjusted_trend(efforts)
        assert result is not None
        assert result["effort_count"] == 3  # Only even-indexed have HR

    def test_no_hr_data(self):
        base = datetime(2026, 1, 1)
        efforts = [
            _make_effort(
                elapsed_time=300,
                average_heartrate=None,
                start_date=base + timedelta(days=i * 30),
            )
            for i in range(5)
        ]
        result = _compute_hr_adjusted_trend(efforts)
        assert result is None

    def test_result_has_required_fields(self):
        base = datetime(2026, 1, 1)
        efforts = [
            _make_effort(
                elapsed_time=300 - i * 5,
                average_heartrate=150,
                start_date=base + timedelta(days=i * 30),
            )
            for i in range(4)
        ]
        result = _compute_hr_adjusted_trend(efforts)
        assert result is not None
        assert "direction" in result
        assert "rate_of_change" in result
        assert "rate_unit" in result
        assert "r_squared" in result
        assert "effort_count" in result
        assert result["rate_unit"] == "normalized_units/month"


# ---- Tests for compute_segment_trend_indicator ----


class TestComputeSegmentTrendIndicator:
    def test_insufficient_efforts(self, monkeypatch):
        def mock_efforts(session, segment_id):
            return [_make_effort() for _ in range(2)]

        monkeypatch.setattr(
            "openactivity.analysis.segments.get_segment_efforts_chronological",
            mock_efforts,
        )
        indicator, rate = compute_segment_trend_indicator(None, 100)
        assert indicator == "—"
        assert rate == "—"

    def test_improving_indicator(self, monkeypatch):
        base = datetime(2026, 1, 1)
        efforts = [
            _make_effort(
                elapsed_time=300 - i * 10,
                start_date=base + timedelta(days=i * 30),
            )
            for i in range(5)
        ]

        monkeypatch.setattr(
            "openactivity.analysis.segments.get_segment_efforts_chronological",
            lambda s, sid: efforts,
        )
        indicator, rate = compute_segment_trend_indicator(None, 100)
        assert indicator == "↑"
        assert "-" in rate or "+" in rate  # Has sign

    def test_declining_indicator(self, monkeypatch):
        base = datetime(2026, 1, 1)
        efforts = [
            _make_effort(
                elapsed_time=260 + i * 10,
                start_date=base + timedelta(days=i * 30),
            )
            for i in range(5)
        ]

        monkeypatch.setattr(
            "openactivity.analysis.segments.get_segment_efforts_chronological",
            lambda s, sid: efforts,
        )
        indicator, rate = compute_segment_trend_indicator(None, 100)
        assert indicator == "↓"
