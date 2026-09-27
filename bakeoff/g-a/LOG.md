---
# THROWAWAY: bake-off lane G-A log (docs/bakeoff/lane-log-format.md).
# Check it with: uv run --project tools/bakeoff bakeoff log-check bakeoff/g-a/LOG.md
lane: g-a
direction: A
engine: godot
machine: oryx
status: in-progress
sessions:
  - {start: "2026-09-27T08:23:12Z", end: "2026-09-27T08:37:00Z", purpose: "greybox milestone: workspace, project skeleton, scripts, replay, ci.sh (plan Task 7 Steps 1-17)"}
costs: []
interventions: []
friction:
  - {at: "2026-09-27T08:26:30Z", what: "plan's export_presets.cfg omits include_filter and exclude_filter; every godot --import printed 'Couldn't find the given section preset.0 and key include_filter' errors", workaround: "added include_filter=\"\" and exclude_filter=\"\" to the preset"}
  - {at: "2026-09-27T08:28:00Z", what: "plan's skeleton replay fell into the pit: the jump at tick 199 came after the player had walked off the edge at col 18", workaround: "retuned every input with --trace (per-tick positions from a throwaway copy of the runner)"}
  - {at: "2026-09-27T08:29:00Z", what: "plan's passable assert (named kind passable, every other tagged body solid) cannot hold with red active: mechanic.md makes platform_red passable too, so [33,12] and [58,7] failed with 'platform_red_53_8 passable should be false'", workaround: "runner treats the named kind as naming a color: bodies of that color passable, every other color solid"}
  - {at: "2026-09-27T08:32:00Z", what: "oryx's NVIDIA GPU is off limits (wedged driver), so looking at rendered frames needs software GL", workaround: "one look at frames with llvmpipe under xvfb-run and mesa-only GLX/EGL vendor overrides, about 45% of real time; captures stay with the lead on machine sami"}
blockers: []
deliverables: {build: bakeoff/g-a/reports/build.txt, capture: null, stills: [], tests: bakeoff/g-a/reports/replay.json}
---

THROWAWAY. Lane G-A (Godot 4.7.2 2D, painted world) of the Phase 1 bake-off. Nothing here is canon.

Greybox milestone (plan Task 7 Steps 1-17): greybox visuals and the STAND-IN capsule character; painted art (Step 18), the Spine rig (Step 19) and captures (Step 20) come later.

The replay puts the four moments the capture stills look for on capture-lib's still times: red orb at about 5 s (tick 287), the air-dash over the pit at 20 s (ticks 1194-1206), the green orb at 40 s (tick 2394), the mid-air switch at col 57 at 60 s (tick 3593). The goal is reached at tick 3757; capture mode runs to tick 3960 (66 s). Between them the player idles or walks back and forth through the wall of the active color.

A hazard touch is reported twice when the player's box overlaps two hazard cells; the run fails either way.
