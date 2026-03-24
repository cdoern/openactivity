"""Unit tests for FIT file parsing (T029)."""

from __future__ import annotations

from pathlib import Path

import pytest

from openactivity.providers.garmin.fit_parser import FitActivityParser, parse_fit_file

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
SAMPLE_DIR = FIXTURES_DIR / "sample_activities"
EDGE_DIR = FIXTURES_DIR / "edge_cases"


# === FitActivityParser Tests ===


class TestFitActivityParser:
    """Test the FitActivityParser class directly."""

    def test_parse_running_activity(self) -> None:
        parser = FitActivityParser(SAMPLE_DIR / "run_5k.fit")
        result = parser.parse()

        assert result is not None
        assert result["provider"] == "garmin"
        assert result["type"] == "Run"
        assert result["sport_type"] == "running"
        assert result["distance"] == pytest.approx(5000.0, rel=0.01)
        assert result["elapsed_time"] == 1800
        assert result["moving_time"] == 1750
        assert result["average_heartrate"] == 155
        assert result["max_heartrate"] == 180
        assert result["has_heartrate"] is True
        assert result["start_date"] is not None
        assert isinstance(result["provider_id"], int)

    def test_parse_cycling_activity(self) -> None:
        parser = FitActivityParser(SAMPLE_DIR / "ride_30k.fit")
        result = parser.parse()

        assert result is not None
        assert result["type"] == "Ride"
        assert result["sport_type"] == "cycling"
        assert result["distance"] == pytest.approx(30000.0, rel=0.01)
        assert result["elapsed_time"] == 3600
        assert result["average_heartrate"] == 140

    def test_parse_swimming_activity(self) -> None:
        parser = FitActivityParser(SAMPLE_DIR / "swim_1500.fit")
        result = parser.parse()

        assert result is not None
        assert result["type"] == "Swim"
        assert result["sport_type"] == "swimming"
        assert result["distance"] == pytest.approx(1500.0, rel=0.01)

    def test_parse_non_activity_returns_none(self) -> None:
        parser = FitActivityParser(EDGE_DIR / "non_activity.fit")
        result = parser.parse()
        assert result is None

    def test_parse_empty_file_returns_none(self) -> None:
        result = parse_fit_file(EDGE_DIR / "empty.fit")
        assert result is None

    def test_parse_corrupted_file_returns_none(self) -> None:
        result = parse_fit_file(EDGE_DIR / "corrupted.fit")
        assert result is None

    def test_parse_minimal_activity(self) -> None:
        parser = FitActivityParser(EDGE_DIR / "minimal.fit")
        result = parser.parse()

        assert result is not None
        assert result["type"] == "Run"
        assert result["distance"] == pytest.approx(100.0, rel=0.01)
        assert result["elapsed_time"] == 60

    def test_provider_id_is_stable(self) -> None:
        """Provider ID should be deterministic based on start_time."""
        parser = FitActivityParser(SAMPLE_DIR / "run_5k.fit")
        result1 = parser.parse()

        parser2 = FitActivityParser(SAMPLE_DIR / "run_5k.fit")
        result2 = parser2.parse()

        assert result1["provider_id"] == result2["provider_id"]

    def test_name_is_generated(self) -> None:
        parser = FitActivityParser(SAMPLE_DIR / "run_5k.fit")
        result = parser.parse()

        assert result["name"] is not None
        assert "Garmin Activity" in result["name"]

    def test_total_elevation_gain(self) -> None:
        parser = FitActivityParser(SAMPLE_DIR / "run_5k.fit")
        result = parser.parse()

        assert result["total_elevation_gain"] == 120

    def test_average_speed_parsed(self) -> None:
        parser = FitActivityParser(SAMPLE_DIR / "run_5k.fit")
        result = parser.parse()

        assert result["average_speed"] == pytest.approx(2.78, rel=0.01)


# === Sport Type Normalization ===


class TestSportTypeNormalization:
    """Test the _normalize_activity_type method."""

    def test_running_maps_to_run(self) -> None:
        parser = FitActivityParser(SAMPLE_DIR / "run_5k.fit")
        assert parser._normalize_activity_type("running") == "Run"

    def test_cycling_maps_to_ride(self) -> None:
        parser = FitActivityParser(SAMPLE_DIR / "run_5k.fit")
        assert parser._normalize_activity_type("cycling") == "Ride"

    def test_swimming_maps_to_swim(self) -> None:
        parser = FitActivityParser(SAMPLE_DIR / "run_5k.fit")
        assert parser._normalize_activity_type("swimming") == "Swim"

    def test_walking_maps_to_walk(self) -> None:
        parser = FitActivityParser(SAMPLE_DIR / "run_5k.fit")
        assert parser._normalize_activity_type("walking") == "Walk"

    def test_hiking_maps_to_hike(self) -> None:
        parser = FitActivityParser(SAMPLE_DIR / "run_5k.fit")
        assert parser._normalize_activity_type("hiking") == "Hike"

    def test_generic_maps_to_workout(self) -> None:
        parser = FitActivityParser(SAMPLE_DIR / "run_5k.fit")
        assert parser._normalize_activity_type("generic") == "Workout"

    def test_unknown_sport_capitalized(self) -> None:
        parser = FitActivityParser(SAMPLE_DIR / "run_5k.fit")
        assert parser._normalize_activity_type("snowboarding") == "Snowboarding"

    def test_none_sport_returns_workout(self) -> None:
        parser = FitActivityParser(SAMPLE_DIR / "run_5k.fit")
        assert parser._normalize_activity_type(None) == "Workout"

    def test_case_insensitive(self) -> None:
        parser = FitActivityParser(SAMPLE_DIR / "run_5k.fit")
        assert parser._normalize_activity_type("Running") == "Run"
        assert parser._normalize_activity_type("CYCLING") == "Ride"


# === parse_fit_file convenience function ===


class TestParseFitFile:
    """Test the parse_fit_file convenience function."""

    def test_valid_file(self) -> None:
        result = parse_fit_file(SAMPLE_DIR / "run_5k.fit")
        assert result is not None
        assert result["type"] == "Run"

    def test_nonexistent_file_returns_none(self) -> None:
        result = parse_fit_file(Path("/nonexistent/path/fake.fit"))
        assert result is None

    def test_corrupted_file_returns_none(self) -> None:
        result = parse_fit_file(EDGE_DIR / "corrupted.fit")
        assert result is None

    def test_non_activity_returns_none(self) -> None:
        result = parse_fit_file(EDGE_DIR / "non_activity.fit")
        assert result is None
