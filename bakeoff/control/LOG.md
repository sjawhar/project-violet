---
# THROWAWAY: bake-off lane Control log (docs/bakeoff/lane-log-format.md).
# Check it with: uv run --project tools/bakeoff bakeoff log-check bakeoff/control/LOG.md
lane: control
direction: control
engine: blender
machine: oryx
status: blocked
sessions:
  - {start: "2026-09-28T03:05:00Z", end: "2026-09-28T03:20:00Z", purpose: "record the lane's wait (plan Task 11 status, decision 0012): LOG.md, ci-tools and the plan's ci.sh; no lane work"}
costs: []
interventions: []
friction: []
blockers:
  - {what: "the full-3D protagonist needs Meshy's image-to-3D and auto-rig (plan Task 11 Step 1), and the bake-off buys no tools (decision 0012)", since: "2026-09-27T18:10:23Z", waiting_on: sjawhar}
  - {what: "no playable build and no completability test, by design: the lane is a rendered reel", since: "2026-09-27T18:10:23Z", waiting_on: "nobody (structural, not a failure)"}
deliverables: {build: null, capture: null, stills: [], tests: null}
---

THROWAWAY. Lane Control (Blender, full-3D protagonist) of the Phase 1 bake-off. Nothing here is canon.

The lane does not run. Its character would come from Meshy (image-to-3D from the approved concept, then auto-rig and motions), and decision 0012 (`docs/decisions/0012-no-purchases-until-agents-prove-it.md`) holds every purchase until the agents have shown what they can make without one. The plan's Task 11 steps stay as written in case that changes. Until then this log records the wait, so the judging page shows the lane as blocked rather than missing.

`game/control/ci.sh` is the plan's check (the reel's `render.json` and that `capture.mp4` decodes). With nothing rendered, CI's lane checks fail on the missing `render.json`, which is the true state; `log-check`, provenance and LFS pass.
