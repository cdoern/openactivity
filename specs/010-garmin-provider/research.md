# Research: Garmin Connect Provider

**Date**: 2026-03-23
**Feature**: 010-garmin-provider
**Purpose**: Resolve technical unknowns before design phase

## 1. Garmin Connect API Library

### Decision: garminconnect Python Library

**Chosen**: `garminconnect` - Unofficial Garmin Connect API library for Python
**Version**: Latest stable (will pin during implementation)

**Rationale**:
- Widely adopted in Python fitness tracking community
- Supports authentication, activity retrieval, health/wellness data
- Active maintenance with recent commits
- Used by other open-source fitness projects (proven track record)
- Handles session management and API pagination
- Supports both username/password auth and MFA (though MFA requires manual token)

**Key Capabilities**:
```python
from garminconnect import Garmin

# Authentication
client = Garmin(username, password)
client.login()

# Activities
activities = client.get_activities(start=0, limit=20)  # Paginated
activity_detail = client.get_activity(activity_id)

# Health metrics
daily_stats = client.get_stats(date)  # Resting HR, stress, steps, etc.
sleep_data = client.get_sleep_data(date)
hrv_data = client.get_hrv_data(date)
body_battery = client.get_body_battery(start_date, end_date)

# User profile
user_profile = client.get_full_profile()
```

**Limitations**:
- No official API - reverse-engineered, subject to breakage if Garmin changes endpoints
- No OAuth support - username/password only (MFA requires manual token retrieval)
- Rate limiting not well-documented - need defensive programming
- Some endpoints may require specific Garmin device ownership (e.g., Body Battery requires compatible watch)

**Alternatives Considered**:
- `python-garminconnect`: Similar but less actively maintained
- Direct API calls: Too much overhead, reinventing the wheel
- Strava-only approach: Doesn't unlock health metrics (HRV, Body Battery, sleep)

---

## 2. Multi-Provider Architecture Pattern

### Decision: Provider-as-Plugin Pattern

**Pattern**: Each provider is a self-contained module implementing a minimal shared interface

**Structure**:
```python
# providers/interface.py
class ProviderInterface(ABC):
    @abstractmethod
    def authenticate(self) -> bool: ...

    @abstractmethod
    def sync_activities(self, since: datetime | None) -> int: ...

    @abstractmethod
    def get_activities(self, limit: int) -> list[Activity]: ...

# providers/garmin/client.py
class GarminProvider(ProviderInterface):
    def __init__(self, username: str, password: str):
        self.client = Garmin(username, password)

    def authenticate(self) -> bool:
        return self.client.login()

    # ... implement interface

    # Provider-specific methods
    def get_health_summary(self, date: datetime) -> dict: ...
```

**Rationale**:
- Aligns with constitution's provider isolation principle
- Strava provider already follows this pattern (reference implementation)
- Adding new providers requires no changes to existing code
- Provider-specific features (health data for Garmin, segments for Strava) don't pollute shared interface
- Easy to test providers independently with mocked API clients

**Implementation Notes**:
- Keep shared interface minimal (auth, sync, list) - already established by Strava
- Provider-specific data goes in provider-scoped tables (e.g., `garmin_daily_summary`)
- Provider-specific CLI commands live in provider module (e.g., `cli/garmin/daily.py`)
- Unified commands (e.g., `activities list`) query across providers using database joins

---

## 3. Database Schema Migration Strategy

### Decision: Alembic-style Migration with Backward Compatibility

**Approach**: Add `provider` and `provider_id` columns to Activity model, maintain compatibility

**Migration Steps**:
1. Add columns with defaults: `provider` (default='strava'), `provider_id` (nullable, copy from existing `id` column)
2. Create index on `(provider, provider_id)` for lookups
3. Add `ActivityLink` table for deduplication
4. Add Garmin-specific tables: `garmin_daily_summary`, `garmin_sleep_session`

