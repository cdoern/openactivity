# Tasks: Cross-Provider Activity Linking

**Input**: Design documents from `/specs/011-cross-provider-linking/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested — test tasks omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No new project setup needed — this feature modifies existing files only.

- [x] T001 Verify `activity_links` table exists in local database and matches ActivityLink model in src/openactivity/db/models.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Fix the type matching logic that all user stories depend on.

**CRITICAL**: Type normalization must work before any linking can succeed.

- [x] T002 Fix `_types_match()` in src/openactivity/db/queries.py to strip Strava's `root='...'` wrapper format before comparison (e.g., `root='Run'` → `Run`, `root='AlpineSki'` → `AlpineSki`)
- [x] T003 Extend type alias groups in `_types_match()` in src/openactivity/db/queries.py to include `alpineski`/`alpine_skiing` mapping and any other Strava↔Garmin type mismatches found in the database

**Checkpoint**: `_types_match("root='Run'", "Run")` returns True, `_types_match("root='AlpineSki'", "Alpine_skiing")` returns True

---

## Phase 3: User Story 1 — Bulk Link Existing Activities (Priority: P1) MVP

**Goal**: User runs `openactivity activities link` to scan all unlinked activities and create cross-provider links with summary stats.

**Independent Test**: Run `openactivity activities link` with activities from both providers in the DB. Verify links are created and `activities list` shows `[Strava+Garmin]` badges.

### Implementation for User Story 1

- [x] T004 [US1] Add `bulk_link_activities()` function in src/openactivity/db/queries.py that iterates all unlinked activities from one provider, calls `detect_duplicate_activities()` for each, selects the highest-confidence match, calls `link_activities()`, and returns stats dict `{scanned, matched, linked, already_linked, skipped}`
- [x] T005 [US1] Add `link_command()` to the activities typer app in src/openactivity/cli/strava/activities.py with options `--dry-run` (bool), `--unlink` (int, optional), `--json` (bool). When invoked without flags, calls `bulk_link_activities()` and displays results per contracts/cli-commands.md
- [x] T006 [US1] Implement rich terminal output for the link command in src/openactivity/cli/strava/activities.py: show each match with activity names, dates, confidence scores, and a summary table with scanned/matched/linked/skipped counts
- [x] T007 [US1] Implement `--json` output for the link command in src/openactivity/cli/strava/activities.py returning the JSON structure defined in contracts/cli-commands.md

**Checkpoint**: `openactivity activities link` creates links, `openactivity activities list` shows `[Strava+Garmin]` badges for linked activities.

---

## Phase 4: User Story 2 — Preview Matches Before Linking (Priority: P1)

**Goal**: User runs `openactivity activities link --dry-run` to see proposed matches without creating any links.

**Independent Test**: Run `--dry-run`, verify output shows matches with confidence scores, verify no ActivityLink records created.

### Implementation for User Story 2

- [x] T008 [US2] Add `dry_run` parameter to `bulk_link_activities()` in src/openactivity/db/queries.py — when True, collect matches but skip `link_activities()` calls and don't commit
- [x] T009 [US2] Wire `--dry-run` flag in the link command in src/openactivity/cli/strava/activities.py to pass `dry_run=True` to `bulk_link_activities()` and display "Would link" instead of "Links created" in output

**Checkpoint**: `openactivity activities link --dry-run` shows matches but creates zero database records.

---

## Phase 5: User Story 3 — Auto-Link During Import and Sync (Priority: P2)

**Goal**: New activities are automatically linked against the other provider's existing activities during garmin import and strava sync.

**Independent Test**: Import a Garmin FIT file that matches an existing Strava activity. Verify the link is created automatically and import output shows linking stats.

### Implementation for User Story 3

- [x] T010 [P] [US3] Add `auto_link_new_activities()` function in src/openactivity/db/queries.py that takes a session and list of newly added Activity objects, calls `detect_duplicate_activities()` for each, links the best match, and returns stats dict `{checked, linked}`
- [x] T011 [US3] Call `auto_link_new_activities()` at the end of `import_from_directory()` in src/openactivity/providers/garmin/importer.py after `session.commit()`, passing the list of newly created activities. Add linking stats to ImportResult.
- [x] T012 [US3] Call `auto_link_new_activities()` at the end of `sync_activities()` in src/openactivity/providers/strava/sync.py after the commit, passing newly synced activities. Add linking stats to the return dict.
- [x] T013 [P] [US3] Display auto-linking stats in garmin import CLI output in src/openactivity/cli/garmin/import_cmd.py: "Cross-provider linking: X of Y new activities matched to Strava"
- [x] T014 [P] [US3] Display auto-linking stats in strava sync CLI output in src/openactivity/cli/strava/sync.py: "Cross-provider linking: X of Y new activities matched to Garmin"

**Checkpoint**: `openactivity garmin import` and `openactivity strava sync` both auto-link and report stats.

---

## Phase 6: User Story 4 — Remove Incorrect Links (Priority: P3)

**Goal**: User can remove a bad link with `openactivity activities link --unlink <ID>`.

**Independent Test**: Create a link, run `--unlink` with the activity ID, verify the link is removed and both activities appear separately.

### Implementation for User Story 4

- [x] T015 [US4] Add `unlink_activity()` function in src/openactivity/db/queries.py that finds and deletes the ActivityLink where strava_activity_id or garmin_activity_id matches the given ID. Return the deleted link or None.
- [x] T016 [US4] Wire `--unlink` flag in the link command in src/openactivity/cli/strava/activities.py to call `unlink_activity()`, display confirmation message with both activity names, or error if no link found

**Checkpoint**: `openactivity activities link --unlink <ID>` removes the link, activity appears as single-provider in list.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, edge cases, and validation.

- [x] T017 Add error handling in the link command in src/openactivity/cli/strava/activities.py for: no activities in DB, only one provider present, unlink target not found
- [x] T018 Handle ambiguous matches (multiple candidates above 0.7) in `bulk_link_activities()` in src/openactivity/db/queries.py: select highest confidence, log warning about ambiguity
- [x] T019 Run `openactivity activities link` against real database to validate end-to-end and verify `openactivity activities list` shows correct badges

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — verification only
- **Phase 2 (Foundational)**: No dependencies — fix type matching
- **Phase 3 (US1 Bulk Link)**: Depends on Phase 2 (type matching must work)
- **Phase 4 (US2 Dry Run)**: Depends on Phase 3 (bulk link function must exist)
- **Phase 5 (US3 Auto-Link)**: Depends on Phase 2 only (independent of US1 CLI)
- **Phase 6 (US4 Unlink)**: Depends on Phase 3 (link command must exist)
- **Phase 7 (Polish)**: Depends on all user stories

### User Story Dependencies

- **US1 (Bulk Link)**: Can start after Phase 2 — no other story dependencies
- **US2 (Dry Run)**: Depends on US1 (extends the same function and command)
- **US3 (Auto-Link)**: Can start after Phase 2 — independent of US1/US2 (different files)
- **US4 (Unlink)**: Depends on US1 (extends the link command)

### Parallel Opportunities

- T002 and T003 can run in parallel (different parts of same function, but same file — run sequentially)
- T010, T013, T014 are marked [P] — T010 in queries.py, T013 in import_cmd.py, T014 in sync.py
- US1 and US3 can be worked in parallel after Phase 2 (different files)

---

## Parallel Example: User Story 3

```bash
# After T010 completes, these can run in parallel:
Task T011: "Auto-link in garmin importer.py"
Task T012: "Auto-link in strava sync.py"

# These CLI display tasks can run in parallel:
Task T013: "Display linking stats in garmin import CLI"
Task T014: "Display linking stats in strava sync CLI"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Verify setup
2. Complete Phase 2: Fix type matching
3. Complete Phase 3: Bulk link command
4. **STOP and VALIDATE**: Run `openactivity activities link` on real data
5. User can now deduplicate their 375 activities

### Incremental Delivery

1. Phase 2 → Type matching works → Foundation ready
2. Phase 3 (US1) → Bulk linking → **MVP!** Users can deduplicate
3. Phase 4 (US2) → Dry-run preview → Safety net for cautious users
4. Phase 5 (US3) → Auto-linking → Seamless ongoing experience
5. Phase 6 (US4) → Unlink → Error correction
6. Phase 7 → Polish → Production-ready

---

## Notes

- No new dependencies required
- No schema migration needed — `activity_links` table already exists
- 4 existing files modified, 0 new source files created
- The `detect_duplicate_activities()` and `link_activities()` functions in queries.py are already complete — this feature wires them into the CLI and provider layers
