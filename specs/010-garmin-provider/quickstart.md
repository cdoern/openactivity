# Quickstart: Garmin Connect Provider

**Feature**: 010-garmin-provider
**Audience**: Developers implementing this feature
**Purpose**: Fast onboarding to Garmin provider architecture and implementation flow

## 5-Minute Overview

**What**: Add Garmin Connect as second data provider alongside Strava
**Why**: Unlock health metrics (HRV, Body Battery, sleep) that Strava doesn't have
**How**: Follow existing Strava provider pattern, extend Activity model, add unified commands

**Key Changes**:
1. New provider module: `src/openactivity/providers/garmin/`
2. New CLI commands: `openactivity garmin auth|sync|athlete|daily`
3. Database migration: Add `provider` + `provider_id` fields to Activity
4. New tables: `activity_links`, `garmin_daily_summary`, `garmin_sleep_session`
5. Enhanced unified commands: `activity <ID>` and `activities list` work across providers

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│                   CLI Layer (typer)                         │
│  ┌────────────────────┐  ┌──────────────────────────────┐  │
│  │ Strava Commands    │  │ Garmin Commands (NEW)        │  │
│  │ strava auth/sync   │  │ garmin auth/sync/daily       │  │
│  └────────────────────┘  └──────────────────────────────┘  │
│         │                          │                        │
│  ┌──────▼──────────────────────────▼────────────────────┐  │
│  │        Unified Commands (ENHANCED)                   │  │
│  │        activity <ID>                                 │  │
│  │        activities list --provider strava|garmin      │  │
│  └──────────────────────┬───────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────┘
                          │
┌─────────────────────────▼──────────────────────────────────┐
│                  Database Layer (SQLAlchemy)               │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │  Activities  │  │ Activity     │  │ Garmin Health   │  │
│  │  (extended)  │  │ Links (NEW)  │  │ Data (NEW)      │  │
│  │ +provider    │  │ Deduplication│  │ Daily/Sleep     │  │
│  │ +provider_id │  │              │  │                 │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼──────────────────────────────────┐
│               Provider Layer (API Clients)                 │
│  ┌────────────────────┐  ┌──────────────────────────────┐  │
│  │ Strava Provider    │  │ Garmin Provider (NEW)        │  │
│  │ stravalib wrapper  │  │ garminconnect wrapper        │  │
│  └────────────────────┘  └──────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

**Data Flow**:
1. User runs `garmin sync`
2. CLI calls `providers/garmin/sync.py`
3. Garmin client fetches activities + health data from API
4. Transform layer converts Garmin models → local models
5. Database layer stores data with `provider='garmin'`
6. Deduplication logic links matching Strava/Garmin activities
7. Unified commands query database (provider-agnostic)

---

## Implementation Checklist

### Phase 1: Database Migration ✓

- [ ] Add `provider` column to Activity (default='strava')
- [ ] Add `provider_id` column to Activity (nullable initially)
- [ ] Backfill `provider_id` for existing Strava activities
- [ ] Create `activity_links` table
- [ ] Create `garmin_daily_summary` table
- [ ] Create `garmin_sleep_session` table
- [ ] Create indexes: `(provider, provider_id)`, `date` on health tables
- [ ] Write migration script (Alembic-style)
- [ ] Test migration on copy of production database

**Files**:
- `src/openactivity/db/models.py` (modify Activity, add new models)
- `src/openactivity/db/migrations/001_add_garmin_support.py` (new)

---

### Phase 2: Garmin Provider Module ✓

- [ ] Create directory structure: `src/openactivity/providers/garmin/`
- [ ] Implement `client.py` (garminconnect wrapper)
- [ ] Implement `auth.py` (username/password auth)
- [ ] Implement `transform.py` (Garmin API → local models)
- [ ] Implement `sync.py` (activity + health data sync logic)
- [ ] Add to `providers/__init__.py` (register provider)

**Files**:
- `src/openactivity/providers/garmin/__init__.py`
- `src/openactivity/providers/garmin/client.py`
- `src/openactivity/providers/garmin/auth.py`
- `src/openactivity/providers/garmin/transform.py`
- `src/openactivity/providers/garmin/sync.py`

**Key Implementation Notes**:
- Follow Strava provider pattern (reference: `providers/strava/`)
- Use `garminconnect` library for API access
- Store credentials in keyring (same as Strava)
- Implement incremental sync (track last sync time)
- Handle rate limiting with exponential backoff
- Transform Garmin activity types to normalized types

---

### Phase 3: Garmin CLI Commands ✓

