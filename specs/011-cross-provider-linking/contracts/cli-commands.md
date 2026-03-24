# CLI Command Contracts: Cross-Provider Activity Linking

## `openactivity activities link`

Scan all unlinked activities and create cross-provider links.

### Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--dry-run` | bool | false | Preview matches without creating links |
| `--unlink` | int | none | Remove the link for this activity ID |
| `--json` | bool | false | Output in JSON format |

### Human Output (default)

```
Scanning for cross-provider matches...

Found 150 potential matches:

  #1  Strava: Morning Run (2026-03-20 07:15)  ↔  Garmin: Run (2026-03-20 07:15)
      Confidence: 0.98  |  Duration: 45:12 vs 45:10

  #2  Strava: Afternoon Ride (2026-03-19 14:00)  ↔  Garmin: Cycling (2026-03-19 14:01)
      Confidence: 0.95  |  Duration: 1:30:00 vs 1:29:45

  ...

Summary:
  Scanned: 200 strava + 175 garmin activities
  Matches found: 150
  Links created: 150
  Already linked: 0
  Skipped (low confidence): 2
```

### Dry-Run Output

Same as above but with "Links created" replaced by "Would link" and no database changes.

### JSON Output

```json
{
  "scanned": {"strava": 200, "garmin": 175},
  "matches_found": 150,
  "links_created": 150,
  "already_linked": 0,
  "skipped": 2,
  "links": [
    {
      "strava_activity_id": 42,
      "garmin_activity_id": 318,
      "strava_name": "Morning Run",
      "garmin_name": "Run",
      "confidence": 0.98,
      "strava_date": "2026-03-20T07:15:00Z",
      "garmin_date": "2026-03-20T07:15:02Z"
    }
  ]
}
```

### Unlink Output

```
Removed link for activity #42 (Strava: Morning Run ↔ Garmin: Run)
```

### Error Cases

| Condition | Exit Code | Message |
|-----------|-----------|---------|
| No activities in DB | 1 | "No activities found. Run `strava sync` or `garmin import` first." |
| Only one provider | 0 | "Only [provider] activities found. Import from another provider to enable linking." |
| Unlink: no link found | 1 | "Activity #ID is not linked to another provider." |
| Unlink: activity not found | 1 | "Activity #ID not found." |

## Auto-Linking Output (appended to import/sync)

### After `garmin import`

```
...existing import output...

Cross-provider linking: 12 of 15 new activities matched to Strava
```

### After `strava sync`

```
...existing sync output...

Cross-provider linking: 5 of 8 new activities matched to Garmin
```
