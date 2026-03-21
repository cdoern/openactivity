<!--
  Sync Impact Report
  ====================
  Version change: 1.0.0 → 1.1.0
  Modified principles:
    - Principle III: User Experience Consistency — rewritten from
      verb-noun to provider-first CLI hierarchy
    - Principle IV: Simplicity — relaxed shared interface requirement
      to account for provider-specific command trees
  Modified sections:
    - API Provider Integration Standards — updated to reflect
      provider-first architecture with per-provider command trees
  Added sections:
    - Principle I: Code Quality
    - Principle II: Testing Standards
    - Principle III: User Experience Consistency
    - Principle IV: Simplicity
    - Principle V: Maintainability
    - Principle VI: Performance Requirements
    - Section: API Provider Integration Standards
    - Section: Development Workflow
    - Governance
  Removed sections: None
  Templates requiring updates:
    ✅ plan-template.md — no changes needed, Constitution Check
       is dynamically filled from this file
    ✅ spec-template.md — no changes needed, structure aligns
    ✅ tasks-template.md — no changes needed, phase structure aligns
  Follow-up TODOs: None
-->

# OpenActivity Constitution

## Core Principles

### I. Code Quality

- All code MUST pass linting and formatting checks before merge.
- Functions and methods MUST have a single, clear responsibility.
- Public APIs (CLI commands, exported functions) MUST include
  type annotations or signatures appropriate to the language.
- Error messages MUST be actionable: state what went wrong,
  why, and what the user can do about it.
- All API provider interactions MUST use structured error
  handling — never silently swallow failures.

### II. Testing Standards

- Every new feature MUST include unit tests covering the
  primary success path and at least one failure path.
- Integration tests MUST exist for each API provider adapter
  (Strava, Garmin, etc.) validating authentication flow,
  data retrieval, and error responses.
- Tests MUST be deterministic and MUST NOT depend on live
  external API calls; use recorded responses or fixtures.
- Test coverage MUST NOT decrease on any PR. New code SHOULD
  target >= 80% line coverage.
- Contract tests MUST validate that provider adapter interfaces
  conform to the shared activity data model.

### III. User Experience Consistency

- The CLI MUST follow a provider-first hierarchy where each
  provider defines its own command tree based on its capabilities
  (e.g., `openactivity strava activities list`,
  `openactivity garmin hrv`, `openactivity strava routes list`).
- Providers MAY expose different commands — Strava and Garmin
  are fundamentally different services and MUST NOT be forced
  into a single uniform command set.
- Top-level commands (e.g., `openactivity providers list`,
  `openactivity activities list`) MAY exist for cross-provider
  operations that aggregate or query normalized local data.
- Each provider's `--help` MUST clearly list all available
  subcommands so users and agents can discover provider-specific
  capabilities via `openactivity <provider> --help`.
- Output MUST default to human-readable format and MUST support
  `--json` for machine-readable output on every command.
- Errors MUST be written to stderr; data MUST be written to stdout.
- Progress indicators MUST be displayed for operations that may
  take longer than 2 seconds (e.g., API syncs).
- Help text (`--help`) MUST be present on every command and
  subcommand with usage examples.

### IV. Simplicity

- Start with the simplest implementation that satisfies the
  requirement. Do not build abstractions until a pattern repeats
  at least twice (YAGNI).
- Each provider adapter MUST implement a minimal shared interface
  (auth, sync, list activities). Provider-specific features
  (routes, HRV, social features) live in the provider module
  and MUST NOT leak into core application code.
- Configuration MUST use a single file format and location.
  Avoid multiple config mechanisms for the same purpose.
- Dependencies MUST be justified. Every third-party library
  addition MUST solve a problem that cannot be reasonably
  handled with existing dependencies or standard library.

### V. Maintainability

- Provider adapters MUST be isolated behind a common interface
  so that adding a new provider requires no changes to core code.
- Breaking changes to the CLI interface MUST follow a deprecation
  cycle: warn for one minor release, remove in the next major.
- All modules MUST have clear ownership boundaries. Circular
  dependencies between packages/modules are prohibited.
- Commit messages MUST follow Conventional Commits format
  (e.g., `feat:`, `fix:`, `docs:`, `refactor:`).

### VI. Performance Requirements

- CLI startup time MUST remain under 500ms with no network calls
  on non-sync commands.
- API sync operations MUST support pagination and incremental
  sync (only fetch new/updated activities since last sync).
- Local data queries (list, filter, search) MUST complete in
  under 200ms for datasets of up to 10,000 activities.
- Memory usage MUST remain under 256MB during normal operation
  including large sync batches.

## API Provider Integration Standards

- Each provider (Strava, Garmin, etc.) MUST be implemented as
  an isolated module that owns its own command tree, API client,
  and data types.
- All providers MUST implement a minimal shared interface
  covering: authentication, sync, and listing activities.
  Beyond that, providers define their own commands freely
  (e.g., Strava: routes, comments, kudos; Garmin: HRV, sleep,
  body composition).
- Provider-specific data MUST be stored alongside the shared
  activity model, not crammed into it. The shared model covers
  normalized activity data; provider-specific fields stay in
  provider-scoped storage.
- Authentication credentials MUST be stored securely (OS keychain
  or encrypted config) and MUST NOT appear in logs or error output.
- Rate limiting MUST be handled gracefully with automatic backoff
  and clear user messaging when limits are hit.
- Adding a new provider MUST require only: implementing the
  shared provider interface, defining provider-specific commands,
  adding configuration schema, and registering the adapter —
  no modifications to existing providers or core logic.

## Development Workflow

- All changes MUST go through pull request review before merging
  to the main branch.
- PRs MUST include a description of what changed and why.
- CI MUST run linting, formatting, and the full test suite on
  every PR. All checks MUST pass before merge.
- Release versions MUST follow Semantic Versioning (MAJOR.MINOR.PATCH).
- Documentation (help text, README) MUST be updated in the same
  PR as the feature or change it describes.

## Governance

- This constitution supersedes all other development practices
  for the OpenActivity project.
- Amendments require: (1) a PR with the proposed change,
  (2) description of rationale, and (3) update to the version
  number following semver rules (MAJOR for principle removals
  or redefinitions, MINOR for additions, PATCH for clarifications).
- All PRs and code reviews MUST verify compliance with these
  principles. Non-compliance MUST be flagged and resolved before
  merge.
- Complexity beyond what these principles allow MUST be justified
  in writing (PR description or ADR) with rationale for why the
  simpler alternative is insufficient.

**Version**: 1.1.0 | **Ratified**: 2026-03-13 | **Last Amended**: 2026-03-13