- [ ] Create `cli/garmin/` directory
- [ ] Implement `app.py` (command group root)
- [ ] Implement `auth.py` (`garmin auth` command)
- [ ] Implement `sync.py` (`garmin sync` command)
- [ ] Implement `athlete.py` (`garmin athlete` command)
- [ ] Implement `activities.py` (`garmin activities list` command)
- [ ] Implement `daily.py` (`garmin daily` command - health metrics)
- [ ] Register command group in `cli/root.py`

**Files**:
- `src/openactivity/cli/garmin/__init__.py`
- `src/openactivity/cli/garmin/app.py`
- `src/openactivity/cli/garmin/auth.py`
- `src/openactivity/cli/garmin/sync.py`
- `src/openactivity/cli/garmin/athlete.py`
- `src/openactivity/cli/garmin/activities.py`
- `src/openactivity/cli/garmin/daily.py`
- `src/openactivity/cli/root.py` (modify to register garmin group)

---

### Phase 4: Activity Deduplication ✓

- [ ] Implement matching algorithm in `db/queries.py`
- [ ] Add `detect_duplicates()` function (time + duration + type matching)
- [ ] Add `link_activities()` function (create ActivityLink record)
- [ ] Integrate deduplication into sync workflow
- [ ] Add confidence scoring (0.0-1.0)
- [ ] Handle edge cases (multiple candidates, already linked)

**Files**:
- `src/openactivity/db/queries.py` (add deduplication functions)
- `src/openactivity/providers/garmin/sync.py` (call dedup after sync)

**Algorithm**:
```python
def detect_duplicates(strava_id: int, garmin_id: int) -> float | None:
    # Returns confidence score or None
    time_diff = abs(strava.start_date - garmin.start_date).total_seconds()
    if time_diff > 60:
        return None

    duration_ratio = garmin.elapsed_time / strava.elapsed_time
    if not (0.95 <= duration_ratio <= 1.05):
        return None

    # Confidence = weighted time + duration match
    return calculate_confidence(time_diff, duration_ratio)
```

---

### Phase 5: Unified Commands Enhancement ✓

- [ ] Modify `cli/activities.py` to query all providers
- [ ] Add `--provider` filter option
- [ ] Add provider badge logic (show "Strava", "Garmin", or "Strava+Garmin")
- [ ] Update `activity <ID>` to search across providers
- [ ] Modify database queries to support provider filtering

**Files**:
- `src/openactivity/cli/activities.py` (modify list command)
- `src/openactivity/cli/strava/activities.py` (modify show_activity for unified ID lookup)
- `src/openactivity/db/queries.py` (add provider-aware query functions)

---

### Phase 6: Testing ✓

- [ ] Unit tests for Garmin auth flow
- [ ] Unit tests for Garmin sync (with VCR fixtures)
- [ ] Unit tests for transformation layer
- [ ] Unit tests for deduplication algorithm
- [ ] Integration test: Full Garmin sync workflow
- [ ] Integration test: Provider-agnostic queries
- [ ] Contract tests: Garmin provider conforms to interface

**Files**:
- `tests/unit/test_garmin_auth.py`
- `tests/unit/test_garmin_sync.py`
- `tests/unit/test_garmin_transform.py`
- `tests/unit/test_deduplication.py`
- `tests/integration/test_garmin_provider.py`
- `tests/contract/test_provider_interface.py` (update for Garmin)

**VCR Fixtures**:
- Record real Garmin API responses during development
- Sanitize credentials before committing
- Use for deterministic integration tests

---

## Development Workflow

### 1. Set Up Development Environment

```bash
# Clone and switch to feature branch
git checkout 010-garmin-provider

# Install dependencies (including garminconnect)
uv sync --extra dev

# Run existing tests to ensure baseline
uv run pytest
```

### 2. Database Migration (Do This First!)

```bash
# Create migration script
touch src/openactivity/db/migrations/001_add_garmin_support.py

# Implement migration (see data-model.md for SQL)
# Test on local database copy

# Apply migration
python -m openactivity.db.migrations.001_add_garmin_support
```

### 3. Implement Garmin Provider

```bash
# Create module structure
mkdir -p src/openactivity/providers/garmin
touch src/openactivity/providers/garmin/{__init__,client,auth,transform,sync}.py

# Implement in order:
# 1. client.py (API wrapper)
# 2. auth.py (credentials)
# 3. transform.py (data conversion)
# 4. sync.py (orchestration)

# Test each module as you go
uv run pytest tests/unit/test_garmin_*.py
```

### 4. Implement CLI Commands

```bash
# Create CLI structure
mkdir -p src/openactivity/cli/garmin
touch src/openactivity/cli/garmin/{__init__,app,auth,sync,athlete,activities,daily}.py

# Implement commands in priority order:
# 1. auth (required for all others)
# 2. sync (core functionality)
# 3. daily (health data - unique value)
# 4. athlete, activities (nice-to-have)

# Manual testing
uv run openactivity garmin auth
uv run openactivity garmin sync
uv run openactivity garmin daily --last 7d
```

