# Quickstart: Recovery & Readiness Score

## What's New

A daily readiness score (0-100) combining Garmin health metrics with training load, available as `openactivity analyze readiness`.

## Usage

```bash
# Today's readiness
openactivity analyze readiness

# Last 30 days trend
openactivity analyze readiness --last 30d

# JSON for agents
openactivity --json analyze readiness

# Strava-only data
openactivity analyze readiness --provider strava
```

## How It Works

Four weighted components:

| Component | Weight | Source | What It Measures |
|-----------|--------|--------|-----------------|
| HRV | 30% | Garmin daily summary | Today's HRV vs 7-day baseline |
| Sleep | 20% | Garmin daily summary | Sleep quality score |
| Form | 30% | Training data (TSB) | Current fatigue vs fitness balance |
| Volume | 20% | Training data | 7-day load vs prior 7-day load |

## Recommendations

| Score | Label | Meaning |
|-------|-------|---------|
| 75-100 | Go Hard | Body is recovered — push intensity |
| 40-74 | Easy Day | Moderate recovery — keep it light |
| 0-39 | Rest | Take a rest day or very easy activity |

## Graceful Degradation

Missing Garmin data? The score still works — unavailable components redistribute their weight to available ones. Training-only scoring uses Form (60%) + Volume (40%).
