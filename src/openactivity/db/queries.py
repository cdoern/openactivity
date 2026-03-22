"""Common database query helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import desc

from openactivity.db.models import (
    Activity,
    ActivityStream,
    ActivityZone,
    Athlete,
    AthleteStats,
    AthleteZone,
    CustomDistance,
    Gear,
    Lap,
    PersonalRecord,
    Segment,
    SegmentEffort,
    SyncState,
)

if TYPE_CHECKING:
    from datetime import datetime

    from sqlalchemy.orm import Session


def get_athlete(session: Session) -> Athlete | None:
    """Get the first (only) athlete record."""
    return session.query(Athlete).first()


def get_athlete_stats(session: Session, athlete_id: int) -> list[AthleteStats]:
    """Get all stats for an athlete."""
    return session.query(AthleteStats).filter_by(athlete_id=athlete_id).all()


def get_activities(
    session: Session,
    *,
    activity_type: str | None = None,
    after: datetime | None = None,
    before: datetime | None = None,
    search: str | None = None,
    sort: str = "date",
    limit: int = 20,
    offset: int = 0,
) -> list[Activity]:
    """Query activities with optional filters."""
    query = session.query(Activity)

    if activity_type:
        query = query.filter(Activity.type.ilike(activity_type))
    if after:
        query = query.filter(Activity.start_date >= after)
    if before:
        query = query.filter(Activity.start_date <= before)
    if search:
        query = query.filter(Activity.name.ilike(f"%{search}%"))

    if sort == "distance":
        query = query.order_by(desc(Activity.distance))
    elif sort == "duration":
        query = query.order_by(desc(Activity.moving_time))
    else:
        query = query.order_by(desc(Activity.start_date))

    return query.offset(offset).limit(limit).all()


def count_activities(
    session: Session,
    *,
    activity_type: str | None = None,
    after: datetime | None = None,
    before: datetime | None = None,
    search: str | None = None,
) -> int:
    """Count activities matching filters."""
    query = session.query(Activity)
    if activity_type:
        query = query.filter(Activity.type.ilike(activity_type))
    if after:
        query = query.filter(Activity.start_date >= after)
    if before:
        query = query.filter(Activity.start_date <= before)
    if search:
        query = query.filter(Activity.name.ilike(f"%{search}%"))
    return query.count()


def get_activity_by_id(session: Session, activity_id: int) -> Activity | None:
    """Get a single activity by Strava ID."""
    return session.query(Activity).filter_by(id=activity_id).first()


def get_laps(session: Session, activity_id: int) -> list[Lap]:
    """Get laps for an activity, ordered by index."""
    return session.query(Lap).filter_by(activity_id=activity_id).order_by(Lap.lap_index).all()


def get_activity_zones(session: Session, activity_id: int) -> list[ActivityZone]:
    """Get zone distributions for an activity."""
    return (
        session.query(ActivityZone)
        .filter_by(activity_id=activity_id)
        .order_by(ActivityZone.zone_type, ActivityZone.zone_index)
        .all()
    )


def get_athlete_zones(session: Session, athlete_id: int) -> list[AthleteZone]:
    """Get configured training zones for an athlete."""
    return (
        session.query(AthleteZone)
        .filter_by(athlete_id=athlete_id)
        .order_by(AthleteZone.zone_type, AthleteZone.zone_index)
        .all()
    )


def get_activity_streams(
    session: Session, activity_id: int, stream_types: list[str] | None = None
) -> list[ActivityStream]:
    """Get stream data for an activity."""
    query = session.query(ActivityStream).filter_by(activity_id=activity_id)
    if stream_types:
        query = query.filter(ActivityStream.stream_type.in_(stream_types))
    return query.all()


def get_gear(session: Session, gear_id: str) -> Gear | None:
    """Get gear by ID."""
    return session.query(Gear).filter_by(id=gear_id).first()


def get_starred_segments(
    session: Session,
    *,
    activity_type: str | None = None,
    limit: int = 20,
) -> list[Segment]:
    """Get starred segments."""
    query = session.query(Segment).filter_by(starred=True)
    if activity_type:
        query = query.filter(Segment.activity_type.ilike(activity_type))
    return query.limit(limit).all()


def get_segment_efforts(
    session: Session, segment_id: int, *, limit: int = 20
) -> list[SegmentEffort]:
    """Get efforts on a segment, ordered by date descending."""
    return (
        session.query(SegmentEffort)
        .filter_by(segment_id=segment_id)
        .order_by(desc(SegmentEffort.start_date))
        .limit(limit)
        .all()
    )


def get_personal_records(
    session: Session, *, record_type: str | None = None, current_only: bool = True
) -> list[PersonalRecord]:
    """Get personal records, optionally filtered by type."""
    query = session.query(PersonalRecord)
    if current_only:
        query = query.filter(PersonalRecord.is_current.is_(True))
    if record_type:
        query = query.filter(PersonalRecord.record_type == record_type)
    return query.order_by(PersonalRecord.distance_type).all()


def get_records_by_distance(
    session: Session, distance_type: str
) -> list[PersonalRecord]:
    """Get all records for a distance type, ordered by date."""
    return (
        session.query(PersonalRecord)
        .filter(PersonalRecord.distance_type == distance_type)
        .order_by(PersonalRecord.achieved_date)
        .all()
    )


def get_custom_distances(session: Session) -> list[CustomDistance]:
    """Get all custom distances."""
    return session.query(CustomDistance).order_by(CustomDistance.label).all()


def get_sync_state(session: Session, entity_type: str) -> SyncState | None:
    """Get sync state for an entity type."""
    return session.query(SyncState).filter_by(entity_type=entity_type).first()


def upsert_sync_state(
    session: Session,
    entity_type: str,
    *,
    last_sync_at: datetime | None = None,
    last_activity_at: datetime | None = None,
    status: str = "complete",
) -> SyncState:
    """Create or update sync state for an entity type."""
    state = get_sync_state(session, entity_type)
    if state is None:
        state = SyncState(entity_type=entity_type)
        session.add(state)
    if last_sync_at is not None:
        state.last_sync_at = last_sync_at
    if last_activity_at is not None:
        state.last_activity_at = last_activity_at
    state.status = status
    session.flush()
    return state