### 5. Implement Deduplication

```bash
# Add deduplication logic
# File: src/openactivity/db/queries.py

def detect_duplicates(...):
    # Matching algorithm

def link_activities(...):
    # Create ActivityLink

# Integrate into sync
# File: src/openactivity/providers/garmin/sync.py

def sync_activities(...):
    # ... fetch and store activities
    detect_and_link_duplicates()
```

### 6. Enhance Unified Commands

```bash
# Modify existing commands
# Files: src/openactivity/cli/activities.py

# Add provider filtering
# Add provider badges
# Test with mixed Strava + Garmin data

uv run openactivity activities list
uv run openactivity activity 12345  # Should work with any provider ID
```

### 7. Write Tests

```bash
# Unit tests
uv run pytest tests/unit/test_garmin_*.py -v

# Integration tests (with VCR)
uv run pytest tests/integration/test_garmin_provider.py -v

# Contract tests
uv run pytest tests/contract/ -v

# Full suite
uv run pytest
```

### 8. Manual Testing Checklist

```bash
# Fresh install scenario
rm -rf ~/.local/share/openactivity/  # Clear database

# Auth flow
openactivity garmin auth
# Enter credentials, verify keyring storage

# First sync (full)
openactivity garmin sync
# Should fetch all activities + health data

# Incremental sync
# (wait a day or manually add activity on Garmin)
openactivity garmin sync
# Should only fetch new data

# View activities
openactivity activities list
# Should show Strava + Garmin with badges

# View specific activity
openactivity activity <garmin-id>
# Should auto-detect provider

# View health data
openactivity garmin daily --last 7d
# Should display health metrics

# Deduplication
# Upload same activity to both Strava and Garmin
openactivity garmin sync
openactivity activities list
# Should show [Strava+Garmin] badge
```

---

## Common Gotchas

### Database Migration

**Issue**: Existing Strava activities don't have `provider` or `provider_id`
**Solution**: Migration sets defaults: `provider='strava'`, `provider_id=id`

### Garmin API Quirks

**Issue**: garminconnect library may break if Garmin changes API
**Solution**: Pin library version, add defensive error handling, monitor for breakage

### MFA Support

**Issue**: Garmin MFA requires manual token retrieval
**Solution**: Document workaround (app-specific passwords), detect MFA error and show helpful message

### Deduplication False Positives

**Issue**: Two different activities might match if very similar
**Solution**: Use confidence threshold (0.7), allow manual unlinking via CLI command

### Provider-Specific Fields

**Issue**: Garmin has fields Strava doesn't (HRV, Body Battery)
**Solution**: Use separate tables, don't pollute Activity model

---

## Quick Reference

### Key Files by Component

| Component | Files |
|-----------|-------|
| Database | `db/models.py`, `db/queries.py`, `db/migrations/001_*.py` |
| Garmin Provider | `providers/garmin/{client,auth,transform,sync}.py` |
| Garmin CLI | `cli/garmin/{app,auth,sync,athlete,activities,daily}.py` |
| Unified CLI | `cli/activities.py` (modified) |
| Tests | `tests/unit/test_garmin_*.py`, `tests/integration/test_garmin_provider.py` |

### Command Patterns

```bash
# Provider-specific
openactivity garmin <subcommand>
openactivity strava <subcommand>

# Unified (cross-provider)
openactivity activity <ID>
openactivity activities list [--provider <name>]
```

### Database Queries

```python
# Get all activities (any provider)
activities = session.query(Activity).all()

# Get only Garmin activities
garmin = session.query(Activity).filter_by(provider='garmin').all()

# Check if activity is linked
link = session.query(ActivityLink)\
    .filter((ActivityLink.strava_activity_id == id) |
            (ActivityLink.garmin_activity_id == id))\
    .first()

# Get health data for date
health = session.query(GarminDailySummary)\
    .filter_by(date=target_date).first()
```

---

## Next Steps After Implementation

1. **Documentation**: Update README with Garmin setup instructions
2. **Examples**: Add example workflows to docs
3. **Error Messages**: Audit all error messages for clarity
4. **Performance**: Profile sync performance with large datasets
5. **Monitoring**: Add logging for deduplication hits/misses

---

## Need Help?

- **Spec**: [spec.md](spec.md) - Full feature specification
- **Research**: [research.md](research.md) - Technical decisions and rationale
- **Data Model**: [data-model.md](data-model.md) - Complete database schema
- **Contracts**: [contracts/cli-commands.md](contracts/cli-commands.md) - CLI command reference
- **Strava Reference**: `src/openactivity/providers/strava/` - Similar implementation pattern
