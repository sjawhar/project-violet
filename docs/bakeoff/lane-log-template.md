---
# THROWAWAY: a bake-off lane log (docs/bakeoff/lane-log-format.md). Copy to bakeoff/<lane>/LOG.md.
# Check it with: uv run --project tools/bakeoff bakeoff log-check bakeoff/<lane>/LOG.md
lane: g-a  # the lane's directory name: g-a | g-d | u-d | g-c | control
direction: A  # A | C | D | control
engine: godot  # godot | unity | blender
machine: oryx  # oryx | sami
status: in-progress  # in-progress | delivered | blocked
sessions: []
# - {start: "2026-09-28T09:00:00Z", end: "2026-09-28T11:30:00Z", purpose: greybox level and replay}
costs: []
# - {item: "gen image, 12 body parts", usd: 1.80, evidence: "provider dashboard, 2026-09-28"}
interventions: []
# - {at: "2026-09-28T10:05:00Z", who: sjawhar, what: approved the shared-inputs PR, minutes: 5}
friction: []
# - {at: "2026-09-28T09:40:00Z", what: "--export-release exited 0 without a binary", workaround: "test -x plus a headless smoke run"}
blockers: []
# - {what: Recraft paid account, since: "2026-09-28T09:00:00Z", waiting_on: sjawhar}
deliverables: {build: null, capture: null, stills: [], tests: null}
# e.g. {build: out/g-a/violet-g-a.x86_64, capture: bakeoff/g-a/capture/capture.mp4, stills: [bakeoff/g-a/capture/still-05.png], tests: bakeoff/g-a/reports/replay.json}
---

Free-form notes: what worked, what didn't, anything the numbers above don't show.
