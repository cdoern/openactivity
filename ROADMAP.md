# OpenActivity Roadmap

**Created**: 2026-03-21
**Status**: Active
**Process**: Feed each feature description into `/speckit.specify` to generate a spec, then `/speckit.plan`, `/speckit.tasks`, and `/speckit.implement` to execute.

---

## Phase 1: Advanced Strava Analytics

Features that build on existing Strava data and the current `openactivity strava analyze` command group. No new providers needed — these all work with the activity data, streams, and segments already synced to the local DB.

### Feature 1.1: Custom Time-Range Comparisons

**Branch**: `002-time-range-compare`

Compare any two arbitrary date ranges across all metrics. "How did my Jan-Mar 2026 compare to Jan-Mar 2025?" Strava only offers YTD vs prior year.

- New command: `openactivity strava analyze compare`
- Flags: `--range1 2025-01-01:2025-03-31 --range2 2026-01-01:2026-03-31`
- Optional: `--type Run|Ride` filter
- Output: side-by-side table showing delta for each metric (distance, duration, elevation, count, avg pace, avg HR)
- Percentage change with direction indicators
- `--json` output for agent consumption
- Agents can use this to answer: "Am I training more or less than last year at this point?"

### Feature 1.2: Personal Records Database

**Branch**: `003-personal-records`

Automatically detect and track PRs across standard distances (1mi, 5K, 10K, half marathon, marathon, 1hr power, etc.) by scanning activity GPS/distance streams. Strava only tracks a handful of preset distances and doesn't show PR progression over time.

- New commands:
  - `openactivity strava records list` — show current PRs by distance/duration
  - `openactivity strava records history --distance 5K` — show PR progression over time
  - `openactivity strava records scan` — re-scan all activities for PRs (or run automatically during sync)
- New DB model: `PersonalRecord` (distance_type, time, pace, activity_id, date, previous_record_id)
- Detection: scan distance/time streams with sliding window for best effort at each standard distance
- Support custom distances: `openactivity strava records add-distance 15K`
- Cycling: best power for 5s, 1min, 5min, 20min, 60min (extend existing power curve into persistent records)
- `--json` output for agents to answer: "What's my 5K PR and when did I set it?"

### Feature 1.3: Grade-Adjusted Pace (GAP) & Effort Scoring

**Branch**: `004-gap-effort`

Compute Grade-Adjusted Pace from elevation and distance streams so users can compare efforts across hilly vs flat courses. Strava shows GAP per-activity but doesn't let you trend it or compare across activities. Add a normalized effort score per activity.

- Extend `openactivity strava activity <ID>` detail view with GAP per split and overall
- New command: `openactivity strava analyze effort` — trend GAP over time
- Flags: `--last 90d|6m|1y`, `--type Run`
- Algorithm: Apply Minetti energy cost model to grade stream, compute equivalent flat pace
- Effort score: normalize each activity to a 0-100 scale based on duration, GAP, HR, and elevation
- Enables fair comparison: a hilly trail run vs a flat road run
- `--json` output for agents to answer: "What was my hardest effort this month regardless of terrain?"

### Feature 1.4: Training Block / Periodization Detector

**Branch**: `005-periodization`

Automatically detect training phases (base, build, peak, recovery) from volume and intensity patterns over time. Help users understand where they are in their training cycle without manual logging.

- New command: `openactivity strava analyze blocks`
- Flags: `--last 6m|1y|all`, `--type Run|Ride`
- Algorithm:
  - Compute weekly volume and intensity (HR/pace-based)
  - Classify weeks: recovery (<70% of 4-week avg volume), base (high volume, low intensity), build (rising volume + intensity), peak (high intensity, tapering volume)
  - Group consecutive similar weeks into named blocks
- Output: timeline of blocks with date ranges, avg volume, avg intensity, classification
- `--json` output for agents to answer: "Am I in a build phase or should I be recovering?"

### Feature 1.5: Race Predictor & Readiness Score

**Branch**: `006-race-predictor`

Predict race times at target distances using recent training data, PR history, and current fitness. Neither Strava nor Garmin does cross-metric prediction with training context.

- New command: `openactivity strava predict`
- Flags: `--distance 5K|10K|half|marathon`, `--race-date 2026-06-15`
- Algorithm:
  - Riegel formula from recent best efforts at shorter distances
  - Adjust for current training volume trend (are they building or tapering?)
  - Factor in recent intensity distribution
  - Confidence interval based on data recency and consistency
- Readiness score (0-100): composite of training consistency, recent volume trend, taper status, and PR recency
- Output: predicted time, pace, confidence range, readiness score with breakdown
- `--json` output for agents building training plans or race-day strategies

### Feature 1.6: Cross-Activity Correlation Engine

**Branch**: `007-correlations`

Correlate any two metrics across activities to find patterns. "Does my weekly mileage correlate with my resting HR?" "Do weeks with more zone 2 improve my next month's pace?" Pure data science that no consumer platform offers.

