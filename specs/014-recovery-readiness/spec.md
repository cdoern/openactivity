# Feature Specification: Recovery & Readiness Score

**Feature Branch**: `014-recovery-readiness`  
**Created**: 2026-04-03  
**Status**: Draft  
**Input**: User description: "Combine Garmin health metrics (HRV, sleep, Body Battery, stress) with training load to produce a daily readiness score (0-100). New command: openactivity analyze readiness."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Today's Readiness Score (Priority: P1)

A runner opens their terminal before a morning run and runs `openactivity analyze readiness` to see whether today is a good day to push hard or take it easy. The system combines their overnight HRV, sleep quality, current training form (TSB), and recent volume trend into a single 0–100 readiness score with a plain-language recommendation.

**Why this priority**: This is the core value proposition — the single daily number that tells the user what to do today. Everything else builds on this.

**Independent Test**: Can be fully tested by running the command with Garmin health data and training history in the database; delivers an actionable score and recommendation.

**Acceptance Scenarios**:

1. **Given** Garmin daily summaries and training activities exist in the database, **When** the user runs `openactivity analyze readiness`, **Then** the system displays today's readiness score (0–100), a label (e.g., "Go Hard", "Easy Day", "Rest"), a component breakdown (HRV, sleep, form, volume), and a recommendation.
2. **Given** the user has training data but no Garmin health metrics, **When** the user runs `openactivity analyze readiness`, **Then** the system computes a partial score using only TSB and volume components (50% of total weight), clearly indicates which components are unavailable, and displays the partial score with a note about missing data.
3. **Given** no training data or health data exists, **When** the user runs `openactivity analyze readiness`, **Then** the system displays a helpful error directing the user to sync or import data first.

---

### User Story 2 — Readiness Trend Over Time (Priority: P2)

A user wants to see how their readiness has trended over the past 30 days to understand patterns (e.g., readiness drops every Monday after a long Sunday run). They run `openactivity analyze readiness --last 30d` and see a daily history.

**Why this priority**: Historical context transforms a single number into an insight tool. Users can correlate readiness with training outcomes.

**Independent Test**: Can be tested by running with `--last 30d` flag; displays a table of daily readiness scores over the requested window.

**Acceptance Scenarios**:

1. **Given** 30+ days of health and training data, **When** the user runs `openactivity analyze readiness --last 30d`, **Then** the system displays a daily table showing date, readiness score, label, and individual component values.
2. **Given** the user specifies `--last 7d`, **When** the command runs, **Then** only the last 7 days are shown.
3. **Given** data exists for only 10 of the last 30 days, **When** the user runs `--last 30d`, **Then** the system shows scores for available days and indicates gaps.

---

### User Story 3 — JSON Output for Agents (Priority: P3)

An AI agent or script queries readiness data programmatically via `openactivity --json analyze readiness` to incorporate into automated training plan decisions.

**Why this priority**: JSON output enables integration with agents and external tools, but the human-readable output serves most users first.

**Independent Test**: Can be tested by running with `--json` flag and validating the output structure contains score, label, components, and recommendation.

**Acceptance Scenarios**:

1. **Given** health and training data exist, **When** the user runs `openactivity --json analyze readiness`, **Then** the output is valid JSON containing: `score`, `label`, `recommendation`, `components` (with each component's score, weight, available flag, and description), and `date`.
2. **Given** the `--last 30d` flag is used with `--json`, **When** the command runs, **Then** the JSON contains a `daily` array with per-day readiness entries.

---

### Edge Cases

- What happens when HRV data is present for some days but not others within the trend window? — System computes readiness using available components, adjusting weights proportionally for missing data, and flags which components were unavailable per day.
- What happens when the user has only 1 day of data? — System computes and displays readiness for that single day; trend is not available.
- What happens when Garmin daily summary exists but all health fields are null? — System treats health components as unavailable and falls back to training-only scoring.
- What happens when Body Battery or stress data is missing but HRV and sleep are present? — HRV component uses HRV data only (Body Battery and stress are supplementary inputs to the HRV component); sleep component uses sleep score.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute a daily readiness score from 0 to 100 combining up to four weighted components: HRV vs baseline (30%), sleep quality (20%), training form/TSB (30%), and volume trend (20%).
- **FR-002**: System MUST compute the HRV component by comparing today's HRV to a rolling 7-day baseline. Higher HRV relative to baseline = higher score. If HRV is unavailable, this component is marked unavailable and its weight is redistributed proportionally among available components.
- **FR-003**: System MUST compute the sleep component from the Garmin sleep score (0–100 stored in `garmin_daily_summary`). If unavailable, weight is redistributed.
- **FR-004**: System MUST compute the training form component from the current day's TSB value (from the fitness/fatigue model). Positive TSB (fresh) scores higher; deeply negative TSB (fatigued) scores lower.
- **FR-005**: System MUST compute the volume trend component by comparing recent 7-day training volume to the prior 7-day volume. Stable or slightly reduced volume scores higher; sharp spikes score lower (injury risk).
- **FR-006**: System MUST assign a recommendation label based on the composite score: "Go Hard" (score >= 75), "Easy Day" (score 40–74), "Rest" (score < 40).
- **FR-007**: System MUST support a `--last` flag accepting time window strings (e.g., "7d", "30d", "90d") to display historical daily readiness scores.
- **FR-008**: System MUST support `--json` output containing score, label, recommendation, component breakdown, and daily history when `--last` is specified.
- **FR-009**: System MUST gracefully degrade when health data is partially or fully missing — compute using available components with proportionally redistributed weights, and clearly indicate which components are unavailable.
- **FR-010**: System MUST display the readiness command output under `openactivity analyze readiness` (top-level) and `openactivity strava analyze readiness` (alias with implicit provider filter).

### Key Entities

- **Daily Readiness**: A computed daily record containing: date, composite score (0–100), label, recommendation, and per-component scores (HRV, sleep, form, volume) with availability flags. Not persisted — computed on-the-fly from existing data.
- **GarminDailySummary** (existing): Contains hrv_avg, sleep_score, body_battery_max/min, stress_avg per day.
- **GarminSleepSession** (existing): Contains per-night sleep stage breakdowns and sleep_score.
- **Fitness/Fatigue Model** (existing): Provides daily TSB (Training Stress Balance) values.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can retrieve today's readiness score and recommendation in a single command invocation.
- **SC-002**: Readiness score computation completes in under 2 seconds for users with up to 2 years of training data.
- **SC-003**: When all four data components are available, the readiness score reflects all four weighted inputs; when components are missing, the score adjusts proportionally without requiring user intervention.
- **SC-004**: Historical readiness trend displays daily scores for any requested window up to 1 year.
- **SC-005**: JSON output provides a complete, machine-parseable readiness payload suitable for agent consumption.

## Assumptions

- HRV, sleep, and Body Battery data are imported via existing Garmin import functionality and stored in `garmin_daily_summary`.
- TSB values are computed on-the-fly by the existing fitness/fatigue model (`analyze_fitness` / `compute_fitness_fatigue`).
- Readiness scores are not persisted to the database — they are computed on demand from existing data. This avoids stale data and additional schema changes.
- The HRV baseline is a simple 7-day rolling average. No advanced HRV analytics (e.g., RMSSD decomposition) are in scope.
- Body Battery and stress data from Garmin are supplementary signals to the HRV component (used to adjust confidence) rather than independent components, keeping the model at 4 components.
