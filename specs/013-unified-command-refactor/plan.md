# Implementation Plan: Unified Command Refactoring

**Branch**: `013-unified-command-refactor` | **Date**: 2026-03-29 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/013-unified-command-refactor/spec.md`

## Summary

Promote Strava-specific `analyze`, `records`, `predict`, `segments`, and `segment` commands to provider-agnostic top-level commands. Add `--provider` filter to all promoted commands. Keep provider-specific commands (`auth`, `sync`, `athlete`, `import`) under their namespaces. Maintain backwards compatibility by making `strava <command>` an alias that implicitly filters to Strava.

## Technical Context

**Language/Version**: Python 3.12+ (existing)
**Primary Dependencies**: typer (CLI), rich (terminal output), sqlalchemy (ORM) — all existing
**Storage**: SQLite at `~/.local/share/openactivity/openactivity.db` — no schema changes
**Testing**: pytest (existing)
**Target Platform**: macOS, Linux, Windows
**Project Type**: CLI
**Performance Goals**: CLI startup under 500ms, local queries under 200ms
**Constraints**: No new dependencies. Backwards compatibility required for all existing `strava` command paths.
**Scale/Scope**: ~8 command files to refactor, ~15 individual commands to promote

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Quality | PASS | Refactoring only — no new logic, just command routing |
| II. Testing Standards | PASS | Will add tests for new top-level routes and --provider filtering |
| III. User Experience Consistency | PASS | Constitution says top-level commands MAY exist for cross-provider operations. Backwards compat maintained via aliases. |
| IV. Simplicity | PASS | No new abstractions — reuse existing command functions, just register them at a higher level |
| V. Maintainability | PASS | Deprecation cycle: strava commands become aliases, not removed. No circular dependencies. |
| VI. Performance Requirements | PASS | No performance impact — routing changes only |

**Constitution Note**: Principle III says "providers MAY expose different commands" and "top-level commands MAY exist for cross-provider operations." This refactoring promotes analysis/records/predict to top-level cross-provider commands while keeping provider-specific commands namespaced — fully aligned.

## Project Structure

### Documentation (this feature)

```text
specs/013-unified-command-refactor/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (minimal — no schema changes)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── cli-commands.md  # New command tree
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/openactivity/
├── main.py                      # MODIFY: register promoted commands at root
├── cli/
│   ├── root.py                  # EXISTING: global options
│   ├── analyze.py               # MODIFY: merge strava analyze commands here
│   ├── records.py               # NEW: top-level records (moved from strava/)
│   ├── predict.py               # NEW: top-level predict (moved from strava/)
│   ├── segments.py              # NEW: top-level segments (moved from strava/)
│   ├── config.py                # EXISTING: unchanged
│   ├── strava/
│   │   ├── app.py               # MODIFY: replace command groups with aliases
│   │   ├── auth.py              # EXISTING: unchanged
│   │   ├── sync.py              # EXISTING: unchanged
│   │   ├── athlete.py           # EXISTING: unchanged
│   │   ├── activities.py        # EXISTING: unchanged (already unified)
│   │   ├── analyze.py           # MODIFY: becomes thin alias to top-level
│   │   ├── records.py           # MODIFY: becomes thin alias to top-level
│   │   ├── predict.py           # MODIFY: becomes thin alias to top-level
│   │   ├── segments.py          # MODIFY: becomes thin alias to top-level
│   │   └── export.py            # EXISTING: unchanged
│   └── garmin/
│       ├── app.py               # EXISTING: unchanged
│       └── import_cmd.py        # EXISTING: unchanged

tests/
├── unit/
│   └── test_command_routing.py  # NEW: verify all routes resolve
└── integration/
    └── test_provider_filter.py  # NEW: verify --provider filtering
```

**Structure Decision**: Move command logic from `cli/strava/*.py` to `cli/*.py` at top level. The strava files become thin wrappers that import the top-level app and alias it with implicit `--provider strava` behavior. No new directories needed.

## Complexity Tracking

No violations — this is a straightforward command re-routing with no new abstractions.
