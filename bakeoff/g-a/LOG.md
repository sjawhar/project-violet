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
  - {start: "2026-09-27T08:43:18Z", end: "2026-09-27T09:08:00Z", purpose: "painted world (plan Task 7 Step 18): gen image pieces, PaintedArt, reveal shader, parallax backdrop"}
costs:
  - {item: "gen image gpt-image-2 1024x1024, wall-tile (rejected)", usd: 0.0143, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:47:36+00:00)"}
  - {item: "gen image gpt-image-2 1536x1024, backdrop-near (rejected)", usd: 0.0062, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:48:31+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024, wall-tile (kept)", usd: 0.0073, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:48:31+00:00)"}
  - {item: "gen image gpt-image-2 1536x1024, backdrop-far (rejected)", usd: 0.0061, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:48:31+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024, orb (kept)", usd: 0.0073, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:48:31+00:00)"}
  - {item: "gen image gpt-image-2 1536x1024, backdrop-mid (rejected)", usd: 0.0063, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:48:31+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024, crystal-wall (kept)", usd: 0.0073, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:48:32+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024, ground-tile (kept)", usd: 0.0074, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:48:32+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024, platform-tile (kept)", usd: 0.0073, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:48:32+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024, goal-gate (rejected)", usd: 0.0072, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:48:32+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024, crystal-platform (kept)", usd: 0.0146, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:48:36+00:00)"}
  - {item: "gen image gpt-image-2 1536x1024, backdrop-near (kept)", usd: 0.0064, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:49:48+00:00)"}
  - {item: "gen image gpt-image-2 1536x1024, backdrop-mid (kept)", usd: 0.0064, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:49:50+00:00)"}
  - {item: "gen image gpt-image-2 1536x1024, backdrop-far (kept)", usd: 0.0118, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:49:53+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024, goal-gate (kept)", usd: 0.0146, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:49:55+00:00)"}
interventions: []
friction:
  - {at: "2026-09-27T08:26:30Z", what: "plan's export_presets.cfg omits include_filter and exclude_filter; every godot --import printed 'Couldn't find the given section preset.0 and key include_filter' errors", workaround: "added include_filter=\"\" and exclude_filter=\"\" to the preset"}
  - {at: "2026-09-27T08:28:00Z", what: "plan's skeleton replay fell into the pit: the jump at tick 199 came after the player had walked off the edge at col 18", workaround: "retuned every input with --trace (per-tick positions from a throwaway copy of the runner)"}
  - {at: "2026-09-27T08:29:00Z", what: "the plan's first runner text checked passable per kind (named kind passable, every other tagged body solid), which cannot hold with red active because mechanic.md makes platform_red passable too; [33,12] failed with 'platform_red_53_8 passable should be false'", workaround: "runner reads passable as a color (every body of that color passable, every other tagged body solid); the lead has since made that the format's rule, so the runner now follows the format"}
  - {at: "2026-09-27T08:32:00Z", what: "oryx's NVIDIA GPU is off limits (wedged driver), so looking at rendered frames needs software GL", workaround: "llvmpipe under xvfb-run with mesa-only GLX/EGL vendor overrides, 32-45% of real time; captures stay with the lead on machine sami"}
  - {at: "2026-09-27T08:44:00Z", what: "plan Step 18 generates with --input (the approved kit turntable or protagonist concept); neither exists yet (#19's concept unapproved, Task 6's turntable not made)", workaround: "lead's decision: no --input; every prompt carries the biome brief's hex palette instead (deviation from the plan)"}
  - {at: "2026-09-27T08:46:00Z", what: "tools/gen keeps no token usage, so a generation's cost has no record", workaround: "bakeoff/g-a/gen_usage.py runs gen unchanged and appends each response's usage to reports/gen-usage.jsonl; gen_cost.py prices it into reports/gen-cost.txt"}
  - {at: "2026-09-27T08:47:40Z", what: "gen passes no quality or background to the OpenAI Images API: every image came back quality=low and opaque, so the orb, goal gate and two backdrop layers could not be transparent", workaround: "painted those on flat magenta, keyed it out with bakeoff/g-a/art_edit.py key, recorded with provenance edit"}
  - {at: "2026-09-27T08:48:40Z", what: "gpt-image-2 put red and green crystals into neutral pieces (wall-tile v1, goal-gate v1, backdrop-mid and backdrop-near v1), which muddies the red/green tag colors; its 'seamless' backdrops did not repeat cleanly", workaround: "regenerated with explicit 'no crystals, no gems'; backdrops cropped to their best-matching edge bands and crossfaded (art_edit.py seam, provenance edit); backdrop-mid needed a second pass to drop a half-transparent ghost at the join"}
  - {at: "2026-09-27T08:56:00Z", what: "each 1024 px tile drawn whole into one 64 px cell (plan: scale = ts / texture width) repeated every cell as busy stripes", workaround: "PaintedArt shows a quarter of the texture per cell, picked by cell position, so one texture spans 4 cells (surface tiles: half, top edge kept)"}
  - {at: "2026-09-27T08:57:00Z", what: "Parallax2D loops only when repeat_size covers the screen; the backdrops are 1266-1397 px wide, so the mid layer showed a hard cut", workaround: "repeat_times = ceil(viewport width / texture width) + 1"}
blockers: []
deliverables: {build: bakeoff/g-a/reports/build.txt, capture: null, stills: [], tests: bakeoff/g-a/reports/replay.json}
---

THROWAWAY. Lane G-A (Godot 4.7.2 2D, painted world) of the Phase 1 bake-off. Nothing here is canon.

Done: the greybox milestone (plan Task 7 Steps 1-17) and the painted world (Step 18). Still to come: the Spine rig (Step 19) and captures (Step 20); until the rig lands the character is the STAND-IN capsule.

The replay puts the four moments the capture stills look for on capture-lib's still times: red orb at about 5 s (tick 287), the air-dash over the pit at 20 s (ticks 1194-1206), the green orb at 40 s (tick 2394), the mid-air switch at col 57 at 60 s (tick 3593). The goal is reached at tick 3757; capture mode runs to tick 3960 (66 s). Between them the player idles or walks back and forth through the wall of the active color.

A hazard touch is reported twice when the player's box overlaps two hazard cells; the run fails either way.

Painted world (Step 18): the ten pieces the biome brief lists, generated by `bakeoff/g-a/gen-art.sh` (gpt-image-2, prompts and palette in the script and in each sidecar) and edited by `bakeoff/g-a/edit-art.sh`. PaintedArt (art/painted_art.gd, art/lane_art.tres) chooses ground-tile for open-topped cells on the ground line, platform-tile for open-topped cells above it, wall-tile inside; crystal cells get art/reveal.gdshader (gray until acquired, tinted once acquired, glow pulsing while active); orbs are the untinted orb sprite tinted by color; the goal gate is two tiles tall; hazards are a flat dark violet. The backdrop is three Parallax2D layers (scroll 0.2/0.5/0.8). The character is still the STAND-IN capsule. Replays and the tag check run on the default greybox art, so the art cannot change collisions. The letterbox above and below the 16-row level is dark violet (project clear color) instead of gray.

Rejected generations: wall-tile v1 (cartoon brick look, red crystal sprouts in neutral rock), goal-gate v1 (red and green gems on the gate), backdrop-far v1 (clouds broke at the repeat seam), backdrop-mid v1 and backdrop-near v1 (red and green crystals in the scenery; mid also had a visible seam).
