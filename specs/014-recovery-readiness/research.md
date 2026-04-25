# Research: Recovery & Readiness Score

## Decision 1: Readiness Score Architecture

**Decision**: Create a new `src/openactivity/analysis/readiness.py` module with a `compute_readiness()` orchestrator. Do NOT reuse `predict.py`'s `compute_readiness_score()` — that function scores race readiness (consistency, taper, PR recency), which is a different concept than daily recovery readiness (HRV, sleep, form, volume).

**Rationale**: The predict readiness score answers "Am I ready to race?" while this feature answers "Should I train hard today?" Different inputs, different weights, different output. Sharing code would create confusing coupling.

**Alternatives considered**:
- Extend `predict.py`'s readiness — rejected because it would conflate two distinct concepts and add complexity to an already large module.
- Add to `fitness.py` — rejected because fitness.py is specifically about ATL/CTL/TSB computation, not composite scoring.

## Decision 2: HRV Component Scoring

**Decision**: Compare today's `hrv_avg` from `GarminDailySummary` to a 7-day rolling average. Score = percentile position within a ±30% band around the baseline. HRV at or above baseline scores 75+; HRV 15%+ below baseline scores below 40.

**Rationale**: HRV is highly individual — absolute values are meaningless without personal baseline. A 7-day rolling average is the standard approach used by Whoop, Oura, and sports science literature. Body Battery and stress can optionally boost/dampen the HRV score as modifiers.

**Alternatives considered**:
- 14-day or 30-day baseline — rejected; 7 days captures acute recovery without oversmoothing.
- Use Body Battery as an independent 5th component — rejected; keeping 4 components aligns with the spec and avoids over-weighting Garmin-specific data.

## Decision 3: TSB-to-Score Mapping

**Decision**: Map TSB to a 0–100 component score using a piecewise linear function:
- TSB >= +15 → score 90 (very fresh)
- TSB +5 to +15 → score 70-90
- TSB -10 to +5 → score 50-70 (neutral)
- TSB -20 to -10 → score 30-50 (tired)
- TSB < -20 → score 10-30 (very fatigued)

**Rationale**: These thresholds align with standard TSB interpretation from training peaks literature.

## Decision 4: Volume Trend Scoring

**Decision**: Compare last-7-day total distance to prior-7-day total distance. Ratio near 1.0 (stable) or 0.7–0.9 (slight taper) scores high. Ratio > 1.3 (sharp ramp) scores low (injury risk). Ratio < 0.5 scores moderate (detraining).

**Rationale**: Acute:Chronic workload ratio principles — sharp volume spikes correlate with injury risk.

## Decision 5: Weight Redistribution for Missing Components

**Decision**: When a component is unavailable (e.g., no Garmin data), redistribute its weight proportionally among available components. Example: if HRV (30%) is missing, form becomes 30/70*30%=~43%, sleep becomes 20/70*20%=~29%, volume becomes 20/70*20%=~29%.

**Rationale**: Simple proportional redistribution preserves relative importance of available components without special-case logic.

## Decision 6: Data Access Pattern

**Decision**: Add query functions to `db/queries.py` for Garmin health data: `get_daily_summaries(session, after, before)` and `get_daily_summary(session, date)`. Compute TSB by calling existing `compute_daily_tss()` + `compute_fitness_fatigue()` from `fitness.py`.

**Rationale**: Follows existing patterns — all DB queries go through `queries.py`, all analysis through `analysis/` modules.
