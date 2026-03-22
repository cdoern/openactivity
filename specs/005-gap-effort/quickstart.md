# Quickstart: Grade-Adjusted Pace & Effort Scoring

## Prerequisites

- Activities synced: `openactivity strava sync`
- Activities with elevation stream data (GPS-recorded outdoor runs)

## View GAP for a Single Activity

```bash
# View activity detail — now includes GAP alongside actual pace
openactivity strava activity 12345678

# Output includes:
#   Pace: 8:15 /mi
#   GAP:  7:30 /mi   (grade-adjusted)
#
#   Laps table now shows GAP column
```

## Trend GAP and Effort Over Time

```bash
# Default: last 90 days of running
openactivity strava analyze effort

# Last 6 months
openactivity strava analyze effort --last 6m

# All cycling activities
openactivity strava analyze effort --type Ride --last 1y

# JSON output for agents
openactivity --json strava analyze effort --last 30d
```

## Understanding the Output

### Grade-Adjusted Pace (GAP)
- **What**: Your equivalent pace if you ran the same effort on a flat course
- **Uphill**: GAP will be faster than actual pace (you were working harder than your pace shows)
- **Downhill**: GAP will be slower than actual pace (gravity was helping)
- **Flat**: GAP approximately equals actual pace

### Effort Score (0-100)
- **0-20**: Easy/recovery effort
- **20-50**: Moderate effort
- **50-75**: Hard effort
- **75-100**: Very hard / race effort
- Accounts for duration, GAP, heart rate, and elevation

### Trend Direction
- **Improving**: Your GAP is getting faster over time
- **Declining**: Your GAP is getting slower over time
- **Stable**: No significant change