**Schema Changes**:
```sql
-- Activity table modifications
ALTER TABLE activities ADD COLUMN provider VARCHAR DEFAULT 'strava';
ALTER TABLE activities ADD COLUMN provider_id INTEGER;
UPDATE activities SET provider_id = id WHERE provider = 'strava';
CREATE INDEX idx_activities_provider ON activities(provider, provider_id);

-- New: Activity deduplication link table
CREATE TABLE activity_links (
    id INTEGER PRIMARY KEY,
    strava_activity_id INTEGER REFERENCES activities(id),
    garmin_activity_id INTEGER REFERENCES activities(id),
    primary_provider VARCHAR NOT NULL,  -- Which provider is authoritative
    match_confidence FLOAT,  -- 0.0-1.0 confidence score
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- New: Garmin health data tables
CREATE TABLE garmin_daily_summary (
    id INTEGER PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    resting_hr INTEGER,
    hrv_avg INTEGER,
    body_battery_max INTEGER,
    body_battery_min INTEGER,
    stress_avg INTEGER,
    sleep_score INTEGER,
    steps INTEGER,
    respiration_avg FLOAT,
    spo2_avg FLOAT,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE garmin_sleep_session (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    total_duration_seconds INTEGER,
    deep_duration_seconds INTEGER,
    light_duration_seconds INTEGER,
    rem_duration_seconds INTEGER,
    awake_duration_seconds INTEGER,
    sleep_score INTEGER,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Rationale**:
- Backward compatible - existing Strava-only data continues to work
- `provider` enum allows future expansion (could add Wahoo, Polar, etc.)
- `provider_id` stores original ID from provider API (Strava uses integer IDs, Garmin may differ)
- Separate link table avoids denormalizing match data into Activity table
- Health data tables isolated from activity data (Garmin-specific, won't pollute Activity table)

**Rollback Strategy**:
- Migration is additive only - can be reversed by dropping new columns/tables
- Existing Strava functionality unaffected if migration fails

---

## 4. Activity Deduplication Algorithm

### Decision: Time-Distance-Type Matching with Confidence Scoring

**Algorithm**:
```python
def match_activities(strava_activity: Activity, garmin_activity: Activity) -> float | None:
    """
    Returns confidence score (0.0-1.0) if activities match, None otherwise.

    Matching criteria:
    - Start time within 60 seconds
    - Activity type compatible (e.g., "Run" matches "Running")
    - Duration within 5%
    - Optional: Distance within 5% (if both have distance)
    """
    # Time check
    time_diff = abs((strava_activity.start_date - garmin_activity.start_date).total_seconds())
    if time_diff > 60:
        return None

    # Type check (normalize types first)
    if not types_match(strava_activity.type, garmin_activity.type):
        return None

    # Duration check
    duration_ratio = garmin_activity.elapsed_time / strava_activity.elapsed_time
    if not (0.95 <= duration_ratio <= 1.05):
        return None

    # Calculate confidence (weighted average)
    time_score = 1.0 - (time_diff / 60.0)  # 1.0 = exact match, 0.0 = 60s diff
    duration_score = 1.0 - abs(1.0 - duration_ratio) / 0.05  # 1.0 = exact, 0.0 = 5% off

    confidence = (time_score * 0.6) + (duration_score * 0.4)

    return confidence if confidence >= 0.7 else None
```

**Rationale**:
- Time window of 60 seconds handles clock sync differences and manual start/stop delays
- Duration tolerance accounts for auto-pause differences between devices
- Confidence scoring allows manual review of borderline matches
- Type normalization handles slight naming differences ("Run" vs "Running", "Ride" vs "VirtualRide")
- Distance check is optional since some indoor activities (treadmill, trainer) may not have GPS

**Edge Cases Handled**:
- Multiple activities in same time window: Pick best confidence score
- One provider has more data: Mark that as primary, link both
- Manual activities: May not have distance - skip distance check
- Same activity uploaded to both providers later: Match by time even if different IDs

**Deduplication Workflow**:
1. After syncing from Garmin, query Strava activities in ±24h window
2. Run matching algorithm for each candidate pair
3. Create link entry if confidence >= 0.7
4. Mark primary provider based on which has more detailed data (streams, HR, etc.)
5. Display linked activities with "(Strava + Garmin)" badge in UI

---

## 5. Health Data Storage Pattern

### Decision: Daily Summary + Detail Tables

**Pattern**: Aggregate metrics in daily summary, detailed sessions in separate tables

**Rationale**:
- Daily summary optimized for trend queries ("Show me HRV over past 30 days")
- Sleep sessions may occur multiple times per day (naps) - separate table with 1:N relationship
- Aligns with Garmin API structure (daily stats endpoint + sleep endpoint)
- Easy to extend with more Garmin-specific metrics later

**Query Patterns**:
```python
# Get daily health trend
summaries = session.query(GarminDailySummary)\
    .filter(GarminDailySummary.date >= start_date)\
    .order_by(GarminDailySummary.date)\
    .all()

