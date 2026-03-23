# Research: Race Predictor & Readiness Score

## Decision 1: Prediction Formula

**Decision**: Use the Riegel formula: `T2 = T1 * (D2/D1)^1.06`
**Rationale**: Industry standard for recreational runners. Peter Riegel's 1981 formula is simple, well-validated, and used by most running calculators. The exponent 1.06 works well for distances from 1 mile to marathon.
**Alternatives considered**:
- Cameron model (adjustable exponent by fitness level) — more complex, minimal improvement for recreational runners
- Purdy points system — designed for comparing performances, not predicting race times
- VO2max-based prediction (Jack Daniels VDOT) — requires VO2max estimation, adds complexity without clear benefit given our data

## Decision 2: Reference Effort Selection

**Decision**: Use PersonalRecord entries from the existing PR database. Find best efforts at standard distances (1mi, 5K, 10K, half, marathon) from the last 6 months. When multiple reference distances exist, compute predictions from each and average them (weighted by recency and distance proximity to target).
**Rationale**: The PR scanning system already extracts best efforts with sliding-window accuracy. Reusing it avoids duplicate computation. Multiple reference points improve accuracy.
**Alternatives considered**:
- Scan activities on-the-fly each time — slower, redundant with existing PR system
- Use only the single closest reference distance — less accurate than averaging multiple predictions

## Decision 3: Confidence Interval Calculation

**Decision**: Base confidence interval width on: (1) number of reference efforts (more = narrower), (2) recency of efforts (older = wider), (3) spread of predictions from different reference distances (more agreement = narrower). Apply as percentage of predicted time: ±2% baseline, widened by factors.
**Rationale**: Simple and intuitive. Users see a range like "42:30 - 44:15" that naturally widens when data is sparse or old.
**Alternatives considered**:
- Statistical prediction intervals from regression — requires more data points than typical users have
- Fixed percentage bands — doesn't adapt to data quality

## Decision 4: Readiness Score Components

**Decision**: Four components with fixed weights:
- Training consistency (30%): % of last 8 weeks with ≥3 activities
- Volume trend (25%): last-4-weeks volume vs prior-4-weeks volume ratio
- Taper status (25%): volume decreasing last 2-3 weeks while intensity maintained
- PR recency (20%): days since most recent PR at any reference distance

**Rationale**: Covers the key dimensions coaches assess: are you training regularly, is volume appropriate, are you tapering correctly, and is your fitness demonstrated recently. Weights reflect coaching consensus that consistency and volume/taper matter most.
**Alternatives considered**:
- Include HR-based recovery metrics — not all users have HR data; graceful degradation handled but not weighted
- User-configurable weights — adds complexity, most users won't tune these
- Include sleep/recovery data — requires Garmin provider (Phase 2)

## Decision 5: CLI Structure

**Decision**: New `predict` subcommand under `strava` (not under `analyze`). Command: `openactivity strava predict --distance 10K`.
**Rationale**: Prediction is a distinct capability, not just analysis. It deserves its own command group. Follows the pattern where major features get their own subcommand (`strava records`, `strava analyze`).
**Alternatives considered**:
- `strava analyze predict` — nests too deep, prediction is a first-class feature
- `strava race` — less discoverable, "predict" is clearer about what it does
