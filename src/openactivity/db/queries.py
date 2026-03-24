"""Common database query helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import asc, desc

from openactivity.db.models import (
    Activity,
    ActivityLink,
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
    provider: str | None = None,
    sort: str = "date",
    limit: int = 20,
    offset: int = 0,
) -> list[Activity]:
    """Query activities with optional filters."""
    query = session.query(Activity)

    if activity_type:
        query = query.filter(Activity.type.ilike(f"%{activity_type}%"))
    if after:
        query = query.filter(Activity.start_date >= after)
    if before:
        query = query.filter(Activity.start_date <= before)
    if search:
        query = query.filter(Activity.name.ilike(f"%{search}%"))
    if provider:
        query = query.filter(Activity.provider == provider)

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
    provider: str | None = None,
) -> int:
    """Count activities matching filters."""
    query = session.query(Activity)
    if activity_type:
        query = query.filter(Activity.type.ilike(f"%{activity_type}%"))
    if after:
        query = query.filter(Activity.start_date >= after)
    if before:
        query = query.filter(Activity.start_date <= before)
    if search:
        query = query.filter(Activity.name.ilike(f"%{search}%"))
    if provider:
        query = query.filter(Activity.provider == provider)
    return query.count()


def get_provider_badge(session: Session, activity: Activity) -> str:
    """Get a display badge for the activity's provider(s).

    Returns badges like [Strava], [Garmin], or [Strava+Garmin] if linked.
    """
    # Check if this activity is linked to one from another provider
    link = (
        session.query(ActivityLink)
        .filter(
            (ActivityLink.strava_activity_id == activity.id)
            | (ActivityLink.garmin_activity_id == activity.id)
        )
        .first()
    )

    if link:
        return "[Strava+Garmin]"

    if activity.provider == "garmin":
        return "[Garmin]"
    return "[Strava]"


def get_activity_by_id(session: Session, activity_id: int) -> Activity | None:
    """Get a single activity by ID."""
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


def get_segment_efforts_chronological(
    session: Session, segment_id: int, *, limit: int = 10000
) -> list[SegmentEffort]:
    """Get efforts on a segment, ordered by date ascending (oldest first)."""
    return (
        session.query(SegmentEffort)
        .filter_by(segment_id=segment_id)
        .order_by(asc(SegmentEffort.start_date))
        .limit(limit)
        .all()
    )


def get_segment_by_id(session: Session, segment_id: int) -> Segment | None:
    """Get a single segment by ID."""
    return session.query(Segment).filter_by(id=segment_id).first()


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


def detect_duplicate_activities(session: Session, activity: Activity) -> list[tuple[Activity, float]]:
    """Detect potential duplicate activities from other providers.

    Uses time window (±60 seconds), activity type matching, and duration tolerance (±5%)
    to find activities that are likely the same activity recorded on different platforms.

    Args:
        session: Database session
        activity: The activity to find duplicates for

    Returns:
        List of (matching_activity, confidence_score) tuples, sorted by confidence desc
    """
    if not activity.start_date or not activity.elapsed_time:
        return []

    # Get opposite provider
    other_provider = "garmin" if activity.provider == "strava" else "strava"

    # Time window: ±60 seconds
    time_window_seconds = 60
    from datetime import timedelta

    start_min = activity.start_date - timedelta(seconds=time_window_seconds)
    start_max = activity.start_date + timedelta(seconds=time_window_seconds)

    # Query candidates from other provider
    candidates = (
        session.query(Activity)
        .filter(
            Activity.provider == other_provider,
            Activity.start_date >= start_min,
            Activity.start_date <= start_max,
        )
        .all()
    )

    matches = []

    for candidate in candidates:
        # Check if already linked
        existing_link = (
            session.query(ActivityLink)
            .filter(
                (ActivityLink.strava_activity_id == activity.id)
                | (ActivityLink.garmin_activity_id == activity.id)
                | (ActivityLink.strava_activity_id == candidate.id)
                | (ActivityLink.garmin_activity_id == candidate.id)
            )
            .first()
        )

        if existing_link:
            continue  # Skip already linked activities

        # Type check (normalize types for comparison)
        if not _types_match(activity.type, candidate.type):
            continue

        # Duration check (within 5%)
        if not candidate.elapsed_time or candidate.elapsed_time == 0:
            continue

        duration_ratio = candidate.elapsed_time / activity.elapsed_time
        if not (0.95 <= duration_ratio <= 1.05):
            continue

        # Calculate confidence score
        time_diff = abs((activity.start_date - candidate.start_date).total_seconds())
        time_score = 1.0 - (time_diff / time_window_seconds)
        duration_score = 1.0 - abs(1.0 - duration_ratio) / 0.05

        confidence = (time_score * 0.6) + (duration_score * 0.4)

        if confidence >= 0.7:
            matches.append((candidate, confidence))

    # Sort by confidence descending
    matches.sort(key=lambda x: x[1], reverse=True)

    return matches


def _types_match(type1: str | None, type2: str | None) -> bool:
    """Check if two activity types match (case-insensitive)."""
    if not type1 or not type2:
        return False

    # Normalize types
    t1 = type1.lower()
    t2 = type2.lower()

    # Direct match
    if t1 == t2:
        return True

    # Handle common variations
    run_types = {"run", "running", "trail_running", "treadmill_running"}
    if t1 in run_types and t2 in run_types:
        return True

    ride_types = {"ride", "cycling", "road_biking", "mountain_biking"}
    if t1 in ride_types and t2 in ride_types:
        return True

    virtual_ride_types = {"virtualride", "virtual_ride", "indoor_cycling"}
    if t1 in virtual_ride_types and t2 in virtual_ride_types:
        return True

    swim_types = {"swim", "swimming", "open_water_swimming"}
    if t1 in swim_types and t2 in swim_types:
        return True

    return False


def link_activities(
    session: Session,
    strava_activity_id: int | None,
    garmin_activity_id: int | None,
    primary_provider: str,
    match_confidence: float,
) -> ActivityLink:
    """Create a link between duplicate activities from different providers.

    Args:
        session: Database session
        strava_activity_id: Strava activity database ID (not provider_id)
        garmin_activity_id: Garmin activity database ID (not provider_id)
        primary_provider: Which provider is authoritative ("strava" or "garmin")
        match_confidence: Confidence score (0.0-1.0)

    Returns:
        The created ActivityLink record
    """
    if not strava_activity_id and not garmin_activity_id:
        raise ValueError("At least one activity ID must be provided")

    if match_confidence < 0.0 or match_confidence > 1.0:
        raise ValueError("Match confidence must be between 0.0 and 1.0")

    # Check if link already exists
    existing = (
        session.query(ActivityLink)
        .filter(
            (
                (ActivityLink.strava_activity_id == strava_activity_id)
                if strava_activity_id
                else False
            )
            | (
                (ActivityLink.garmin_activity_id == garmin_activity_id)
                if garmin_activity_id
                else False
            )
        )
        .first()
    )

    if existing:
        return existing

    # Create new link
    link = ActivityLink(
        strava_activity_id=strava_activity_id,
        garmin_activity_id=garmin_activity_id,
        primary_provider=primary_provider,
        match_confidence=match_confidence,
    )

    session.add(link)
    session.flush()

    return link
