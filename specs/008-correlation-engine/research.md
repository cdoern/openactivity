# Research: Cross-Activity Correlation Engine

## Decision 1: Statistical Library

**Decision**: Use `scipy.stats` for Pearson and Spearman correlation with p-values.
**Rationale**: `scipy.stats.pearsonr` and `scipy.stats.spearmanr` return both the correlation coefficient and p-value in a single call. Reimplementing Pearson r is trivial, but Spearman rank correlation with proper p-value computation (using the t-distribution approximation for small samples) is non-trivial.
**Alternatives considered**:
- Pure Python implementation — feasible for Pearson but error-prone for Spearman p-values
- numpy only — can compute r but not p-values without additional math
- statsmodels — heavier dependency than needed for two functions

## Decision 2: Metric Computation Approach

**Decision**: Compute all weekly metrics in a single pass over aggregated week data. Each metric is a function that takes a WeekSummary dict and returns a float or None (missing).
**Rationale**: Clean separation — metric functions are independently testable, and adding new metrics later is a one-line addition to a registry dict.
**Alternatives considered**:
- Pre-compute all metrics into a DataFrame — adds pandas dependency unnecessarily
- Compute metrics lazily on demand — more complex, no performance benefit for <52 rows

## Decision 3: Missing Data Handling

**Decision**: Exclude weeks where either the X or Y metric is None. Report usable vs total weeks in output.
**Rationale**: Standard statistical practice — pairwise deletion for missing data. Users need to know how many points were used.
**Alternatives considered**:
- Impute missing values (mean/median) — can mask real patterns, inappropriate for small samples
- Require complete data (error if any missing) — too restrictive, HR data is commonly missing

## Decision 4: Lag Implementation

**Decision**: For lag N, pair X[i] with Y[i+N]. This means "does this week's X predict Y in N weeks?" The last N weeks of X and first N weeks of Y are unused.
**Rationale**: This is the standard time-series cross-correlation approach. Clear interpretation: positive lag means X precedes Y.
**Alternatives considered**:
- Pair X[i+N] with Y[i] — reverse interpretation, less intuitive for training context
- Rolling cross-correlation over all lags — too complex for MVP, can add later

## Decision 5: Strength Labels

**Decision**: Use standard thresholds: weak (|r| < 0.3), moderate (0.3 ≤ |r| < 0.7), strong (|r| ≥ 0.7).
**Rationale**: These are widely accepted in social science and sports science research. Cohen's conventions.
**Alternatives considered**:
- Domain-specific thresholds — no established training-specific standards exist
- No labels, just numbers — less accessible to non-technical users
