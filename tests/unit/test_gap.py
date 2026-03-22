"""Tests for GAP computation and effort scoring."""

from __future__ import annotations

import pytest

from openactivity.analysis.gap import (
    FLAT_COST,
    EffortScoreResult,
    GAPResult,
    compute_effort_score,
    compute_grades,
    minetti_cost,
)


# ---- Tests for compute_grades ----


class TestComputeGrades:
    """Tests for grade computation from altitude and distance streams."""

    def test_flat_terrain_returns_zero_grades(self):
        """Flat terrain should produce grades near zero."""
        altitude = [100.0] * 20
        distance = [float(i * 10) for i in range(20)]
        grades = compute_grades(altitude, distance)
        assert len(grades) > 0
        for g in grades:
            assert abs(g) < 0.01

    def test_uphill_returns_positive_grades(self):
        """Consistent uphill should produce positive grades."""
        # 1m rise per 10m distance = 10% grade
        altitude = [float(i) for i in range(20)]
        distance = [float(i * 10) for i in range(20)]
        grades = compute_grades(altitude, distance)
        assert len(grades) > 0
        for g in grades:
            assert g > 0

    def test_downhill_returns_negative_grades(self):
        """Consistent downhill should produce negative grades."""
        altitude = [100.0 - float(i) for i in range(20)]
        distance = [float(i * 10) for i in range(20)]
        grades = compute_grades(altitude, distance)
        assert len(grades) > 0
        for g in grades:
            assert g < 0

    def test_smoothing_reduces_noise(self):
        """Smoothing should reduce extreme spikes in noisy data."""
        # Alternating flat and spike
        altitude = [100.0 + (5.0 if i % 2 == 0 else 0.0) for i in range(20)]
        distance = [float(i * 10) for i in range(20)]

        grades = compute_grades(altitude, distance)
        # With smoothing, no grade should be as extreme as the raw value
        for g in grades:
            assert abs(g) < 0.5  # Raw would be ±0.5

    def test_too_few_points_returns_empty(self):
        """Fewer than 2 points should return empty list."""
        assert compute_grades([100.0], [0.0]) == []
        assert compute_grades([], []) == []


# ---- Tests for minetti_cost ----


class TestMinettiCost:
    """Tests for the Minetti energy cost model."""

    def test_flat_grade_returns_3_6(self):
        """Flat grade (0) should return FLAT_COST = 3.6 J/kg/m."""
        assert minetti_cost(0.0) == pytest.approx(3.6, abs=0.01)

    def test_uphill_costs_more_than_flat(self):
        """Uphill grades should cost more energy than flat."""
        for grade in [0.05, 0.10, 0.15, 0.20]:
            assert minetti_cost(grade) > FLAT_COST

    def test_moderate_downhill_costs_less_than_flat(self):
        """Moderate downhill should cost less than flat."""
        # Moderate downhill (-5% to -10%) should be cheaper
        assert minetti_cost(-0.05) < FLAT_COST

    def test_steep_uphill_more_than_gentle(self):
        """Steeper uphill should cost more than gentle uphill."""
        assert minetti_cost(0.15) > minetti_cost(0.05)

    def test_cost_clamped_to_minimum(self):
        """Very steep downhill should be clamped to minimum 1.0."""
        # At extreme downhill, polynomial can go negative
        cost = minetti_cost(-0.5)
        assert cost >= 1.0


# ---- Tests for compute_gap (unit-level, testing via GAPResult) ----


class TestComputeGapResult:
    """Tests for GAP result structure and behavior."""

    def test_unavailable_result_structure(self):
        """Unavailable GAP result should have correct structure."""
        result = GAPResult(
            overall_gap=None, lap_gaps=[], grade_profile=[], available=False
        )
        assert result.available is False
        assert result.overall_gap is None

    def test_available_result_structure(self):
        """Available GAP result should have non-None values."""
        result = GAPResult(
            overall_gap=3.5, lap_gaps=[3.4, 3.6], grade_profile=[0.01], available=True
        )
        assert result.available is True
        assert result.overall_gap == 3.5
        assert len(result.lap_gaps) == 2


# ---- Tests for compute_effort_score ----


class TestComputeEffortScore:
    """Tests for effort score computation."""

    def _make_activity(self, **kwargs):
        """Create a mock activity-like object."""

        class MockActivity:
            pass

        a = MockActivity()
        a.moving_time = kwargs.get("moving_time", 1800)
        a.average_speed = kwargs.get("average_speed", 3.5)
        a.distance = kwargs.get("distance", 5000.0)
        a.total_elevation_gain = kwargs.get("total_elevation_gain", 50.0)
        a.average_heartrate = kwargs.get("average_heartrate", None)
        a.max_heartrate = kwargs.get("max_heartrate", None)
        return a

    def _make_stats(self):
        """Create sample user stats distribution."""
        return {
            "durations": [1200, 1500, 1800, 2100, 2400, 2700, 3000, 3600],
            "gap_speeds": [2.5, 3.0, 3.2, 3.5, 3.8, 4.0, 4.2, 4.5],
            "elev_per_kms": [5, 10, 15, 20, 30, 40, 50, 80],
            "estimated_max_hr": 190,
        }

    def test_score_range_0_to_100(self):
        """Effort score should always be 0-100."""
        activity = self._make_activity()
        gap = GAPResult(overall_gap=3.5, lap_gaps=[], grade_profile=[], available=True)
        result = compute_effort_score(activity, gap, self._make_stats())
        assert 0 <= result.score <= 100

    def test_harder_effort_scores_higher(self):
        """Longer, faster, more elevation should score higher."""
        easy = self._make_activity(
            moving_time=1200, average_speed=2.5,
            distance=3000, total_elevation_gain=10
        )
        hard = self._make_activity(
            moving_time=3600, average_speed=4.5,
            distance=16000, total_elevation_gain=200
        )
        gap_easy = GAPResult(
            overall_gap=2.5, lap_gaps=[], grade_profile=[], available=True
        )
        gap_hard = GAPResult(
            overall_gap=4.5, lap_gaps=[], grade_profile=[], available=True
        )
        stats = self._make_stats()

        easy_score = compute_effort_score(easy, gap_easy, stats)
        hard_score = compute_effort_score(hard, gap_hard, stats)

        assert hard_score.score > easy_score.score

    def test_missing_hr_redistributes_weights(self):
        """Without HR, components should use 33.3% weights each."""
        activity = self._make_activity(average_heartrate=None)
        gap = GAPResult(overall_gap=3.5, lap_gaps=[], grade_profile=[], available=True)
        result = compute_effort_score(activity, gap, self._make_stats())
        assert result.hr_component is None
        # Total should still be valid 0-100
        assert 0 <= result.score <= 100

    def test_with_hr_has_four_components(self):
        """With HR, all four components should be present."""
        activity = self._make_activity(average_heartrate=155)
        gap = GAPResult(overall_gap=3.5, lap_gaps=[], grade_profile=[], available=True)
        result = compute_effort_score(activity, gap, self._make_stats())
        assert result.hr_component is not None

    def test_short_easy_run_scores_low(self):
        """A very short easy jog should score low."""
        activity = self._make_activity(
            moving_time=600, average_speed=2.0,
            distance=1200, total_elevation_gain=5
        )
        gap = GAPResult(
            overall_gap=2.0, lap_gaps=[], grade_profile=[], available=True
        )
        stats = self._make_stats()
        result = compute_effort_score(activity, gap, stats)
        assert result.score <= 30
