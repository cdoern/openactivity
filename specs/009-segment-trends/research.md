# Research: Segment Trend Analysis

## Decision 1: Linear Regression Library

**Decision**: Use `scipy.stats.linregress` for linear regression on effort times vs dates.
**Rationale**: scipy is already a dependency (added in 008-correlation-engine). `linregress` returns slope, intercept, R-squared, p-value, and standard error in a single call — everything needed for trend analysis.
**Alternatives considered**:
- numpy polyfit — returns coefficients but not R-squared or p-value
- Pure Python implementation — feasible but error-prone for proper statistical measures
- sklearn LinearRegression — heavyweight dependency for a single regression

## Decision 2: Date Encoding for Regression

**Decision**: Convert effort dates to "days since first effort" as the X variable for regression. Report rate of change converted to seconds/month (slope × 30.44).
**Rationale**: Linear regression needs numeric X values. Days-since-first is simple, interpretable, and avoids timezone/epoch complications. Converting to seconds/month matches the spec requirement and is intuitive for users.
**Alternatives considered**:
- Unix timestamps — large numbers that can cause floating-point issues
- Ordinal effort number (1, 2, 3...) — loses temporal information (gaps between efforts matter)

## Decision 3: Trend Classification Thresholds

**Decision**: Use ±1 second/month as the "stable" threshold (per spec assumption). Negative slope = improving (getting faster), positive slope = declining (getting slower).
**Rationale**: Spec explicitly defines stable as ±1 second/month. For running segments, elapsed time decreasing means improvement.
**Alternatives considered**:
- Percentage-based threshold — more complex, segment-length-dependent
- Statistical significance threshold — p-value approach could miss meaningful but noisy trends

## Decision 4: HR-Adjusted Normalization

**Decision**: Compute HR-adjusted metric as `elapsed_time / average_hr`. Run separate linear regression on these normalized values. Only include efforts that have HR data.
**Rationale**: Per spec FR-007, time/HR normalization means lower values = better performance at same effort level. This separates "faster because fitter" from "faster because tried harder."
**Alternatives considered**:
- Heart rate reserve (HRR) normalization — requires max HR which we don't reliably have
- Pace/HR ratio — equivalent to time/HR for fixed-distance segments
- TRIMP-adjusted — requires zone thresholds, too complex for this feature

## Decision 5: Effort Query Approach

**Decision**: Query `get_segment_efforts` with ascending date order (modify existing query or add new one) to get chronological effort list. Compute all analysis on the returned list.
**Rationale**: Existing `get_segment_efforts` returns efforts in descending order (most recent first). Trend analysis needs chronological order. Adding an `order` parameter keeps the query flexible.
**Alternatives considered**:
- Reverse the list in Python — works but wasteful if query can sort
- New dedicated query function — unnecessary duplication
