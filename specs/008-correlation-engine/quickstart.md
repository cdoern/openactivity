# Quickstart: Cross-Activity Correlation Engine

## Prerequisites

- Activities synced: `openactivity strava sync`
- At least 4 weeks of activity data (12+ weeks recommended)

## Basic Correlation

```bash
# Does more weekly distance lead to faster pace?
openactivity strava analyze correlate --x weekly_distance --y avg_pace

# Does higher HR correlate with more elevation?
openactivity strava analyze correlate --x weekly_elevation --y avg_hr

# More rest days → faster pace?
openactivity strava analyze correlate --x rest_days --y avg_pace
```

## Lag Analysis

```bash
# Does this week's distance predict pace 4 weeks later?
openactivity strava analyze correlate --x weekly_distance --y avg_pace --lag 4

# Does volume this week predict HR next week?
openactivity strava analyze correlate --x weekly_distance --y avg_hr --lag 1
```

## Time Window and Type

```bash
# Last 6 months only
openactivity strava analyze correlate --x activity_count --y avg_pace --last 6m

# All time data
openactivity strava analyze correlate --x weekly_distance --y avg_pace --last all

# Cycling activities
openactivity strava analyze correlate --x weekly_distance --y avg_hr --type Ride
```

## JSON for Agents

```bash
openactivity --json strava analyze correlate --x weekly_distance --y avg_pace
```

## Supported Metrics

| Metric | Description |
|--------|-------------|
| weekly_distance | Total distance in the week |
| weekly_duration | Total moving time |
| weekly_elevation | Total elevation gain |
| avg_pace | Distance-weighted average pace |
| avg_hr | Average heart rate (requires HR data) |
| max_hr | Maximum heart rate (requires HR data) |
| activity_count | Number of activities |
| rest_days | Days without any activity (0-7) |
| longest_run | Longest single activity distance |

## Understanding Results

- **Pearson r**: Measures linear correlation (-1 to 1)
- **Spearman ρ**: Measures monotonic correlation (handles non-linear)
- **p-value**: < 0.05 means statistically significant
- **Strength**: weak (|r| < 0.3), moderate (0.3-0.7), strong (> 0.7)
- **Negative r**: As X increases, Y decreases (e.g., more distance → faster pace is negative because pace in s/km decreases)
