"""Tests for race prediction and readiness scoring."""

from __future__ import annotations

from datetime import datetime, timedelta

from openactivity.analysis.predict import (
    DISTANCES,
    compute_confidence_interval,
    compute_pr_recency,
    compute_readiness_score,
    predict_race_time,
    riegel_predict,
)


# ---- Tests for riegel_predict ----


class TestRiegelPredict:
    def test_5k_to_10k(self):
        # 5K in 20:00 (1200s) → 10K should be ~41:30ish
        predicted = riegel_predict(1200, 5000, 10000)
        assert 2400 < predicted < 2600  # ~40-43 min range

    def test_10k_to_marathon(self):
        # 10K in 42:00 (2520s) → Marathon should be ~3:15-3:30ish
        predicted = riegel_predict(2520, 10000, 42195)
        assert 11000 < predicted < 13000  # ~3:03-3:36 range

    def test_same_distance_returns_same_time(self):
        predicted = riegel_predict(1200, 5000, 5000)
        assert abs(predicted - 1200) < 0.01

    def test_shorter_distance_faster(self):
        # Predicting 1mi from 5K should be faster
        predicted = riegel_predict(1200, 5000, 1609.34)
        assert predicted < 1200

    def test_longer_distance_slower(self):
        # Predicting marathon from 5K should be slower
        predicted = riegel_predict(1200, 5000, 42195)
        assert predicted > 1200


# ---- Tests for predict_race_time ----


def _make_effort(label, distance, time, days_ago=10):
    """Create a mock reference effort dict."""
    return {
        "distance_label": label,
        "distance_display": label,
        "distance_meters": distance,
        "time_seconds": time,
        "pace_per_km": time / (distance / 1000),
        "activity_id": 1,
        "activity_date": datetime.now() - timedelta(days=days_ago),
        "days_ago": days_ago,
        "is_recent": days_ago <= 180,
    }


class TestPredictRaceTime:
    def test_single_reference(self):
        efforts = [_make_effort("5K", 5000, 1200)]
        result = predict_race_time(efforts, 10000)
        assert "predicted_time" in result
        assert result["prediction_source"] == "single"
        assert result["predicted_time"] > 0

    def test_multiple_references(self):
        efforts = [
            _make_effort("1mi", 1609.34, 360),
            _make_effort("5K", 5000, 1200),
            _make_effort("10K", 10000, 2520),
        ]
        result = predict_race_time(efforts, 21097.5)
        assert "predicted_time" in result
        assert result["prediction_source"] == "multi"
        assert result["predicted_time"] > 0

    def test_no_efforts_returns_error(self):
        result = predict_race_time([], 10000)
        assert "error" in result

    def test_prediction_has_confidence(self):
        efforts = [
            _make_effort("5K", 5000, 1200),
            _make_effort("10K", 10000, 2520),
        ]
        result = predict_race_time(efforts, 21097.5)
        assert "confidence_low" in result
        assert "confidence_high" in result
        assert result["confidence_low"] < result["predicted_time"]
        assert result["confidence_high"] > result["predicted_time"]


# ---- Tests for compute_confidence_interval ----


class TestComputeConfidenceInterval:
    def test_baseline_interval(self):
        efforts = [_make_effort("5K", 5000, 1200, days_ago=10)] * 4
        predictions = [2500, 2500, 2500, 2500]
        low, high, pct = compute_confidence_interval(predictions, efforts)
        # Base 2% with 4 efforts, recent, no spread
        assert pct >= 2.0
        assert low < 2500
        assert high > 2500

    def test_widens_with_fewer_references(self):
        # 1 effort should be wider than 4 efforts
        efforts_1 = [_make_effort("5K", 5000, 1200, days_ago=10)]
        efforts_4 = [_make_effort("5K", 5000, 1200, days_ago=10)] * 4
        _, _, pct_1 = compute_confidence_interval([2500], efforts_1)
        _, _, pct_4 = compute_confidence_interval([2500] * 4, efforts_4)
        assert pct_1 > pct_4

    def test_widens_with_old_data(self):
        efforts_recent = [_make_effort("5K", 5000, 1200, days_ago=10)] * 4
        efforts_old = [_make_effort("5K", 5000, 1200, days_ago=120)] * 4
        _, _, pct_recent = compute_confidence_interval([2500] * 4, efforts_recent)
        _, _, pct_old = compute_confidence_interval([2500] * 4, efforts_old)
        assert pct_old > pct_recent

    def test_widens_with_spread(self):
        efforts = [_make_effort("5K", 5000, 1200, days_ago=10)] * 4
        tight = [2500, 2500, 2500, 2500]
        spread = [2300, 2500, 2700, 2400]
        _, _, pct_tight = compute_confidence_interval(tight, efforts)
        _, _, pct_spread = compute_confidence_interval(spread, efforts)
        assert pct_spread > pct_tight


# ---- Tests for readiness components ----


class TestPrRecency:
    def test_recent_pr_scores_high(self):
        efforts = [_make_effort("5K", 5000, 1200, days_ago=7)]
        result = compute_pr_recency(efforts)
        assert result["score"] == 100

    def test_old_pr_scores_low(self):
        efforts = [_make_effort("5K", 5000, 1200, days_ago=200)]
        result = compute_pr_recency(efforts)
        assert result["score"] == 20

    def test_no_efforts_scores_zero(self):
        result = compute_pr_recency([])
        assert result["score"] == 0

    def test_medium_recency(self):
        efforts = [_make_effort("5K", 5000, 1200, days_ago=45)]
        result = compute_pr_recency(efforts)
        assert result["score"] == 70


# ---- Tests for compute_readiness_score ----


class TestComputeReadinessScore:
    def test_weighted_calculation(self):
        consistency = {"score": 80, "weight": 0.30, "description": ""}
        volume = {"score": 70, "weight": 0.25, "description": ""}
        taper = {"score": 90, "weight": 0.25, "description": ""}
        recency = {"score": 60, "weight": 0.20, "description": ""}
        result = compute_readiness_score(consistency, volume, taper, recency)
        expected = int(80 * 0.30 + 70 * 0.25 + 90 * 0.25 + 60 * 0.20)
        assert result["overall"] == expected

    def test_label_not_ready(self):
        comp = {"score": 20, "weight": 0.25, "description": ""}
        result = compute_readiness_score(comp, comp, comp, comp)
        assert result["label"] == "Not Ready"

    def test_label_race_ready(self):
        comp = {"score": 90, "weight": 0.25, "description": ""}
        result = compute_readiness_score(comp, comp, comp, comp)
        assert result["label"] == "Race Ready"

    def test_label_building(self):
        comp = {"score": 50, "weight": 0.25, "description": ""}
        result = compute_readiness_score(comp, comp, comp, comp)
        assert result["label"] == "Building"

    def test_label_almost_ready(self):
        comp = {"score": 70, "weight": 0.25, "description": ""}
        result = compute_readiness_score(comp, comp, comp, comp)
        assert result["label"] == "Almost Ready"

    def test_clamped_to_0_100(self):
        high = {"score": 150, "weight": 0.25, "description": ""}
        result = compute_readiness_score(high, high, high, high)
        assert result["overall"] <= 100

        low = {"score": -50, "weight": 0.25, "description": ""}
        result = compute_readiness_score(low, low, low, low)
        assert result["overall"] >= 0
