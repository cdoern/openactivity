"""Garmin Connect activity sync module."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from openactivity.db import queries
from openactivity.db.models import Activity, GarminDailySummary, GarminSleepSession
from openactivity.providers.garmin import transform
from openactivity.providers.garmin.client import GarminClient

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class SyncResult:
    """Result of a sync operation."""

    def __init__(self):
        self.activities_new = 0
        self.activities_updated = 0
        self.activities_errors = 0
        self.duplicates_detected = 0
        self.health_daily_summaries = 0
        self.health_sleep_sessions = 0
        self.duration_seconds = 0.0


def sync_activities(
    session: Session,
    client: GarminClient,
    *,
    full: bool = False,
    limit: int | None = None,
) -> SyncResult:
    """Sync activities from Garmin Connect to local database.

    Args:
        session: Database session
        client: Authenticated Garmin client
        full: If True, perform full sync ignoring last sync time
        limit: Maximum number of activities to sync (None for all)

    Returns:
        SyncResult with statistics about the sync operation
    """
    start_time = datetime.now()
    result = SyncResult()

    # Get sync state for incremental sync
    sync_state = queries.get_sync_state(session, "garmin_activities")
    last_sync_at = None if full else (sync_state.last_sync_at if sync_state else None)

    # Fetch activities from Garmin
    activities_processed = 0
    page_start = 0
    page_size = 20

    while True:
        try:
            garmin_activities = client.get_activities(start=page_start, limit=page_size)
        except Exception as e:
            print(f"Error fetching activities: {e}")
            break

        if not garmin_activities:
            break

        for garmin_activity in garmin_activities:
            # Check if we've reached the sync limit
            if limit and activities_processed >= limit:
                break

            # Skip if activity is older than last sync (incremental)
            if last_sync_at:
                activity_date_str = garmin_activity.get("startTimeGMT")
                if activity_date_str:
                    try:
                        activity_date = datetime.fromisoformat(
                            activity_date_str.replace("Z", "+00:00")
                        )
                        if activity_date < last_sync_at:
                            # Reached activities older than last sync, stop
                            break
                    except (ValueError, AttributeError):
                        pass

            # Transform and store activity
            try:
                activity_data = transform.transform_activity(garmin_activity)
                provider_id = activity_data["provider_id"]

                # Check if activity already exists
                existing = (
                    session.query(Activity)
                    .filter_by(provider="garmin", provider_id=provider_id)
                    .first()
                )

                if existing:
                    # Update existing activity
                    for key, value in activity_data.items():
                        if key != "id" and value is not None:
                            setattr(existing, key, value)
                    result.activities_updated += 1
                else:
                    # Create new activity
                    new_activity = Activity(**activity_data)
                    session.add(new_activity)
                    session.flush()  # Get ID assigned
                    result.activities_new += 1

                    # Detect and link duplicates
                    matches = queries.detect_duplicate_activities(session, new_activity)
                    if matches:
                        best_match, confidence = matches[0]

                        # Determine primary provider (prefer one with more data)
                        primary = "garmin" if new_activity.has_heartrate else best_match.provider

                        # Link activities
                        strava_id = best_match.id if best_match.provider == "strava" else new_activity.id
                        garmin_id = new_activity.id if new_activity.provider == "garmin" else best_match.id

                        queries.link_activities(
                            session,
                            strava_activity_id=strava_id if best_match.provider == "strava" else None,
                            garmin_activity_id=garmin_id,
                            primary_provider=primary,
                            match_confidence=confidence,
                        )
                        result.duplicates_detected += 1

                activities_processed += 1

            except Exception as e:
                print(f"Error processing activity: {e}")
                result.activities_errors += 1

        # Check if we should continue to next page
        if limit and activities_processed >= limit:
            break

        if len(garmin_activities) < page_size:
            # Last page
            break

        page_start += page_size

    # Update sync state
    queries.upsert_sync_state(
        session,
        "garmin_activities",
        last_sync_at=datetime.now(),
        last_activity_at=datetime.now(),
        status="complete",
    )

    session.commit()

    result.duration_seconds = (datetime.now() - start_time).total_seconds()
    return result


def sync_health_data(
    session: Session,
    client: GarminClient,
    *,
    days: int = 7,
) -> SyncResult:
    """Sync health data (daily summaries and sleep) from Garmin Connect.

    Args:
        session: Database session
        client: Authenticated Garmin client
        days: Number of days to sync (default: 7)

    Returns:
        SyncResult with statistics about the sync operation
    """
    start_time = datetime.now()
    result = SyncResult()

    # Sync last N days
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")

        try:
            # Fetch daily stats
            stats = client.get_stats(date)

            # Fetch HRV data
            hrv_data = None
            try:
                hrv_data = client.get_hrv_data(date)
            except Exception:
                pass  # HRV may not be available

            # Fetch Body Battery data
            body_battery = None
            try:
                body_battery = client.get_body_battery(date, date)
            except Exception:
                pass  # Body Battery may not be available

            # Transform and store daily summary
            summary_data = transform.transform_daily_summary(date, stats, hrv_data, body_battery)

            # Check if summary already exists
            existing_summary = (
                session.query(GarminDailySummary)
                .filter_by(date=summary_data["date"])
                .first()
            )

            if existing_summary:
                # Update existing
                for key, value in summary_data.items():
                    if key != "id" and value is not None:
                        setattr(existing_summary, key, value)
            else:
                # Create new
                new_summary = GarminDailySummary(**summary_data)
                session.add(new_summary)
                result.health_daily_summaries += 1

            # Fetch and store sleep data
            try:
                sleep_data = client.get_sleep_data(date)
                if sleep_data:
                    sleep_session_data = transform.transform_sleep_session(date, sleep_data)

                    if sleep_session_data:
                        # Check if session already exists
                        existing_sleep = (
                            session.query(GarminSleepSession)
                            .filter_by(
                                date=sleep_session_data["date"],
                                start_time=sleep_session_data["start_time"],
                            )
                            .first()
                        )

                        if existing_sleep:
                            # Update existing
                            for key, value in sleep_session_data.items():
                                if key != "id" and value is not None:
                                    setattr(existing_sleep, key, value)
                        else:
                            # Create new
                            new_sleep = GarminSleepSession(**sleep_session_data)
                            session.add(new_sleep)
                            result.health_sleep_sessions += 1

                        # Update daily summary with sleep score
                        if existing_summary and sleep_session_data.get("sleep_score"):
                            existing_summary.sleep_score = sleep_session_data["sleep_score"]

            except Exception as e:
                print(f"Error fetching sleep data for {date}: {e}")

        except Exception as e:
            print(f"Error syncing health data for {date}: {e}")

    # Update sync state
    queries.upsert_sync_state(
        session,
        "garmin_health",
        last_sync_at=datetime.now(),
        status="complete",
    )

    session.commit()

    result.duration_seconds = (datetime.now() - start_time).total_seconds()
    return result


def sync_all(
    session: Session,
    client: GarminClient,
    *,
    full: bool = False,
    activities_only: bool = False,
    health_only: bool = False,
    limit: int | None = None,
) -> SyncResult:
    """Sync both activities and health data from Garmin Connect.

    Args:
        session: Database session
        client: Authenticated Garmin client
        full: If True, perform full sync ignoring last sync time
        activities_only: If True, sync only activities
        health_only: If True, sync only health data
        limit: Maximum number of activities to sync (None for all)

    Returns:
        Combined SyncResult with statistics
    """
    combined_result = SyncResult()
    start_time = datetime.now()

    if not health_only:
        # Sync activities
        activity_result = sync_activities(session, client, full=full, limit=limit)
        combined_result.activities_new = activity_result.activities_new
        combined_result.activities_updated = activity_result.activities_updated
        combined_result.activities_errors = activity_result.activities_errors
        combined_result.duplicates_detected = activity_result.duplicates_detected

    if not activities_only:
        # Sync health data
        health_result = sync_health_data(session, client, days=7 if not full else 30)
        combined_result.health_daily_summaries = health_result.health_daily_summaries
        combined_result.health_sleep_sessions = health_result.health_sleep_sessions

    combined_result.duration_seconds = (datetime.now() - start_time).total_seconds()
    return combined_result
