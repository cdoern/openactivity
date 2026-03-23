# Research: Training Block / Periodization Detector

## Decision 1: Week Classification Algorithm

**Decision**: Use a 4-week rolling average of volume as the baseline, combined with a normalized intensity score (0-100), to classify each week into one of four phases.

**Rationale**: The 4-week rolling average is standard in sports science for smoothing weekly variability. Classification rules:
- **Recovery**: Volume < 70% of 4-week rolling average
- **Base**: Volume >= 70% of rolling avg AND intensity < 60
- **Build**: Volume >= 70% of rolling avg AND intensity >= 60 AND volume rising
- **Peak**: Intensity >= 70 AND volume tapering (decreasing for 2+ weeks)

These thresholds align with common periodization models used by coaches and training platforms.

**Alternatives considered**:
- Machine learning clustering (k-means on volume/intensity): Overkill for 4 categories with well-defined rules, non-deterministic
- Fixed volume thresholds (e.g., >30mi/week = base): Doesn't adapt to individual fitness levels
- Strava's Relative Effort: Proprietary, not available locally

## Decision 2: Intensity Score Computation

**Decision**: Compute intensity as a 0-100 normalized score. When HR is available, use average HR as a percentage of estimated max HR (observed max or 220-age default). When HR is unavailable, use pace relative to the user's pace distribution (percentile rank).

**Rationale**: HR is the gold standard for intensity measurement but not always available (especially older activities or activities without a HR monitor). Pace-based fallback provides a reasonable proxy. Using percentile rank against the user's own history makes it personal — a 9:00/mi pace means different intensity for different runners.

**Alternatives considered**:
- HR zones only: Would exclude activities without HR data
- RPE (Rate of Perceived Exertion): Requires manual input, defeats the purpose of automatic detection
- Power-based (TSS): Only available for cycling with power meters, too narrow

## Decision 3: Block Grouping Strategy

**Decision**: Group consecutive weeks with the same classification into a single block. Force a block boundary when there's a gap of >14 days with no activities.

**Rationale**: Simple consecutive grouping produces intuitive blocks. The 14-day gap rule prevents a vacation from being included in an adjacent training block, which would be misleading.

**Alternatives considered**:
- Allow 1-week classification changes without breaking a block: Adds complexity and can mask real phase transitions
- Fixed-length blocks (e.g., always 4 weeks): Doesn't match real training patterns which vary in length

## Decision 4: On-the-fly vs Persisted Computation

**Decision**: Compute blocks on-the-fly from activity data. Do not persist to database.

**Rationale**: Block detection only needs activity-level metrics (distance, duration, HR, speed) which are already stored. No stream processing required. Aggregating weeks is O(n) over activities — fast enough for interactive use even with 1000+ activities. Avoids schema changes.

**Alternatives considered**:
- Cache weekly summaries in a table: Adds schema complexity for marginal performance gain
- Persist detected blocks: Stale data risk when new activities are synced

## Decision 5: Week Boundaries

**Decision**: Use ISO week numbering (Monday through Sunday).

**Rationale**: ISO weeks are the international standard and align with how most training plans are structured. Monday start is conventional in endurance sports training.

**Alternatives considered**:
- Sunday-Saturday weeks: US convention but less common in training contexts
- Configurable start day: Adds complexity without meaningful benefit