- New command: `openactivity strava analyze correlate`
- Flags: `--x weekly_distance --y avg_pace`, `--last 1y`, `--lag 0|1|2|4` (weeks)
- Supported metrics: weekly_distance, weekly_duration, weekly_elevation, avg_pace, avg_hr, max_hr, zone2_pct, zone4_pct, activity_count, rest_days, longest_run
- Algorithm: Pearson and Spearman correlation with p-value
- Lag analysis: does this week's metric X predict next week's metric Y?
- Output: correlation coefficient, p-value, strength label (weak/moderate/strong), scatter data points
- `--json` output for agents to discover training patterns: "What single factor most predicts my pace improvement?"

### Feature 1.7: Route & Segment Decay Analysis

**Branch**: `008-segment-decay`

For repeated routes and segments, show performance trends over time. Strava shows raw times per effort but no trend analysis, no adjustment for conditions, no decay/improvement detection.

- New command: `openactivity strava segment <ID> trend`
- Extend `openactivity strava segments list` with trend indicators (improving/declining/stable)
- Algorithm:
  - Collect all efforts on a segment, sorted by date
  - Compute linear regression on elapsed time vs date
  - Report: trend direction, rate of change (seconds/month), best/worst/recent effort
  - Optional: adjust for HR (was the effort harder or easier?) if HR data available
- New command: `openactivity strava analyze routes` — detect repeated routes (similar start/end + distance) and show trends across them even if not on official Strava segments
- `--json` output for agents to answer: "Am I getting faster or slower on my regular Tuesday loop?"

---

## Phase 2: Garmin Provider

Add Garmin Connect as a second data provider, following the existing provider interface pattern. This unlocks HRV, Body Battery, sleep, respiration, and other health metrics that Strava doesn't have.

### Feature 2.1: Garmin FIT File Import ✅ COMPLETE

**Branch**: `010-garmin-provider`

Import Garmin activity data via FIT files (no API dependency — Garmin rate-limits/bans automated API access). Supports import from USB device, Garmin Express folder, bulk export ZIP, and custom directories. Unified `openactivity activities list` and `openactivity activity <ID>` commands work across all providers with provider badges.

- FIT file import: `openactivity garmin import --from-device|--from-connect|--from-zip|--from-directory`
- Unified commands: `openactivity activities list`, `openactivity activity <ID>` (provider-agnostic)
- Provider filter: `--provider garmin|strava` on activities list
- Provider badges: [Strava], [Garmin], [Strava+Garmin] in activity listings
- Library: `fitparse` (FIT file parsing, no API needed)
- Deduplication: by provider_id (start timestamp) and cross-provider linking by time/type/duration
- DB: `provider` + `provider_id` columns on activities, `activity_links` table, Garmin health tables

### Feature 2.2: Cross-Provider Activity Linking ✨ NEW

**Branch**: `011-cross-provider-linking`

Automatically detect and link duplicate activities that exist in both Strava and Garmin. The matching algorithm and `activity_links` table already exist from Feature 2.1 but are never invoked. Wire up automatic linking during garmin import and strava sync, add a manual `openactivity activities link` command for bulk linking existing data, and ensure linked activities appear as a single entry in unified views.

- New command: `openactivity activities link` — scan all unlinked activities and create cross-provider links
- Auto-link during `openactivity garmin import` — after importing, scan new activities for Strava matches
- Auto-link during `openactivity strava sync` — after syncing, scan new activities for Garmin matches
- Matching: ±60s start time, same activity type (with fuzzy matching), ±5% duration
- Confidence scoring: weighted combination of time proximity (60%) and duration similarity (40%)
- `openactivity activities list` already shows `[Strava+Garmin]` badge for linked activities
- `openactivity activities link --dry-run` to preview matches without committing
- `openactivity activities link --unlink <ID>` to remove incorrect links
- Stats output: "Linked X of Y potential matches (Z already linked)"

### Feature 2.3: Unified Command Refactoring

**Branch**: future (after `010-garmin-provider` merges)

Refactor remaining overlapping Strava-specific commands to be provider-agnostic at the root level. Currently `openactivity activities list` and `openactivity activity <ID>` are unified; remaining commands like `analyze`, `records`, `predict`, `export` should also be promoted to work across providers.

- Move `openactivity strava analyze` → `openactivity analyze` (reads from all providers)
- Move `openactivity strava records` → `openactivity records` (scans all provider activities)
- Move `openactivity strava predict` → `openactivity predict` (uses best data from any provider)
- Keep provider-specific commands under their namespaces (`strava auth`, `strava sync`, `garmin import`)
- Ensure all analysis commands respect `--provider` filter for per-provider analysis

---

## Phase 3: Cross-Provider & Recovery Analytics

Features that combine data from multiple providers or leverage Garmin-specific health metrics for deeper insights.

### Feature 3.1: Fitness / Fatigue Model (ATL/CTL/TSB) ✅

**Branch**: `012-fitness-fatigue-model` | **Status**: Complete

The classic training peaks model. Strava locks this behind Summit ($60/yr). Compute Acute Training Load (fatigue), Chronic Training Load (fitness), and Training Stress Balance (form) from HR data using TRIMP-based TSS.

