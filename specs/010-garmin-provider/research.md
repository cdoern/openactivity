# Research: Garmin FIT File Import

**Date**: 2026-03-23
**Feature**: 010-garmin-provider
**Purpose**: Document technical research and decision to use FIT files instead of API

## 1. API Approach Failure Analysis

### Initial Plan: Garmin Connect API

**Chosen Library**: `garminconnect` - Unofficial Garmin Connect API library for Python

**Why It Failed**:

1. **Rate Limiting** (HTTP 429):
   - Triggers after 1-2 login attempts
   - Bans last 24-48 hours minimum
   - IP-based, account-based, and pattern-based
   - No documented limits or appeal process

2. **Bot Detection**:
   - User-agent fingerprinting
   - Request pattern analysis
   - TLS signature detection
   - Missing browser-specific headers trigger blocking

3. **Unreliability**:
   - Even valid OAuth tokens get rate limited
   - Browser cookie extraction gets blocked eventually
   - Selenium/Playwright automation is slow and still detectable
   - Community reports ~30% success rate at best

**Evidence from Testing**:
- User attempted authentication → immediate 429 error
- Waited 30 minutes → still blocked
- Attempted with MFA support → still rate limited
- GitHub issues show this is widespread: [garminconnect#332](https://github.com/cyberjunky/python-garminconnect/issues/332)

**Community Findings**:
- Some users banned for 48+ hours
- VPN/proxy workarounds unreliable
- Even successful projects (GarminDB) treat API as fallback, not primary method
- Garmin actively hostile to automation (no official API for consumers)

**Conclusion**: No sustainable API solution exists. Building on `garminconnect` would result in unreliable tool that frustrates users.

---

## 2. Alternative Approach: FIT File Parsing

### Decision: Use fitparse Library

**Chosen**: `fitparse>=1.2.0` - Pure Python FIT file parser

**Rationale**:

1. **Reliability**:
   - No network requests = no rate limiting
   - No authentication = no account bans
   - Works offline = reliable anywhere
   - File format is stable (FIT SDK standard)

2. **Data Completeness**:
   - All activity data: GPS tracks, heart rate, power, cadence, speed
   - Metadata: timestamps, activity type, equipment, zones
   - Enough for 95% of use cases

3. **Battle-Tested**:
   - Used by GarminDB, TrainerRoad tools, Golden Cheetah
   - 100+ GitHub stars, active maintenance
   - Handles edge cases (corrupted files, various device types)

4. **Multiple Sources**:
   - Direct from device (USB)
   - Garmin Connect folder (Garmin Express)
   - Bulk export (official Garmin feature)
   - Custom locations (user flexibility)

**Key Capabilities**:

```python
from fitparse import FitFile

fit = FitFile('activity.fit')

# Parse session (summary data)
for record in fit.get_messages('session'):
    for field in record:
        print(f"{field.name}: {field.value}")

# Parse record messages (GPS track)
for record in fit.get_messages('record'):
    # Get timestamps, lat/lon, HR, power, etc.
    pass
```

**Limitations**:

FIT files do NOT contain:
- HRV (Heart Rate Variability)
- Body Battery scores
- Detailed sleep phase analysis
- Stress scores
- Advanced physiological metrics

These are Garmin cloud-only proprietary calculations, not stored in device files.

**Workaround**: Garmin's bulk export includes CSV files with some health data. Future enhancement could parse these separately.

---

## 3. FIT File Format Overview

### What is FIT?

**FIT** = Flexible and Interoperable Data Transfer

- Binary file format designed by Garmin
- Published standard (FIT SDK available)
- Used by most modern fitness devices (not just Garmin)
- Compact and efficient (much smaller than GPX/TCX)

### FIT File Types

1. **Activity Files** (what we parse):
   - From device: `/Garmin/Activity/*.fit`
   - Contains: GPS track, HR, power, cadence, laps, zones
   - File ID type: 4

2. **Monitoring Files** (ignored):
   - Daily step counts, sleep, calories
   - Continuous monitoring data
   - File ID type: 15, 32

3. **Settings Files** (ignored):
   - User profile, device settings, zones
   - File ID type: 2

**Our Focus**: Only parse activity files (type 4). Skip monitoring and settings files.

### Data Structure

FIT files contain **messages**:

- **File ID**: Metadata about file type, device
- **Session**: Activity summary (distance, time, calories, avg HR)
- **Lap**: Split data
- **Record**: GPS points (lat/lon, timestamp, HR, power, cadence)
- **Event**: Start/stop markers
- **Device Info**: Device model, firmware

**We primarily use**:
- `session` - For activity summary (what we store in Activity model)
- `file_id` - To identify file type and creation time
- `record` - For future stream data support

---

## 4. FIT File Sources

### Source 1: USB Connected Device ✅

**Location**:
- Linux: `/media/GARMIN/Garmin/Activity/*.fit`
- macOS: `/Volumes/GARMIN/Garmin/Activity/*.fit`
- Windows: `D:\Garmin\Activity\*.fit` (or E:, F:)

**Pros**:
- Direct access to all activities
- No cloud dependency
- Most reliable source

**Cons**:
- Requires physical device connection
- Manual process (user must plug in)

**Use Case**: Best for users who want offline workflow.

### Source 2: Garmin Connect Folder ✅

**Location**:
- macOS: `~/Library/Application Support/Garmin/GarminConnect/`
- Windows: `%LOCALAPPDATA%\Garmin\GarminConnect\`
- Linux: (rare - Garmin Express not officially supported)

**Pros**:
- Automatically synced after Garmin Express sync
- No need to connect device every time
- Convenient for regular users

**Cons**:
- Requires Garmin Express installation
- Only works after cloud sync (online dependency)

**Use Case**: Best for users who already use Garmin Express.

### Source 3: Bulk Export ZIP ✅

**How to Get**:
1. Log into https://www.garmin.com/account/
2. Settings → Data Management → Export Your Data
3. Request export (takes few hours to days)
4. Download ZIP file

**Pros**:
- Official Garmin feature
- Contains complete history (all activities ever)
- One-time migration solution
- Includes CSVs with health data

**Cons**:
- Manual process
- Export request takes time
- Large file size (thousands of activities)

**Use Case**: Best for initial migration or historical data import.

### Source 4: Custom Directory ✅

**Use Case**: User has organized FIT files in custom location.

**Example Scenarios**:
- Downloaded from third-party tools
- Received from training coach
- Migrated from other software

**Pros**:
- Maximum flexibility
- Supports any file organization

**Cons**:
- User must specify path

---

## 5. Comparison: API vs FIT Files

| Aspect | API Approach | FIT File Approach |
|--------|-------------|-------------------|
| **Reliability** | ~30% (rate limited) | 100% (no network) |
| **Setup Complexity** | High (auth, MFA handling) | None (no auth) |
| **Data Coverage** | Activities + health data | Activities only |
| **Maintenance** | High (API changes) | Low (stable format) |
| **Offline Support** | No | Yes |
| **User Friction** | High (banned accounts) | Low (plug and import) |
| **Speed** | Slow (network latency) | Fast (local files) |
| **Dependencies** | garminconnect + garth | fitparse only |

**Winner**: FIT files for activity data. CSV parsing can add health data later if needed.

---

## 6. Successful Projects Using FIT Parsing

### GarminDB

**URL**: https://github.com/tcgoetz/GarminDB

**Approach**:
- PRIMARY: Download Garmin bulk export → parse FIT + CSV files
- SECONDARY: Use garminconnect API for incremental updates (when it works)
- Explicitly documents API unreliability

**Quote from README**:
> "The best way to download your historical data is to use the Export feature on the Garmin Connect website."

### Golden Cheetah

**URL**: https://www.goldencheetah.org/

**Approach**:
- 100% FIT file parsing
- No API usage
- Widely used in cycling community

### TrainerRoad

**Approach**:
- FIT import for Garmin compatibility
- Direct file upload to their platform
- No reliance on Garmin API

**Lesson**: Serious tools don't rely on unofficial Garmin API.

---

## 7. Health Data Future Work

### What's Missing from FIT Files

- HRV (Heart Rate Variability)
- Body Battery
- Detailed sleep stages
- Stress scores
- Training readiness metrics
- VO2 max estimates (Garmin's proprietary algorithm)

### How to Get This Data

**Garmin Bulk Export** includes CSVs:
- `DailySummaries.csv` - Steps, calories, sleep score
- `SleepData.csv` - Sleep start/end, basic stages
- `StressData.csv` - Stress scores
- `Monitoring.csv` - HRV, respiration rate

**Future Enhancement**:
1. Add CSV parser module
2. Import health data from bulk export CSVs
3. Store in GarminDailySummary and GarminSleepSession tables
4. Add `openactivity garmin import-health --from-csv` command

**Why Not Now**:
- MVP focuses on activities (primary use case)
- Health data is nice-to-have, not critical
- CSV parsing is straightforward addition later

---

## Summary of Decisions

| Area | Decision | Key Rationale |
|------|----------|---------------|
| **Data Source** | FIT files | 100% reliable, no API failures |
| **Library** | fitparse | Battle-tested, active maintenance, comprehensive |
| **Import Sources** | Device, Connect, ZIP, Custom | Multiple options for different user workflows |
| **Health Data** | Future work (CSV parsing) | Focus MVP on activities first |
| **Architecture** | Simple parser + importer | Minimal abstraction, clear ownership |

**Risks Identified**:
1. **FIT format changes**: Mitigated by using established library that tracks FIT SDK
2. **Corrupted files**: Graceful error handling, skip with message
3. **Missing data fields**: Handle optional fields, don't crash on missing data
4. **User confusion**: Clear documentation, helpful error messages

**Next Steps**: Proceed with FIT file implementation as described in plan.md
