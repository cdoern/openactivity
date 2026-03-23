"""Sync logic for fetching Strava data into local storage."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from openactivity.db.models import (
    Activity,
    ActivityStream,
    ActivityZone,
    Athlete,
    AthleteStats,
    AthleteZone,
    Gear,
    Lap,
    Segment,
    SegmentEffort,
)
from openactivity.db.queries import get_sync_state, upsert_sync_state
from openactivity.providers.strava.client import get_strava_client, rate_limit
from openactivity.providers.strava.transform import (
    transform_activity,
    transform_activity_zones,
    transform_athlete,
    transform_athlete_stats,
    transform_gear,
    transform_laps,
    transform_segment,
    transform_segment_effort,
    transform_streams,
)

console = Console(stderr=True)

STREAM_TYPES = [
    "time",
    "distance",
    "latlng",
    "altitude",
    "velocity_smooth",
    "heartrate",
    "cadence",
    "watts",
    "temp",
    "moving",
    "grade_smooth",
]


def _check_rate_limit() -> None:
    """Pause if rate limited, showing a message."""
    if rate_limit.is_rate_limited:
        wait = rate_limit.seconds_until_reset()
        minutes = wait // 60
        console.print(
            f"  [yellow]⏳ Rate limit reached: pausing {minutes}m (resets in {wait}s)[/yellow]"
        )
        time.sleep(wait + 1)


def sync_athlete(session: Session) -> int:
    """Sync athlete profile and stats. Returns athlete ID."""
    client = get_strava_client()

    strava_athlete = client.get_athlete()
    local_athlete = transform_athlete(strava_athlete)

    existing = session.query(Athlete).filter_by(id=local_athlete.id).first()
    if existing:
        for attr in [
            "firstname",
            "lastname",
            "city",
            "state",
            "country",
            "measurement_pref",
            "weight",
            "ftp",
            "username",
        ]:
            setattr(existing, attr, getattr(local_athlete, attr))
    else:
        session.add(local_athlete)
    session.flush()

    # Sync stats
    strava_stats = client.get_athlete_stats(strava_athlete.id)
    stat_rows = transform_athlete_stats(strava_athlete.id, strava_stats)

    # Delete old stats and replace
    session.query(AthleteStats).filter_by(athlete_id=strava_athlete.id).delete()
    for row in stat_rows:
        session.add(row)
    session.flush()

    # Sync athlete zones
    try:
        strava_zones = client.get_athlete_zones()
        zone_list = getattr(strava_zones, "zones", [])
        if zone_list:
            session.query(AthleteZone).filter_by(athlete_id=strava_athlete.id).delete()
            from openactivity.providers.strava.transform import (
                transform_athlete_zones,
            )

            local_zones = transform_athlete_zones(zone_list, strava_athlete.id)
            for z in local_zones:
                session.add(z)
            session.flush()
    except Exception:
        # Zones may require premium — skip silently
        pass

    upsert_sync_state(
        session,
        "athlete",
        last_sync_at=datetime.now(tz=UTC),
    )
    session.commit()

    return strava_athlete.id


def sync_activities(
    session: Session,
    athlete_id: int,
    *,
    full: bool = False,
    detail: bool = True,
) -> dict:
    """Sync activities from Strava.

    Returns:
        Summary dict with counts.
    """
    client = get_strava_client()

    # Determine start point for incremental sync
    after = None
    if not full:
        state = get_sync_state(session, "activities")
        if state and state.last_activity_at:
            after = state.last_activity_at

    upsert_sync_state(session, "activities", status="in_progress")
    session.commit()

    new_count = 0
    updated_count = 0
    error_count = 0
    latest_date = after

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TextColumn("{task.completed} activities"),
        console=console,
    ) as progress:
        task = progress.add_task("Syncing activities...", total=None)

        activities = client.get_activities(after=after)
        for strava_activity in activities:
            _check_rate_limit()

            try:
                local = transform_activity(strava_activity, athlete_id)
                existing = session.query(Activity).filter_by(id=local.id).first()

                if existing:
                    # Update existing activity
                    for attr in [
                        "name",
                        "type",
                        "sport_type",
                        "distance",
                        "moving_time",
                        "elapsed_time",
                        "total_elevation_gain",
                        "average_speed",
                        "max_speed",
                        "average_heartrate",
                        "max_heartrate",
                        "average_cadence",
                        "average_watts",
                        "max_watts",
                        "calories",
                        "suffer_score",
                        "gear_id",
                    ]:
                        setattr(existing, attr, getattr(local, attr))
                    updated_count += 1
                else:
                    session.add(local)
                    new_count += 1

                # Track latest activity date
                if local.start_date and (latest_date is None or local.start_date > latest_date):
                    latest_date = local.start_date

                # Fetch detail data if requested
                if detail:
                    _sync_activity_detail(session, client, strava_activity.id, athlete_id)

                progress.update(task, advance=1)

                # Commit in batches
                if (new_count + updated_count) % 10 == 0:
                    session.commit()

            except Exception as e:
                console.print(f"  [red]Error syncing activity {strava_activity.id}: {e}[/red]")
                error_count += 1

    # Sync gear referenced by activities
    _sync_gear(session, client)

    # Sync starred segments and efforts
    _sync_segments(session, client)

    upsert_sync_state(
        session,
        "activities",
        last_sync_at=datetime.now(tz=UTC),
        last_activity_at=latest_date,
        status="complete",
    )
    session.commit()

    return {
        "synced": new_count + updated_count,
        "new": new_count,
        "updated": updated_count,
        "errors": error_count,
        "last_sync": datetime.now(tz=UTC).isoformat(),
    }


def _sync_activity_detail(
    session: Session,
    client,
    activity_id: int,
    athlete_id: int,
) -> None:
    """Fetch and store detailed data for a single activity."""
    existing = session.query(Activity).filter_by(id=activity_id).first()
    if existing and existing.synced_detail:
        return

    _check_rate_limit()

    try:
        detailed = client.get_activity(activity_id)
    except Exception:
        return

    # Sync laps
    if hasattr(detailed, "laps") and detailed.laps:
        session.query(Lap).filter_by(activity_id=activity_id).delete()
        laps = transform_laps(list(detailed.laps), activity_id)
        for lap in laps:
            session.add(lap)

    # Sync zones
    _check_rate_limit()
    try:
        strava_zones = client.get_activity_zones(activity_id)
        if strava_zones:
            session.query(ActivityZone).filter_by(activity_id=activity_id).delete()
            zones = transform_activity_zones(strava_zones, activity_id)
            for z in zones:
                session.add(z)
    except Exception:
        pass  # Zones may require premium

    # Sync streams
    _check_rate_limit()
    try:
        strava_streams = client.get_activity_streams(activity_id, types=STREAM_TYPES)
        if strava_streams:
            session.query(ActivityStream).filter_by(activity_id=activity_id).delete()
            streams = transform_streams(strava_streams, activity_id)
            for s in streams:
                session.add(s)
    except Exception:
        pass  # Streams may not be available

    # Mark as detail-synced
    if existing:
        existing.synced_detail = True

    session.flush()


def _sync_gear(session: Session, client) -> None:
    """Sync gear referenced by activities."""
    gear_ids = session.query(Activity.gear_id).filter(Activity.gear_id.isnot(None)).distinct().all()

    for (gear_id,) in gear_ids:
        existing = session.query(Gear).filter_by(id=gear_id).first()
        if existing:
            continue

        _check_rate_limit()
        try:
            strava_gear = client.get_gear(gear_id)
            local_gear = transform_gear(strava_gear)
            session.add(local_gear)
        except Exception:
            pass

    session.flush()


def sync_segments(session: Session) -> dict:
    """Public entry point: sync starred segments and their efforts."""
    client = get_strava_client()
    _sync_segments(session, client)
    session.commit()

    segment_count = session.query(Segment).filter_by(starred=True).count()
    effort_count = session.query(SegmentEffort).count()

    return {
        "segments": segment_count,
        "efforts": effort_count,
    }


def _sync_segments(session: Session, client) -> None:
    """Sync starred segments and their efforts."""
    _check_rate_limit()
    try:
        starred = client.get_starred_segments()
    except Exception:
        return

    for strava_segment in starred:
        _check_rate_limit()
        try:
            local_segment = transform_segment(strava_segment)
            # Force starred=True since these came from get_starred_segments()
            local_segment.starred = True

            existing = session.query(Segment).filter_by(id=local_segment.id).first()
            if existing:
                for attr in [
                    "name",
                    "distance",
                    "average_grade",
                    "maximum_grade",
                    "elevation_high",
                    "elevation_low",
                    "starred",
                    "pr_time",
                    "effort_count",
                ]:
                    setattr(existing, attr, getattr(local_segment, attr))
            else:
                session.add(local_segment)

            # Sync efforts for this segment
            try:
                efforts = client.get_segment_efforts(strava_segment.id)
                for effort in efforts:
                    local_effort = transform_segment_effort(effort)
                    existing_effort = (
                        session.query(SegmentEffort).filter_by(id=local_effort.id).first()
                    )
                    if not existing_effort:
                        session.add(local_effort)
            except Exception:
                pass
        except Exception:
            pass

    session.flush()
