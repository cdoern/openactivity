# Quickstart: Fitness/Fatigue Model (ATL/CTL/TSB)

## What This Feature Does

Computes Training Stress Score (TSS) per activity from heart rate data, then derives daily Fitness (CTL), Fatigue (ATL), and Form (TSB) values using the classic Banister impulse-response model. Classifies your training state as peaking, maintaining, overreaching, or detraining.

## Quick Test

```bash
# 1. View current fitness/fatigue/form
openactivity strava analyze fitness

# 2. View last year of data
openactivity strava analyze fitness --last 1y

# 3. Filter to running only
openactivity strava analyze fitness --type Run

# 4. Generate a chart
openactivity strava analyze fitness --last 6m --chart

# 5. JSON output for programmatic use
openactivity strava analyze fitness --json

# 6. Check TSS on a specific activity
openactivity activity <ID>
# TSS value appears in the detail output
```

## Key Files

| File | Purpose |
|------|---------|
| `src/openactivity/analysis/fitness.py` | Core TSS, ATL, CTL, TSB computation |
| `src/openactivity/cli/strava/analyze.py` | `fitness` CLI command |
| `src/openactivity/cli/strava/activities.py` | TSS in activity detail view |
