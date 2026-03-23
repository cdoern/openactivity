# Quickstart: Race Predictor & Readiness Score

## Prerequisites

- Activities synced: `openactivity strava sync`
- Personal records scanned: `openactivity strava records scan`
- At least 2 best efforts at different standard distances

## Predict a Race Time

```bash
# Predict 10K time from your best efforts
openactivity strava predict --distance 10K

# Predict half marathon
openactivity strava predict --distance half

# Predict marathon
openactivity strava predict --distance marathon

# Predict mile time
openactivity strava predict --distance 1mi
```

## Add a Race Date

```bash
# See prediction with race-date context
openactivity strava predict --distance marathon --race-date 2026-06-15

# Shows: days until race, training phase, taper timing
```

## JSON Output for Agents

```bash
# Structured output for agent consumption
openactivity --json strava predict --distance 10K
```

## Understanding the Output

### Predicted Time & Confidence Range
- Based on the Riegel formula using your recent best efforts
- Confidence range narrows with more reference efforts and recent data
- Shows which efforts were used so you know the basis

### Readiness Score (0-100)
- **Consistency** (30%): How regularly you've been training (weeks with 3+ activities)
- **Volume Trend** (25%): Are you maintaining or appropriately tapering volume?
- **Taper Status** (25%): Volume declining with intensity maintained = race ready
- **PR Recency** (20%): How recently you've demonstrated fitness at speed

### Score Labels
- **0-40**: Not Ready — inconsistent training or insufficient data
- **41-60**: Building — training is progressing but not race-ready
- **61-80**: Almost Ready — solid training, consider final preparations
- **81-100**: Race Ready — consistent training, good taper, recent PRs
