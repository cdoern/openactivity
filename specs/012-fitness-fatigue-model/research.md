# Research: Fitness/Fatigue Model (ATL/CTL/TSB)

**Feature**: 012-fitness-fatigue-model
**Date**: 2026-03-24

## R1: TSS Calculation Method

**Decision**: Use heart-rate-based TRIMP (Training Impulse) for TSS calculation.

**Rationale**: HR data is universally available across both Strava (176/200 activities) and Garmin (175/175 activities). Power-based TSS requires a power meter and FTP which most runners don't have. TRIMP is the standard HR-based training load metric in sports science.

**Formula**: `TRIMP = duration_minutes × (avg_HR - rest_HR) / (max_HR - rest_HR) × 0.64 × e^(1.92 × hr_ratio)`
- Where `hr_ratio = (avg_HR - rest_HR) / (max_HR - rest_HR)`
- The exponential weighting means higher HR zones contribute disproportionately more stress
- Normalize to TSS scale: `TSS = TRIMP × (100 / reference_TRIMP)` where reference is a 60-min effort at threshold

**Simplified fallback**: When only average HR is available (no stream), use the same formula with activity `average_heartrate` and `moving_time`.

**Alternatives considered**:
- Power-based TSS (IF² × duration / 3600 × 100) — rejected because power data not available on all activities
- RPE-based estimation — rejected because subjective and not recorded
- Simple duration × intensity — rejected because doesn't account for HR zone exponential effect

## R2: Max Heart Rate Estimation

**Decision**: Use the highest observed `max_heartrate` across all activities, consistent with existing analysis modules (gap.py, blocks.py, predict.py all use this approach with a default of 190).

**Rationale**: The codebase already uses `max(activity.max_heartrate for all activities)` as the standard approach. Age-based formulas (220 - age) are notoriously inaccurate. Observed max HR from actual hard efforts is more reliable.

**Resting HR**: Estimate as `min(activity.average_heartrate for easy activities)` or default to 60 bpm. Garmin daily summaries have `resting_hr` but that data isn't reliably imported yet.

**Alternatives considered**: Age-based formula (220-age) — rejected, no age field on Athlete model and formula is inaccurate.

## R3: ATL/CTL Exponential Weighted Average

**Decision**: Use standard exponential decay formula matching TrainingPeaks implementation.

**Formula**:
- `ATL_today = ATL_yesterday + (TSS_today - ATL_yesterday) / 7`
- `CTL_today = CTL_yesterday + (TSS_today - CTL_yesterday) / 42`
- `TSB_today = CTL_today - ATL_today`

**Rationale**: This is the universally accepted formula used by TrainingPeaks, Strava Summit, Golden Cheetah, and all major platforms. The time constants (7 and 42 days) are from Banister's impulse-response model.

**Alternatives considered**: EWMA with different time constants — rejected to match industry standard.

## R4: Deduplication of Linked Activities

**Decision**: When computing daily TSS, exclude linked Garmin activities (same approach as `get_activities()` dedup filter from Feature 011).

**Rationale**: The `get_activities()` function already filters out linked Garmin duplicates when no provider filter is set. Reuse this behavior for consistency. The Strava copy is the primary and will be used for TSS.

**Alternatives considered**: Averaging TSS from both copies — rejected because they should be identical data.

## R5: Chart Generation

**Decision**: Use matplotlib (already a project dependency) to generate PNG charts with CTL, ATL, and TSB plotted on the same timeline.

**Rationale**: matplotlib is listed in the project dependencies. The chart should show three lines (CTL blue, ATL red, TSB green/dashed) with a horizontal line at TSB=0. Save to file with `--output` or display inline.

**Alternatives considered**: go-echarts was listed for Go version — N/A for Python.

## R6: Training Status Classification

**Decision**: Classify based on TSB value and CTL trend over the last 14 days.

**Logic**:
- **Peaking**: CTL > 14-day-ago CTL AND TSB > 5 (fit and fresh)
- **Maintaining**: abs(CTL - 14-day-ago CTL) < 5 AND abs(TSB) < 10 (stable)
- **Overreaching**: CTL > 14-day-ago CTL AND TSB < -15 (building but fatigued)
- **Detraining**: CTL < 14-day-ago CTL - 5 AND TSB > 5 (losing fitness, too rested)

**Alternatives considered**: More granular states (tapering, freshening, etc.) — rejected for v1 simplicity, can add later.

## R7: CLI Command Placement

**Decision**: Add `fitness` command to the existing analyze command group in `cli/strava/analyze.py`, following the exact same pattern as all other analyze commands.

**Rationale**: All 9+ existing analyze commands follow the same structure. The fitness command fits naturally here. It works with data from both providers (linked activities already handled).

## R8: Integration with Activity Detail View

**Decision**: Compute TSS on-the-fly when showing activity detail, similar to how GAP is computed in `show_activity()`.

**Rationale**: The GAP pattern (compute_gap imported and called inline) is already established. TSS computation is lightweight (just math on avg HR + duration) and doesn't need caching.
