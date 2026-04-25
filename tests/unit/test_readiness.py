"""Tests for recovery & readiness scoring logic."""

from __future__ import annotations

from datetime import date, timedelta

from openactivity.analysis.readiness import (
    ComponentScore,
    ReadinessResult,
    classify_readiness,
    compute_readiness,
)


# ── classify_readiness tests ──────────────────────────────────────


class TestClassifyReadiness:
    def test_go_hard(self):
        label, rec = classify_readiness(80)
        assert label == "Go Hard"

    def test_easy_day(self):
        label, rec = classify_readiness(50)
        assert label == "Easy Day"

    def test_rest(self):
        label, rec = classify_readiness(30)
        assert label == "Rest"

    def test_boundary_75(self):
        label, _ = classify_readiness(75)
        assert label == "Go Hard"

    def test_boundary_40(self):
        label, _ = classify_readiness(40)
        assert label == "Easy Day"

    def test_zero(self):
        label, _ = classify_readiness(0)
        assert label == "Rest"

    def test_100(self):
        label, _ = classify_readiness(100)
        assert label == "Go Hard"


# ── ComponentScore tests ──────────────────────────────────────────


class TestComponentScore:
    def test_creation(self):
        c = ComponentScore(
            name="hrv", score=75, weight=0.30, available=True,
            description="test",
        )
        assert c.name == "hrv"
        assert c.score == 75
        assert c.weight == 0.30
        assert c.available is True

    def test_unavailable(self):
        c = ComponentScore(
            name="sleep", score=0, weight=0.20, available=False,
            description="Sleep data unavailable",
        )
        assert c.available is False
        assert c.score == 0


# ── ReadinessResult tests ────────────────────────────────────────


class TestReadinessResult:
    def test_creation(self):
        r = ReadinessResult(
            date=date(2026, 4, 3),
            score=72,
            label="Easy Day",
            recommendation="Keep it light.",
            components=[],
        )
        assert r.score == 72
        assert r.label == "Easy Day"

    def test_default_components(self):
        r = ReadinessResult(
            date=date(2026, 4, 3),
            score=50,
            label="Easy Day",
            recommendation="test",
        )
        assert r.components == []


# ── Weight redistribution tests ──────────────────────────────────


class TestWeightRedistribution:
    """Test that compute_readiness redistributes weights correctly."""

    def test_all_unavailable_returns_zero(self):
        """When no components have data, score should be 0."""
        from unittest.mock import patch

        unavailable = ComponentScore(
            name="test", score=0, weight=0.25, available=False,
            description="unavailable",
        )

        with patch(
            "openactivity.analysis.readiness.compute_hrv_score",
            return_value=unavailable,
        ), patch(
            "openactivity.analysis.readiness.compute_sleep_score",
            return_value=unavailable,
        ), patch(
            "openactivity.analysis.readiness.compute_form_score",
            return_value=unavailable,
        ), patch(
            "openactivity.analysis.readiness.compute_volume_score",
            return_value=unavailable,
        ):
            result = compute_readiness(None, date(2026, 4, 3))
            assert result.score == 0
            assert result.label == "Unknown"

    def test_partial_data_redistributes_weights(self):
        """When some components are unavailable, weights should sum to 1.0."""
        from unittest.mock import patch

        hrv = ComponentScore(
            name="hrv", score=80, weight=0.30, available=True,
            description="HRV good",
        )
        sleep_unavail = ComponentScore(
            name="sleep", score=0, weight=0.20, available=False,
            description="unavailable",
        )
        form = ComponentScore(
            name="form", score=70, weight=0.30, available=True,
            description="form ok",
        )
        volume_unavail = ComponentScore(
            name="volume", score=0, weight=0.20, available=False,
            description="unavailable",
        )

        with patch(
            "openactivity.analysis.readiness.compute_hrv_score",
            return_value=hrv,
        ), patch(
            "openactivity.analysis.readiness.compute_sleep_score",
            return_value=sleep_unavail,
        ), patch(
            "openactivity.analysis.readiness.compute_form_score",
            return_value=form,
        ), patch(
            "openactivity.analysis.readiness.compute_volume_score",
            return_value=volume_unavail,
        ):
            result = compute_readiness(None, date(2026, 4, 3))
            # With HRV=80 and Form=70, each at 0.5 weight: 80*0.5 + 70*0.5 = 75
            assert result.score == 75
            assert result.label == "Go Hard"

    def test_all_available_uses_original_weights(self):
        """When all components are available, normalized weights = original."""
        from unittest.mock import patch

        hrv = ComponentScore(
            name="hrv", score=80, weight=0.30, available=True,
            description="hrv",
        )
        sleep = ComponentScore(
            name="sleep", score=60, weight=0.20, available=True,
            description="sleep",
        )
        form = ComponentScore(
            name="form", score=70, weight=0.30, available=True,
            description="form",
        )
        volume = ComponentScore(
            name="volume", score=50, weight=0.20, available=True,
            description="volume",
        )

        with patch(
            "openactivity.analysis.readiness.compute_hrv_score",
            return_value=hrv,
        ), patch(
            "openactivity.analysis.readiness.compute_sleep_score",
            return_value=sleep,
        ), patch(
            "openactivity.analysis.readiness.compute_form_score",
            return_value=form,
        ), patch(
            "openactivity.analysis.readiness.compute_volume_score",
            return_value=volume,
        ):
            result = compute_readiness(None, date(2026, 4, 3))
            # 80*0.30 + 60*0.20 + 70*0.30 + 50*0.20 = 24+12+21+10 = 67
            assert result.score == 67
            assert result.label == "Easy Day"


# ── Edge case tests ──────────────────────────────────────────────


class TestEdgeCases:
    def test_score_clamped_to_0_100(self):
        """Scores should always be 0-100."""
        from unittest.mock import patch

        high = ComponentScore(
            name="hrv", score=100, weight=0.30, available=True,
            description="max",
        )
        sleep = ComponentScore(
            name="sleep", score=100, weight=0.20, available=True,
            description="max",
        )
        form = ComponentScore(
            name="form", score=100, weight=0.30, available=True,
            description="max",
        )
        volume = ComponentScore(
            name="volume", score=100, weight=0.20, available=True,
            description="max",
        )

        with patch(
            "openactivity.analysis.readiness.compute_hrv_score",
            return_value=high,
        ), patch(
            "openactivity.analysis.readiness.compute_sleep_score",
            return_value=sleep,
        ), patch(
            "openactivity.analysis.readiness.compute_form_score",
            return_value=form,
        ), patch(
            "openactivity.analysis.readiness.compute_volume_score",
            return_value=volume,
        ):
            result = compute_readiness(None, date(2026, 4, 3))
            assert 0 <= result.score <= 100
