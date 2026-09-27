# Lane log format (THROWAWAY bake-off evidence)

Part of the Phase 1 bake-off shared inputs; see [README.md](README.md). Every lane keeps `bakeoff/<lane>/LOG.md`, front matter followed by free-form notes: copy [lane-log-template.md](lane-log-template.md) and check it with `uv run --project tools/bakeoff bakeoff log-check bakeoff/<lane>/LOG.md` (CI runs the same check on every push).

## Front matter

```yaml
---
lane: g-a
direction: A          # A | C | D | control
engine: godot         # godot | unity | blender
machine: oryx
status: in-progress   # in-progress | delivered | blocked
sessions:
  - {start: "2026-09-28T14:00:00Z", end: "2026-09-28T16:30:00Z", purpose: "greybox scene, ci.sh"}
costs:
  - {item: "gen image, 4 body parts", usd: 0.32, evidence: "bakeoff/g-a/reports/gen-cost.txt"}
interventions:
  - {at: "2026-09-28T15:10:00Z", who: sami, what: "approved Godot export preset", minutes: 5}
friction:
  - {at: "2026-09-28T15:40:00Z", what: "spine-godot GDExtension version mismatch", workaround: "pinned to 4.3"}
blockers:
  - {what: "Meshy kit not ready", since: "2026-09-28T16:00:00Z", waiting_on: "Task 6"}
deliverables:
  build: bakeoff/g-a/reports/build.txt
  capture: bakeoff/g-a/capture/capture.mp4
  stills: ["bakeoff/g-a/capture/still-01.png"]
  tests: bakeoff/g-a/reports/replay.json
---
```

## Field notes

- `lane`, `direction`, `engine`, `machine`, `status` are single scalars; `status` is one of `in-progress`, `delivered`, `blocked`; `machine` is `oryx` or `sami`.
- `lane` is the lane's directory name, and each of the five lanes has a fixed direction and engine that `log-check` enforces: `g-a` A/godot, `g-d` D/godot, `u-d` D/unity, `g-c` C/godot, `control` control/blender.
- `sessions`: each entry is `{start, end, purpose}`, timestamps ISO-8601 UTC. Agent-hours = Σ(`end` − `start`) across all sessions in all lane logs.
- `costs`: each entry is `{item, usd, evidence}` — a dollar cost with a pointer to the receipt/report that backs it.
- `interventions`: each entry is `{at, who, what, minutes}` — anything a human did or was asked to do.
- `friction`: each entry is `{at, what, workaround}` — engine/MCP/tool trouble and how it was worked around.
- `blockers`: each entry is `{what, since, waiting_on}`.
- `deliverables`: `{build, capture, stills: [], tests}` — paths to the lane's evidence files.

Shared costs (Spine Professional, the desert kit, the protagonist rig) that are not specific to one lane go in `docs/bakeoff/shared-costs.md` on `master`, not in a lane log.
