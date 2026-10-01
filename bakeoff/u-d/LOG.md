---
# THROWAWAY: bake-off lane U-D log (docs/bakeoff/lane-log-format.md).
# Check it with: uv run --project tools/bakeoff bakeoff log-check bakeoff/u-d/LOG.md
lane: u-d
direction: D
engine: unity
machine: sami
status: blocked
sessions:
  - {start: "2026-10-01T05:00:00Z", end: "2026-10-01T05:10:00Z", purpose: "record the lane's wait so the judging page shows it as blocked rather than missing: LOG.md, ci-tools, ci.sh; no lane work"}
costs: []
interventions: []
friction: []
blockers:
  - {what: "Unity 6.3 needs Sami to sign in to Unity Hub once on machine sami before any agent can open the editor (plan Task 9; #4 checklist item 1)", since: "2026-09-27T18:10:23Z", waiting_on: sjawhar}
deliverables: {build: null, capture: null, stills: [], tests: null}
---

THROWAWAY. Lane U-D (Unity 6.3 URP, official MCP only) of the Phase 1 bake-off. Nothing here is canon.

The lane has not started. Unity requires a one-time sign-in by Sami in Unity Hub, and the #4 checklist's default is that U-D waits until the Godot lanes have shown results. Agents work in Unity only through Unity's official MCP (Unity Terms of Service section 17.2), so there is no workaround through a third-party bridge. This log records the wait, so the judging page shows the lane as blocked rather than missing.

`game/u-d/ci.sh` fails on purpose with that reason: there is no Unity project to build or test yet, which is the true state.
