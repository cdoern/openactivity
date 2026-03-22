# Research: Grade-Adjusted Pace & Effort Scoring

## Decision 1: Minetti Energy Cost Model Implementation

**Decision**: Use the Minetti (2002) polynomial cost function to compute the metabolic cost of running at a given grade, then derive equivalent flat pace.

**Rationale**: The Minetti model is the gold standard in exercise physiology for grade-adjusted pace. It's a 5th-degree polynomial relating grade (as a decimal, e.g., 0.10 = 10%) to metabolic cost (J/kg/m). The formula: `C(g) = 155.4g^5 - 30.4g^4 - 43.3g^3 + 46.3g^2 + 19.5g + 3.6`. GAP is derived by computing cost at each grade, averaging the cost ratio relative to flat (C(g)/C(0)), and adjusting actual pace by this ratio.

**Alternatives considered**:
- Simple percentage-based adjustment (e.g., +10s/mile per 100ft gain): Too imprecise, doesn't account for downhill benefit
- Strava's internal GAP model: Proprietary, not available for local computation
- ACSM metabolic equation: Less accurate for steep grades (>15%) and doesn't handle downhill well

## Decision 2: Grade Computation from Streams

**Decision**: Compute grade as `(elevation[i+1] - elevation[i]) / (distance[i+1] - distance[i])` with a rolling average smoothing window of 10 data points to reduce GPS noise.

**Rationale**: Raw elevation streams from GPS devices are noisy. A 10-point rolling average provides adequate smoothing without losing meaningful terrain features. The smoothing window size is a compromise — too small preserves noise, too large flattens real hills.

**Alternatives considered**:
- No smoothing: Produces extreme grade spikes (>100%) from GPS jitter
- Gaussian smoothing: More computationally expensive with marginal accuracy improvement for this use case
- Fixed-distance windowing (e.g., smooth over 50m): Would require resampling streams to uniform distance intervals

## Decision 3: GAP Computation Approach

**Decision**: Compute GAP segment-by-segment by calculating the energy cost ratio at each grade vs flat, then multiply actual time by the weighted average cost ratio.

**Rationale**: This gives per-segment resolution that can be aggregated to per-lap or per-activity level. The formula: `GAP = actual_pace * C(0) / C(grade)`. For segments where grade makes running easier (moderate downhill), GAP will be faster than actual pace. For uphills, GAP will be slower. The overall GAP averages these across the entire activity weighted by distance.

**Alternatives considered**:
- Single average grade for entire activity: Loses all terrain detail, not useful for hilly courses with ups and downs that cancel out
- Time-weighted averaging: Could be biased toward slow uphill segments; distance-weighting is more representative

## Decision 4: Effort Score Formula

**Decision**: Composite score from 4 components, each normalized to 0-25, summed for 0-100 total:
1. **Duration** (25%): Percentile against the user's own activity history
2. **GAP** (25%): Percentile against the user's own GAP distribution (faster GAP = higher score)
3. **Heart Rate** (25%): Average HR as percentage of estimated max HR (220 - age, or from athlete data)
4. **Elevation** (25%): Elevation gain per km, percentiled against history

When HR is unavailable, redistribute its 25% equally: duration 33.3%, GAP 33.3%, elevation 33.3%.

**Rationale**: Using percentiles against the user's own history makes the score personal and meaningful. A 50-effort score means "average for me." Using estimated max HR is standard when actual max is unknown.

**Alternatives considered**:
- Fixed thresholds (e.g., 1hr run = 50 points): Doesn't adapt to user fitness level, a beginner's 30min run might be harder than an expert's 1hr run
- TRIMP (Training Impulse): Requires zone definitions and only uses HR, doesn't account for terrain
- TSS (Training Stress Score): Requires FTP or lactate threshold, too much user configuration needed

## Decision 5: On-the-fly vs Persisted Computation

**Decision**: Compute GAP and effort score on-the-fly from stream data. Do not persist to database.

**Rationale**: Avoids schema changes and migration complexity. Stream data is already stored locally, and GAP computation is O(n) per activity — fast enough for interactive use. For the effort trend command (scanning many activities), caching per-session is sufficient. If performance becomes an issue at scale (>5000 activities), a future optimization can add a cached_gap column.

**Alternatives considered**:
- New database table for computed metrics: Adds schema complexity, migration burden, and stale data risk when algorithms improve
- File-based cache: Adds complexity without meaningful performance benefit for <5000 activities

## Decision 6: Trend Direction Detection

**Decision**: Use simple linear regression on GAP values over the time window. Classify as improving (slope < -2 sec/km/month), declining (slope > +2 sec/km/month), or stable (within threshold).

**Rationale**: Linear regression is simple, interpretable, and sufficient for detecting directional trends. The 2 sec/km/month threshold prevents noise from being classified as a trend.

**Alternatives considered**:
- Moving average crossover: More complex, harder to explain to users
- Mann-Kendall trend test: Statistically rigorous but overkill for a CLI display