- Command: `openactivity strava analyze fitness`
- Flags: `--last 6m|1y|all`, `--type Run|Ride`, `--chart`, `--output`, `--json`
- Per-activity TSS shown in `openactivity strava activity <ID>` detail view
- Status classification: peaking/maintaining/overreaching/detraining
- Chart generation via matplotlib

### Feature 3.2: Training Intensity Distribution Analysis

**Branch**: `011-intensity-distribution`

Classify the user's training approach: polarized (80/20 easy/hard), pyramidal (descending time per zone), or threshold-heavy (too much zone 3). Strava shows zone bars per activity but never analyzes the overall pattern.

- New command: `openactivity analyze intensity`
- Flags: `--last 90d|6m|1y`, `--type Run|Ride`, `--zone-type heartrate|power`
- Output: percentage of total training time in each zone, classification label, comparison to recommended distributions
- Recommendation: if >25% in zone 3, flag "potential junk miles — consider more polarized approach"
- `--json` for agents to provide coaching: "You're doing too much moderate intensity, shift 15% of zone 3 time to zone 1"

### Feature 3.3: Recovery & Readiness Score

**Branch**: `012-recovery-readiness`

Combine Garmin health metrics (HRV, sleep, Body Battery, stress) with training load to produce a daily readiness score. This is what Whoop charges $30/mo for.

- New command: `openactivity analyze readiness`
- Inputs: HRV trend (from Garmin), sleep quality (from Garmin), TSB (from fitness model), recent training volume
- Algorithm: weighted composite score 0-100
  - HRV vs 7-day baseline (30% weight)
  - Sleep score (20% weight)
  - TSB / form (30% weight)
  - Volume trend / ramp rate (20% weight)
- Output: today's readiness score, component breakdown, recommendation (go hard / easy day / rest)
- Historical trend: `--last 30d` to see readiness over time
- `--json` for agents: the single most actionable daily metric

### Feature 3.4: Heart Rate Drift Analysis

**Branch**: `013-hr-drift`

Cardiac drift (HR rising at constant pace over a long effort) is a key aerobic fitness marker. Compute drift percentage per activity and trend it over time. Improving drift = improving aerobic efficiency. Neither platform calculates this.

- New command: `openactivity analyze drift`
- Flags: `--last 90d|6m`, `--type Run`, `--min-duration 30m` (only meaningful for longer efforts)
- Algorithm:
  - Split activity HR and pace streams into first half vs second half
  - Drift % = (avg HR second half - avg HR first half) / avg HR first half * 100
  - Only for steady-state efforts (filter out intervals by pace variance)
- Output: per-activity drift %, trend over time, fitness assessment
- `--json` for agents: "Your cardiac drift has improved from 8% to 4% over 3 months — strong aerobic adaptation"

### Feature 3.5: Injury Risk & Overtraining Alerts

**Branch**: `014-injury-risk`

Flag dangerous training patterns before they cause injury. Sports science-backed alerts using acute:chronic workload ratio, training monotony, and strain metrics.

- New command: `openactivity analyze risk`
- Algorithm:
  - Acute:Chronic Workload Ratio (ACWR): 7-day load / 28-day avg load. Flag if >1.5 (spike) or <0.8 (detraining)
  - Training monotony: daily load std dev / mean. Flag if >2.0
  - Training strain: weekly load * monotony. Flag if strain exceeds historical 85th percentile
  - Consecutive days without rest: flag if >10
- Optional Garmin inputs: poor sleep + high strain = elevated risk
- Output: risk level (low/moderate/high), contributing factors, recommendation
- `--json` for agents: the highest-value proactive alert — "Take a rest day, your injury risk is elevated"

### Feature 3.6: Sleep & Performance Correlation

**Branch**: `015-sleep-performance`

Correlate Garmin sleep data with next-day training performance. Answer: "Does poor sleep actually hurt my workouts?"

- New command: `openactivity analyze sleep-impact`
- Flags: `--last 90d|6m`
- Algorithm:
  - Match sleep sessions to next-day activities
  - Correlate sleep score / duration / deep sleep % with activity performance (pace, HR, effort score, RPE)
  - Lag analysis: does sleep quality predict performance 1-2 days out?
- Output: correlation strength, optimal sleep duration for performance, worst-performing sleep patterns
- `--json` for agents building holistic recommendations

---

## Execution Process

For each feature above:

```bash
# 1. Generate the spec (creates branch and checks it out automatically)
/speckit.specify "<paste the feature description above>"

# 2. Clarify any gaps
/speckit.clarify

# 3. Generate the implementation plan
/speckit.plan

# 4. Generate tasks
/speckit.tasks

# 5. Analyze for consistency
/speckit.analyze

# 6. Execute implementation
/speckit.implement
```

Features within each phase are independent and can be built in any order. Phase 2 (Garmin) should complete before Phase 3 features that depend on Garmin data (3.3, 3.5, 3.6). Phase 3 features that only use activity data (3.1, 3.2, 3.4) can start anytime after Phase 1.
