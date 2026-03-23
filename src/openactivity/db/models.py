"""SQLAlchemy model definitions for local data storage."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - needed at runtime by SQLAlchemy Mapped

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Athlete(Base):
    __tablename__ = "athletes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    firstname: Mapped[str | None] = mapped_column(String, nullable=True)
    lastname: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    state: Mapped[str | None] = mapped_column(String, nullable=True)
    country: Mapped[str | None] = mapped_column(String, nullable=True)
    measurement_pref: Mapped[str | None] = mapped_column(String, nullable=True)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    ftp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class AthleteStats(Base):
    __tablename__ = "athlete_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    athlete_id: Mapped[int] = mapped_column(Integer, nullable=False)
    stat_type: Mapped[str] = mapped_column(String, nullable=False)  # "ytd" or "all_time"
    activity_type: Mapped[str] = mapped_column(String, nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=0)
    distance: Mapped[float] = mapped_column(Float, default=0.0)
    moving_time: Mapped[int] = mapped_column(Integer, default=0)
    elapsed_time: Mapped[int] = mapped_column(Integer, default=0)
    elevation_gain: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[int] = mapped_column(Integer, nullable=False)
    provider: Mapped[str] = mapped_column(String, default="strava", nullable=False)
    provider_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    type: Mapped[str | None] = mapped_column(String, nullable=True)
    sport_type: Mapped[str | None] = mapped_column(String, nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    start_date_local: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    timezone: Mapped[str | None] = mapped_column(String, nullable=True)
    distance: Mapped[float] = mapped_column(Float, default=0.0)
    moving_time: Mapped[int] = mapped_column(Integer, default=0)
    elapsed_time: Mapped[int] = mapped_column(Integer, default=0)
    total_elevation_gain: Mapped[float] = mapped_column(Float, default=0.0)
    average_speed: Mapped[float] = mapped_column(Float, default=0.0)
    max_speed: Mapped[float] = mapped_column(Float, default=0.0)
    average_heartrate: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_heartrate: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_cadence: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_watts: Mapped[float | None] = mapped_column(Float, nullable=True)
    weighted_average_watts: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_watts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    kilojoules: Mapped[float | None] = mapped_column(Float, nullable=True)
    calories: Mapped[float | None] = mapped_column(Float, nullable=True)
    suffer_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gear_id: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_heartrate: Mapped[bool] = mapped_column(Boolean, default=False)
    has_power: Mapped[bool] = mapped_column(Boolean, default=False)
    start_latlng: Mapped[str | None] = mapped_column(String, nullable=True)
    end_latlng: Mapped[str | None] = mapped_column(String, nullable=True)
    synced_detail: Mapped[bool] = mapped_column(Boolean, default=False)
    pr_scanned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_activity_athlete_date", "athlete_id", "start_date"),
        Index("ix_activity_type", "type"),
        Index("ix_activity_provider", "provider", "provider_id"),
    )


class Lap(Base):
    __tablename__ = "laps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    lap_index: Mapped[int] = mapped_column(Integer, default=0)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    distance: Mapped[float] = mapped_column(Float, default=0.0)
    moving_time: Mapped[int] = mapped_column(Integer, default=0)
    elapsed_time: Mapped[int] = mapped_column(Integer, default=0)
    total_elevation_gain: Mapped[float] = mapped_column(Float, default=0.0)
    average_speed: Mapped[float] = mapped_column(Float, default=0.0)
    max_speed: Mapped[float] = mapped_column(Float, default=0.0)
    average_heartrate: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_heartrate: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_cadence: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_watts: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_index: Mapped[int] = mapped_column(Integer, default=0)
    end_index: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (Index("ix_lap_activity", "activity_id"),)


class ActivityZone(Base):
    __tablename__ = "activity_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    zone_type: Mapped[str] = mapped_column(String, nullable=False)
    zone_index: Mapped[int] = mapped_column(Integer, nullable=False)
    min_value: Mapped[int] = mapped_column(Integer, default=0)
    max_value: Mapped[int] = mapped_column(Integer, default=-1)
    time_seconds: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (Index("ix_activity_zone_activity", "activity_id"),)


class AthleteZone(Base):
    __tablename__ = "athlete_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    athlete_id: Mapped[int] = mapped_column(Integer, nullable=False)
    zone_type: Mapped[str] = mapped_column(String, nullable=False)
    zone_index: Mapped[int] = mapped_column(Integer, nullable=False)
    min_value: Mapped[int] = mapped_column(Integer, default=0)
    max_value: Mapped[int] = mapped_column(Integer, default=-1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class ActivityStream(Base):
    __tablename__ = "activity_streams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    stream_type: Mapped[str] = mapped_column(String, nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    resolution: Mapped[str] = mapped_column(String, default="high")

    __table_args__ = (Index("ix_stream_activity", "activity_id"),)


class Gear(Base):
    __tablename__ = "gear"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    distance: Mapped[float] = mapped_column(Float, default=0.0)
    brand_name: Mapped[str | None] = mapped_column(String, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String, nullable=True)
    gear_type: Mapped[str | None] = mapped_column(String, nullable=True)


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    activity_type: Mapped[str | None] = mapped_column(String, nullable=True)
    distance: Mapped[float] = mapped_column(Float, default=0.0)
    average_grade: Mapped[float] = mapped_column(Float, default=0.0)
    maximum_grade: Mapped[float] = mapped_column(Float, default=0.0)
    elevation_high: Mapped[float] = mapped_column(Float, default=0.0)
    elevation_low: Mapped[float] = mapped_column(Float, default=0.0)
    total_elevation_gain: Mapped[float] = mapped_column(Float, default=0.0)
    starred: Mapped[bool] = mapped_column(Boolean, default=False)
    pr_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pr_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    effort_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class SegmentEffort(Base):
    __tablename__ = "segment_efforts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    segment_id: Mapped[int] = mapped_column(Integer, nullable=False)
    activity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    elapsed_time: Mapped[int] = mapped_column(Integer, default=0)
    moving_time: Mapped[int] = mapped_column(Integer, default=0)
    start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    pr_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    average_heartrate: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_watts: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (
        Index("ix_effort_segment", "segment_id"),
        Index("ix_effort_activity", "activity_id"),
    )


class PersonalRecord(Base):
    __tablename__ = "personal_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_type: Mapped[str] = mapped_column(String, nullable=False)  # "distance" or "power"
    distance_type: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "5K", "20min"
    value: Mapped[float] = mapped_column(Float, nullable=False)  # seconds or watts
    pace: Mapped[float | None] = mapped_column(Float, nullable=True)  # seconds per meter
    activity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    activity_name: Mapped[str | None] = mapped_column(String, nullable=True)
    achieved_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    distance_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_pr_distance_type", "distance_type"),
        Index("ix_pr_current", "is_current", "distance_type"),
        Index("ix_pr_activity", "activity_id"),
    )


class CustomDistance(Base):
    __tablename__ = "custom_distances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    distance_meters: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SyncState(Base):
    __tablename__ = "sync_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    page_cursor: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="complete")


class ActivityLink(Base):
    __tablename__ = "activity_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strava_activity_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=True
    )
    garmin_activity_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=True
    )
    primary_provider: Mapped[str] = mapped_column(String, nullable=False)
    match_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "strava_activity_id IS NOT NULL OR garmin_activity_id IS NOT NULL",
            name="at_least_one_activity",
        ),
        CheckConstraint(
            "match_confidence BETWEEN 0.0 AND 1.0", name="confidence_range"
        ),
    )


class GarminDailySummary(Base):
    __tablename__ = "garmin_daily_summary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(Date, unique=True, nullable=False)
    resting_hr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hrv_avg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    body_battery_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    body_battery_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stress_avg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sleep_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    respiration_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    spo2_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("resting_hr BETWEEN 30 AND 200", name="resting_hr_range"),
        CheckConstraint("hrv_avg BETWEEN 0 AND 300", name="hrv_range"),
        CheckConstraint("body_battery_max BETWEEN 0 AND 100", name="bb_max_range"),
        CheckConstraint("body_battery_min BETWEEN 0 AND 100", name="bb_min_range"),
        CheckConstraint("stress_avg BETWEEN 0 AND 100", name="stress_range"),
        CheckConstraint("sleep_score BETWEEN 0 AND 100", name="sleep_score_range"),
        CheckConstraint("steps >= 0", name="steps_range"),
        CheckConstraint("respiration_avg BETWEEN 0 AND 60", name="respiration_range"),
        CheckConstraint("spo2_avg BETWEEN 70 AND 100", name="spo2_range"),
    )


class GarminSleepSession(Base):
    __tablename__ = "garmin_sleep_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    total_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    deep_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    light_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rem_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    awake_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sleep_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_sleep_date", "date"),
        Index("ix_sleep_start", "start_time"),
        CheckConstraint("total_duration_seconds > 0", name="total_duration_positive"),
        CheckConstraint("deep_duration_seconds >= 0", name="deep_duration_nonneg"),
        CheckConstraint("light_duration_seconds >= 0", name="light_duration_nonneg"),
        CheckConstraint("rem_duration_seconds >= 0", name="rem_duration_nonneg"),
        CheckConstraint("awake_duration_seconds >= 0", name="awake_duration_nonneg"),
        CheckConstraint("sleep_score BETWEEN 0 AND 100", name="sleep_score_range_check"),
    )
