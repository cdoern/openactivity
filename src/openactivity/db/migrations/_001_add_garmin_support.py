"""Add Garmin provider support to the database schema.

This migration:
1. Adds provider and provider_id columns to activities table
2. Backfills provider_id for existing Strava activities
3. Creates activity_links table for deduplication
4. Creates garmin_daily_summary table for health metrics
5. Creates garmin_sleep_session table for sleep tracking
"""

from __future__ import annotations

from sqlalchemy import CheckConstraint, Index, inspect, text
from sqlalchemy.engine import Engine


def migrate(engine: Engine) -> None:
    """Apply Garmin provider support migration."""
    inspector = inspect(engine)

    with engine.connect() as conn:
        # Step 1: Extend Activity table with provider support
        if "activities" in inspector.get_table_names():
            existing_columns = {c["name"] for c in inspector.get_columns("activities")}

            if "provider" not in existing_columns:
                conn.execute(
                    text(
                        "ALTER TABLE activities ADD COLUMN provider VARCHAR(20) "
                        "DEFAULT 'strava' NOT NULL"
                    )
                )

            if "provider_id" not in existing_columns:
                conn.execute(
                    text("ALTER TABLE activities ADD COLUMN provider_id INTEGER")
                )

                # Backfill provider_id for existing Strava activities
                conn.execute(
                    text("UPDATE activities SET provider_id = id WHERE provider = 'strava'")
                )

            # Check if index exists and create if not
            existing_indexes = {idx["name"] for idx in inspector.get_indexes("activities")}
            if "ix_activity_provider" not in existing_indexes:
                conn.execute(
                    text("CREATE INDEX ix_activity_provider ON activities(provider, provider_id)")
                )

        # Step 2: Create ActivityLink table
        if "activity_links" not in inspector.get_table_names():
            conn.execute(
                text(
                    """
                    CREATE TABLE activity_links (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strava_activity_id INTEGER REFERENCES activities(id) ON DELETE CASCADE,
                        garmin_activity_id INTEGER REFERENCES activities(id) ON DELETE CASCADE,
                        primary_provider VARCHAR(20) NOT NULL,
                        match_confidence REAL NOT NULL CHECK(match_confidence BETWEEN 0.0 AND 1.0),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CHECK (strava_activity_id IS NOT NULL OR garmin_activity_id IS NOT NULL)
                    )
                    """
                )
            )

        # Step 3: Create GarminDailySummary table
        if "garmin_daily_summary" not in inspector.get_table_names():
            conn.execute(
                text(
                    """
                    CREATE TABLE garmin_daily_summary (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE UNIQUE NOT NULL,
                        resting_hr INTEGER CHECK(resting_hr BETWEEN 30 AND 200),
                        hrv_avg INTEGER CHECK(hrv_avg BETWEEN 0 AND 300),
                        body_battery_max INTEGER CHECK(body_battery_max BETWEEN 0 AND 100),
                        body_battery_min INTEGER CHECK(body_battery_min BETWEEN 0 AND 100),
                        stress_avg INTEGER CHECK(stress_avg BETWEEN 0 AND 100),
                        sleep_score INTEGER CHECK(sleep_score BETWEEN 0 AND 100),
                        steps INTEGER CHECK(steps >= 0),
                        respiration_avg REAL CHECK(respiration_avg BETWEEN 0 AND 60),
                        spo2_avg REAL CHECK(spo2_avg BETWEEN 70 AND 100),
                        synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )

        # Step 4: Create GarminSleepSession table
        if "garmin_sleep_session" not in inspector.get_table_names():
            conn.execute(
                text(
                    """
                    CREATE TABLE garmin_sleep_session (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL,
                        start_time TIMESTAMP NOT NULL,
                        end_time TIMESTAMP NOT NULL,
                        total_duration_seconds INTEGER NOT NULL CHECK(total_duration_seconds > 0),
                        deep_duration_seconds INTEGER CHECK(deep_duration_seconds >= 0),
                        light_duration_seconds INTEGER CHECK(light_duration_seconds >= 0),
                        rem_duration_seconds INTEGER CHECK(rem_duration_seconds >= 0),
                        awake_duration_seconds INTEGER CHECK(awake_duration_seconds >= 0),
                        sleep_score INTEGER CHECK(sleep_score BETWEEN 0 AND 100),
                        synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CHECK (start_time < end_time)
                    )
                    """
                )
            )

            # Create indexes for sleep session
            conn.execute(text("CREATE INDEX ix_sleep_date ON garmin_sleep_session(date)"))
            conn.execute(
                text("CREATE INDEX ix_sleep_start ON garmin_sleep_session(start_time)")
            )

        conn.commit()
