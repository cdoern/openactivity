"""Unit tests for custom time-range comparison analysis."""

from __future__ import annotations

from datetime import date

import pytest

from openactivity.analysis.compare import (
    RangeMetrics,
    comparison_to_dict,
    compute_comparison,
    detect_overlap,
    format_pct_change,
    parse_date_range,
)

# === Phase 2: Date parsing & validation tests ===


class TestParseDateRange:
    def test_valid_range(self) -> None:
        start, end = parse_date_range("2025-01-01:2025-03-31")
        assert start == date(2025, 1, 1)
        assert end == date(2025, 3, 31)

    def test_single_day_range(self) -> None:
        start, end = parse_date_range("2025-06-15:2025-06-15")
        assert start == end == date(2025, 6, 15)

    def test_invalid_format_no_colon(self) -> None:
        with pytest.raises(ValueError, match="Invalid date range format"):
            parse_date_range("2025-01-01 2025-03-31")

    def test_invalid_format_bad_date(self) -> None:
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_range("01-2025:03-2025")

    def test_start_after_end(self) -> None:
        with pytest.raises(ValueError, match="start date .* must be before"):
            parse_date_range("2025-03-31:2025-01-01")

    def test_invalid_month(self) -> None:
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_range("2025-13-01:2025-12-31")

    def test_whitespace_handling(self) -> None:
        start, end = parse_date_range(" 2025-01-01 : 2025-03-31 ")
        assert start == date(2025, 1, 1)
        assert end == date(2025, 3, 31)


class TestDetectOverlap:
    def test_no_overlap(self) -> None:
        r1 = (date(2025, 1, 1), date(2025, 3, 31))
        r2 = (date(2025, 4, 1), date(2025, 6, 30))
        assert detect_overlap(r1, r2) is False

    def test_overlap(self) -> None:
        r1 = (date(2025, 1, 1), date(2025, 6, 30))
        r2 = (date(2025, 3, 1), date(2025, 9, 30))
        assert detect_overlap(r1, r2) is True

    def test_adjacent_no_overlap(self) -> None:
        r1 = (date(2025, 1, 1), date(2025, 1, 31))
        r2 = (date(2025, 2, 1), date(2025, 2, 28))
        assert detect_overlap(r1, r2) is False

    def test_shared_boundary(self) -> None:
        r1 = (date(2025, 1, 1), date(2025, 3, 31))
        r2 = (date(2025, 3, 31), date(2025, 6, 30))
        assert detect_overlap(r1, r2) is True

    def test_identical_ranges(self) -> None:
        r = (date(2025, 1, 1), date(2025, 3, 31))
        assert detect_overlap(r, r) is True

    def test_one_contains_other(self) -> None:
        r1 = (date(2025, 1, 1), date(2025, 12, 31))
        r2 = (date(2025, 3, 1), date(2025, 6, 30))
        assert detect_overlap(r1, r2) is True


# === Phase 3 US1: Comparison logic tests ===


class TestComputeComparison:
    def _make_metrics(
        self,
        *,
        count: int = 0,
        distance: float = 0.0,
        moving_time: int = 0,
        elevation_gain: float = 0.0,
        avg_heartrate: float | None = None,
        avg_pace: float | None = None,
    ) -> RangeMetrics:
        return RangeMetrics(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
            count=count,
            distance=distance,
            moving_time=moving_time,
            elevation_gain=elevation_gain,
            avg_heartrate=avg_heartrate,
            avg_pace=avg_pace,
        )

    def test_basic_deltas(self) -> None:
        r1 = self._make_metrics(count=10, distance=50000.0, moving_time=18000)
        r2 = self._make_metrics(count=15, distance=75000.0, moving_time=27000)
        result = compute_comparison(r1, r2)

        assert result.deltas["count"] == 5
        assert result.deltas["distance_m"] == 25000.0
        assert result.deltas["moving_time_s"] == 9000

    def test_percentage_changes(self) -> None:
        r1 = self._make_metrics(count=10, distance=100000.0)
        r2 = self._make_metrics(count=12, distance=120000.0)
        result = compute_comparison(r1, r2)

        assert result.pct_changes["count"] == pytest.approx(20.0)
        assert result.pct_changes["distance_m"] == pytest.approx(20.0)

    def test_zero_base_pct_is_none(self) -> None:
        r1 = self._make_metrics(count=0, distance=0.0)
        r2 = self._make_metrics(count=5, distance=10000.0)
        result = compute_comparison(r1, r2)

        assert result.pct_changes["count"] is None
        assert result.pct_changes["distance_m"] is None

    def test_both_zero_pct_is_zero(self) -> None:
        r1 = self._make_metrics(count=0, distance=0.0)
        r2 = self._make_metrics(count=0, distance=0.0)
        result = compute_comparison(r1, r2)

        assert result.pct_changes["count"] == 0.0
        assert result.pct_changes["distance_m"] == 0.0

    def test_heartrate_included_when_present(self) -> None:
        r1 = self._make_metrics(avg_heartrate=145.0)
        r2 = self._make_metrics(avg_heartrate=140.0)
        result = compute_comparison(r1, r2)

        assert "avg_heartrate" in result.deltas
        assert result.deltas["avg_heartrate"] == pytest.approx(-5.0)

    def test_heartrate_excluded_when_absent(self) -> None:
        r1 = self._make_metrics()
        r2 = self._make_metrics()
        result = compute_comparison(r1, r2)

        assert "avg_heartrate" not in result.deltas

    def test_negative_delta(self) -> None:
        r1 = self._make_metrics(count=20, distance=200000.0)
        r2 = self._make_metrics(count=10, distance=100000.0)
        result = compute_comparison(r1, r2)

        assert result.deltas["count"] == -10
        assert result.pct_changes["count"] == pytest.approx(-50.0)

    def test_overlap_flag_passed_through(self) -> None:
        r1 = self._make_metrics()
        r2 = self._make_metrics()
        result = compute_comparison(r1, r2, overlap=True)
        assert result.overlap is True

    def test_activity_type_passed_through(self) -> None:
        r1 = self._make_metrics()
        r2 = self._make_metrics()
        result = compute_comparison(r1, r2, activity_type="Run")
        assert result.activity_type == "Run"


