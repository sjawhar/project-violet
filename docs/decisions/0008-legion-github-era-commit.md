# Run Legion from its pre-Dispatch commit

- **Date:** 2026-09-26
- **Status:** settled

## Decision

Legion orchestrates Violet's issue trees from its last GitHub-backed commit (32f4f7d0, 2026-09-09) plus the startup-deadlock fix. It runs as an isolated instance on oryx. The current Legion is not modified.

## Source

"Just checkout an older commit :)"

## Consequences

Restoring GitHub support in current Legion is out of scope. If the isolated instance fails its trial, Phase 2 runs with a lead session instead (tracked in issue #9).