# Get sleep detail for a specific day
sleep_sessions = session.query(GarminSleepSession)\
    .filter(GarminSleepSession.date == target_date)\
    .all()

# Join activity with health data for readiness analysis
activity_with_health = session.query(Activity, GarminDailySummary)\
    .outerjoin(GarminDailySummary, Activity.start_date.date == GarminDailySummary.date)\
    .filter(Activity.start_date >= start_date)\
    .all()
```

**Data Freshness**:
- Health data typically updates once per day (overnight)
- Sync strategy: Fetch last 30 days on full sync, last 7 days on incremental
- No real-time requirement - daily sync is sufficient

---

## 6. Provider-Agnostic Command Implementation

### Decision: Database-Layer Provider Abstraction

**Pattern**: CLI queries database (provider-agnostic), database layer handles provider-specific details

**Implementation**:
```python
# cli/activities.py (unified command)
@app.command("list")
def list_activities(
    provider: str | None = typer.Option(None, "--provider"),
    limit: int = typer.Option(20, "--limit")
):
    activities = get_activities(provider=provider, limit=limit)

    for activity in activities:
        # Provider badge in output
        badge = get_provider_badge(activity)
        console.print(f"{badge} {activity.name} - {activity.distance}km")

# db/queries.py
def get_activities(provider: str | None = None, limit: int = 20) -> list[Activity]:
    query = session.query(Activity)

    if provider:
        query = query.filter(Activity.provider == provider)

    return query.order_by(Activity.start_date.desc()).limit(limit).all()

def get_provider_badge(activity: Activity) -> str:
    # Check if activity is linked
    link = session.query(ActivityLink)\
        .filter((ActivityLink.strava_activity_id == activity.id) |
                (ActivityLink.garmin_activity_id == activity.id))\
        .first()

    if link:
        return "[Strava+Garmin]"
    return f"[{activity.provider.capitalize()}]"
```

**Rationale**:
- Database is single source of truth - CLI doesn't need to know about provider APIs
- Provider badge logic centralized in database layer
- Easy to add filtering, sorting, searching without duplicating logic
- Follows separation of concerns: CLI = presentation, DB layer = data access

**Auto-Detection for `activity <ID>` Command**:
```python
@app.command("activity")
def show_activity(activity_id: int):
    # Try to find activity in database (provider-agnostic)
    activity = session.query(Activity)\
        .filter((Activity.id == activity_id) |
                (Activity.provider_id == activity_id))\
        .first()

    if not activity:
        console.print(f"Activity {activity_id} not found in local database")
        return

    display_activity_detail(activity)
```

---

## Summary of Decisions

| Area | Decision | Key Rationale |
|------|----------|---------------|
| **Garmin API** | garminconnect library | Active maintenance, proven track record, comprehensive API coverage |
| **Architecture** | Provider-as-plugin | Isolation, extensibility, follows existing Strava pattern |
| **Database** | Additive migration + provider fields | Backward compatible, minimal disruption |
| **Deduplication** | Time-distance-type + confidence score | Handles clock drift, allows manual review |
| **Health Data** | Daily summary + detail tables | Optimized for trend queries, extensible |
| **Unified Commands** | Database-layer abstraction | Single source of truth, clean separation |

**Risks Identified**:
1. **Garmin API instability**: Unofficial API may break - mitigate with defensive error handling and version pinning
2. **MFA complexity**: garminconnect doesn't fully support MFA - document limitation, provide manual token workflow
3. **Device-specific metrics**: Not all users have devices that track HRV/Body Battery - handle gracefully, show N/A for missing data
4. **Deduplication accuracy**: 95% target may not be achievable - provide manual link/unlink commands

**Next Steps**: Proceed to Phase 1 (data-model.md, contracts/, quickstart.md)