class TestFormatPctChange:
    def test_positive(self) -> None:
        assert format_pct_change(21.4) == "+21.4%"

    def test_negative(self) -> None:
        assert format_pct_change(-4.5) == "-4.5%"

    def test_none_returns_na(self) -> None:
        assert format_pct_change(None) == "N/A"

    def test_zero_returns_dash(self) -> None:
        assert format_pct_change(0.0) == "—"

    def test_small_positive(self) -> None:
        assert format_pct_change(0.1) == "+0.1%"


# === Phase 5 US3: JSON serialization tests ===


class TestComparisonToDict:
    def test_basic_structure(self) -> None:
        r1 = RangeMetrics(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
            count=10,
            distance=50000.0,
            moving_time=18000,
            elevation_gain=500.0,
        )
        r2 = RangeMetrics(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            count=15,
            distance=75000.0,
            moving_time=27000,
            elevation_gain=800.0,
        )
        comparison = compute_comparison(r1, r2)
        result = comparison_to_dict(comparison, units="metric")

        assert "metadata" in result
        assert "range1" in result
        assert "range2" in result
        assert "deltas" in result
        assert "pct_changes" in result

    def test_metadata_fields(self) -> None:
        r1 = RangeMetrics(start_date=date(2025, 1, 1), end_date=date(2025, 3, 31))
        r2 = RangeMetrics(start_date=date(2026, 1, 1), end_date=date(2026, 3, 31))
        comparison = compute_comparison(r1, r2, activity_type="Run", overlap=True)
        result = comparison_to_dict(comparison, units="imperial")

        meta = result["metadata"]
        assert meta["range1"]["start"] == "2025-01-01"
        assert meta["range1"]["end"] == "2025-03-31"
        assert meta["range2"]["start"] == "2026-01-01"
        assert meta["activity_type"] == "Run"
        assert meta["units"] == "imperial"
        assert meta["overlap"] is True

    def test_heartrate_included_when_present(self) -> None:
        r1 = RangeMetrics(
            start_date=date(2025, 1, 1), end_date=date(2025, 3, 31),
            avg_heartrate=148.0,
        )
        r2 = RangeMetrics(
            start_date=date(2026, 1, 1), end_date=date(2026, 3, 31),
            avg_heartrate=145.0,
        )
        comparison = compute_comparison(r1, r2)
        result = comparison_to_dict(comparison)

        assert result["range1"]["avg_heartrate"] == 148.0
        assert result["range2"]["avg_heartrate"] == 145.0

    def test_heartrate_excluded_when_absent(self) -> None:
        r1 = RangeMetrics(start_date=date(2025, 1, 1), end_date=date(2025, 3, 31))
        r2 = RangeMetrics(start_date=date(2026, 1, 1), end_date=date(2026, 3, 31))
        comparison = compute_comparison(r1, r2)
        result = comparison_to_dict(comparison)

        assert "avg_heartrate" not in result["range1"]
        assert "avg_heartrate" not in result["range2"]

    def test_none_pct_change_serialized(self) -> None:
        r1 = RangeMetrics(
            start_date=date(2025, 1, 1), end_date=date(2025, 3, 31),
            count=0, distance=0.0,
        )
        r2 = RangeMetrics(
            start_date=date(2026, 1, 1), end_date=date(2026, 3, 31),
            count=5, distance=10000.0,
        )
        comparison = compute_comparison(r1, r2)
        result = comparison_to_dict(comparison)

        assert result["pct_changes"]["count"] is None
