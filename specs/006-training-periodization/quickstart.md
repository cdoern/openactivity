# Quickstart: Training Block / Periodization Detector

## Prerequisites

- Activities synced: `openactivity strava sync`
- At least 4 weeks of activity data

## View Training Blocks

```bash
# Default: last 6 months of running
openactivity strava analyze blocks

# Last year
openactivity strava analyze blocks --last 1y

# All cycling activities
openactivity strava analyze blocks --type Ride --last all

# JSON output for agents
openactivity --json strava analyze blocks --last 6m
```

## Understanding the Output

### Phase Classifications
- **Base**: High volume, low intensity — building aerobic fitness
- **Build**: Rising volume and intensity — preparing for performance
- **Peak**: High intensity, tapering volume — race-ready sharpening
- **Recovery**: Low volume (<70% of recent average) — rest and adaptation

### Current Phase Indicator
- The most recent block is marked with ◀ in the table
- This answers: "What phase am I in right now?"

### Intensity Score (0-100)
- Based on heart rate when available (avg HR as % of max)
- Falls back to pace-based intensity when HR unavailable
- Higher number = more intense training
