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
  - {start: "2026-09-27T09:18:56Z", end: "2026-09-27T09:38:00Z", purpose: "painted art regenerated at quality=high with transparent backgrounds (gen from PR #20)"}
  - {start: "2026-09-27T09:42:03Z", end: "2026-09-27T09:55:00Z", purpose: "no vegetation green: backdrop-near and goal-gate regenerated with violet silhouettes and no plants"}
  - {start: "2026-09-27T15:52:28Z", end: "2026-09-27T16:03:00Z", purpose: "hazard-tile from the updated biome brief: sandstone spikes on the hazard cells"}
  - {start: "2026-09-27T17:10:00Z", end: "2026-09-27T17:31:55Z", purpose: "rig reader without Spine (Sami 2026-09-27: no Spine purchase): bakeoff/rig.gd, RigCharacter2D, rig tests, placeholder rig seen animating (shared with lane G-D)"}
costs:
  - {item: "gen image gpt-image-2 1024x1024 quality=low, wall-tile (rejected)", usd: 0.0143, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:47:36+00:00)"}
  - {item: "gen image gpt-image-2 1536x1024 quality=low, backdrop-near (rejected)", usd: 0.0062, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:48:31+00:00)"}
  - {item: "superseded by the quality=high regeneration: gen image gpt-image-2 1024x1024 quality=low, wall-tile", usd: 0.0073, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:48:31+00:00)"}
  - {item: "gen image gpt-image-2 1536x1024 quality=low, backdrop-far (rejected)", usd: 0.0061, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:48:31+00:00)"}
  - {item: "superseded by the quality=high regeneration: gen image gpt-image-2 1024x1024 quality=low, orb", usd: 0.0073, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:48:31+00:00)"}
  - {item: "gen image gpt-image-2 1536x1024 quality=low, backdrop-mid (rejected)", usd: 0.0063, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:48:31+00:00)"}
  - {item: "superseded by the quality=high regeneration: gen image gpt-image-2 1024x1024 quality=low, crystal-wall", usd: 0.0073, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:48:32+00:00)"}
  - {item: "superseded by the quality=high regeneration: gen image gpt-image-2 1024x1024 quality=low, ground-tile", usd: 0.0074, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:48:32+00:00)"}
  - {item: "superseded by the quality=high regeneration: gen image gpt-image-2 1024x1024 quality=low, platform-tile", usd: 0.0073, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:48:32+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024 quality=low, goal-gate (rejected)", usd: 0.0072, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:48:32+00:00)"}
  - {item: "superseded by the quality=high regeneration: gen image gpt-image-2 1024x1024 quality=low, crystal-platform", usd: 0.0146, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:48:36+00:00)"}
  - {item: "superseded by the quality=high regeneration: gen image gpt-image-2 1536x1024 quality=low, backdrop-near", usd: 0.0064, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:49:48+00:00)"}
  - {item: "superseded by the quality=high regeneration: gen image gpt-image-2 1536x1024 quality=low, backdrop-mid", usd: 0.0064, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:49:50+00:00)"}
  - {item: "superseded by the quality=high regeneration: gen image gpt-image-2 1536x1024 quality=low, backdrop-far", usd: 0.0118, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:49:53+00:00)"}
  - {item: "superseded by the quality=high regeneration: gen image gpt-image-2 1024x1024 quality=low, goal-gate", usd: 0.0146, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T08:49:55+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024 quality=high, orb (kept)", usd: 0.2120, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T09:21:50+00:00)"}
  - {item: "gen image gpt-image-2 1536x1024 quality=high, backdrop-far (kept)", usd: 0.1661, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T09:23:27+00:00)"}
  - {item: "gen image gpt-image-2 1536x1024 quality=high, backdrop-near (rejected)", usd: 0.1662, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T09:23:42+00:00)"}
  - {item: "gen image gpt-image-2 1536x1024 quality=high, backdrop-mid (kept)", usd: 0.1662, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T09:23:43+00:00)"}
  - {item: "superseded by the no-green regeneration: gen image gpt-image-2 1024x1024 quality=high, goal-gate", usd: 0.2120, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T09:24:26+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024 quality=high, wall-tile (rejected)", usd: 0.2122, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T09:24:32+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024 quality=high, crystal-wall (rejected)", usd: 0.2121, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T09:24:39+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024 quality=high, platform-tile (rejected)", usd: 0.2122, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T09:24:39+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024 quality=high, ground-tile (rejected)", usd: 0.2122, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T09:24:46+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024 quality=high, crystal-platform (kept)", usd: 0.2121, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T09:24:47+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024 quality=high, crystal-wall (kept)", usd: 0.2122, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T09:28:45+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024 quality=high, platform-tile (kept)", usd: 0.2123, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T09:28:46+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024 quality=high, ground-tile (kept)", usd: 0.2123, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T09:28:46+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024 quality=high, wall-tile (kept)", usd: 0.2123, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T09:28:49+00:00)"}
  - {item: "superseded by the no-green regeneration: gen image gpt-image-2 1536x1024 quality=high, backdrop-near", usd: 0.1663, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T09:32:58+00:00)"}
  - {item: "gen image gpt-image-2 1536x1024 quality=high, backdrop-near (rejected)", usd: 0.1663, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T09:45:59+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024 quality=high, goal-gate (rejected)", usd: 0.2120, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T09:46:41+00:00)"}
  - {item: "gen image gpt-image-2 1536x1024 quality=high, backdrop-near (kept)", usd: 0.1665, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T09:49:03+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024 quality=high, goal-gate (kept)", usd: 0.2121, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T09:49:58+00:00)"}
  - {item: "gen image gpt-image-2 1024x1024 quality=high, hazard-tile (kept)", usd: 0.2124, evidence: "bakeoff/g-a/reports/gen-cost.txt (2026-09-27T15:55:22+00:00)"}
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
  - {at: "2026-09-27T09:26:00Z", what: "at quality=high, three of the five tiles did not tile (wall-tile and platform-tile broke at the side seam, crystal-wall at the top/bottom seam) and ground-tile had red and green pebbles", workaround: "regenerated the four with explicit wrap-around wording and 'pebbles in sand and gray tones only'; the second round tiled"}
  - {at: "2026-09-27T09:31:00Z", what: "the first quality=high backdrop-near had trees at both side edges, so the seam crossfade left a half-transparent green tree canopy floating over the dunes", workaround: "regenerated it with the outer eighth of each side kept to low dunes and grass; the seam edit now crossfades only dunes"}
  - {at: "2026-09-27T09:43:00Z", what: "the quality=high backdrop-near painted the acacia and saguaro olive green and the goal gate had green grass tufts; the brief allows no vegetation green, and green plants beside green walls blur the tag color", workaround: "regenerated both: near with the trees, cacti and grass as shadow violet #5a4a7a silhouettes and 'no green anywhere', the gate with no plants; no hue-shift edit needed. backdrop-mid (mesas only), backdrop-far (sky; its only green-leaning pixels are the teal-to-peach gradient) and the five tiles had no vegetation and were kept"}
  - {at: "2026-09-27T09:46:00Z", what: "my own scripting mistake: a prompt edit failed its assertion inside a ';' chain and the regeneration ran anyway with the old prompts", workaround: "the two re-rolls are logged as rejected ($0.3783); reran with the edit gated by '&&'"}
  - {at: "2026-09-27T16:00:00Z", what: "the spike tile drawn on its own in the hazard cells was the same sandstone color as the near-backdrop dunes behind the pit and barely read", workaround: "the hazard cell keeps its dark shadow-violet floor and draws the spikes on top"}
  - {at: "2026-09-27T17:15:00Z", what: "the rig contract (docs/bakeoff/character-rig.md, PR #25) was not merged when the reader was started, so the first draft followed Spine runtime semantics: setup value before a timeline's first key, and jump/dash/double_jump/land played once", workaround: "switched to the contract when it arrived: the first key holds before it and every animation loops; land still plays once, then run or idle (RigAnimator)"}
  - {at: "2026-09-27T17:24:00Z", what: "spinerig render (the contract's reference implementation) exists only on PR #25's branch, so the lane's own tools/spinerig cannot regenerate the reference fixture", workaround: "tests/rig/make-fixture.sh takes SPINERIG=<a tools/spinerig with render.py>; run here against a throwaway extraction of the PR branch"}
  - {at: "2026-09-27T17:27:00Z", what: "Godot 4.7.2 turns physics processing back on when a node with _physics_process enters the tree, so set_physics_process(false) before add_child did nothing and the player fell during a throwaway pixel comparison (a 10-15 px offset that read as a placement bug)", workaround: "disable it after add_child"}
  - {at: "2026-09-27T17:30:00Z", what: "the workspace holds uncommitted spine-godot binaries in game/g-a/bin from an earlier godot-fetch.sh, which master no longer fetches; local exports pack bin/spine_godot_extension.gdextension (reports/export.log shows it), CI exports do not", workaround: "left out of every commit; the throwaway look-at copy deletes bin/"}
blockers: []
deliverables: {build: bakeoff/g-a/reports/build.txt, capture: null, stills: [], tests: bakeoff/g-a/reports/replay.json}
---

THROWAWAY. Lane G-A (Godot 4.7.2 2D, painted world) of the Phase 1 bake-off. Nothing here is canon.

Done: the greybox milestone (plan Task 7 Steps 1-17), the painted world (Step 18) and the rig reader that replaces Step 19's spine-godot (Sami ruled on 2026-09-27 that the bake-off buys no Spine). Still to come: the protagonist rig itself (Task 5) and captures (Step 20); until `protagonist/violet.rig.json` is in the project the character is the STAND-IN capsule.

Rig reader: `bakeoff/rig.gd` (dimension-agnostic, G-D has the same file) reads the Spine 4.3 JSON subset of docs/bakeoff/character-rig.md and poses it by forward kinematics; `bakeoff/rig_animator.gd` picks the animation (dash; airborne: double_jump once used, else jump while rising, else fall; land plays once on landing; run; idle); `art/rig_character_2d.gd` draws one Sprite2D per slot, scaled to 1.6 tiles from the meta's height_px, flipped with the facing, scarf slots tinted with the active color. `tests/rig_test.tscn` checks FK against a hand calculation, interpolation and looping, the spinerig round trip, and every slot of every frame `spinerig render` draws for the placeholder rig (worst difference 0.000033 px/deg). Looked at in a throwaway copy with the placeholder rig as `protagonist/`: the replay rendered in software shows it idle, run, jump, fall, land, dash (red scarf) and double-jump flip (green scarf); drawn at scale 1 it matches `spinerig render` frames to within 17 edge pixels of about 8000.

The replay puts the four moments the capture stills look for on capture-lib's still times: red orb at about 5 s (tick 287), the air-dash over the pit at 20 s (ticks 1194-1206), the green orb at 40 s (tick 2394), the mid-air switch at col 57 at 60 s (tick 3593). The goal is reached at tick 3757; capture mode runs to tick 3960 (66 s). Between them the player idles or walks back and forth through the wall of the active color.

A hazard touch is reported twice when the player's box overlaps two hazard cells; the run fails either way.

Painted world (Step 18): the eleven pieces the biome brief lists (hazard-tile added when the brief gained it), generated by `bakeoff/g-a/gen-art.sh` with gpt-image-2 at quality=high (prompts and palette in the script and in each sidecar); the orb, the goal gate, the hazard tile and the mid and near backdrops come out of gen with `--background transparent`. `bakeoff/g-a/edit-art.sh` then crops each backdrop to its best-matching edge bands and crossfades them so it repeats (recorded with `provenance edit`). PaintedArt (art/painted_art.gd, art/lane_art.tres) chooses ground-tile for open-topped cells on the ground line, platform-tile for open-topped cells above it, wall-tile inside; crystal cells get art/reveal.gdshader (gray until acquired, tinted once acquired, glow pulsing while active); orbs are the untinted orb sprite tinted by color; the goal gate is two tiles tall; hazard cells are a row of sandstone spikes (hazard-tile) over a dark shadow-violet floor. The backdrop is three Parallax2D layers (scroll 0.2/0.5/0.8). The character is still the STAND-IN capsule. Replays and the tag check run on the default greybox art, so the art cannot change collisions. The letterbox above and below the 16-row level is dark violet (project clear color) instead of gray.

The first Step 18 pass ran at the API's default quality=low (gen had no quality or background option then) and keyed magenta backgrounds by hand; its kept pieces are marked superseded in `costs`.

Rejected generations, quality=low pass: wall-tile v1 (cartoon brick look, red crystal sprouts in neutral rock), goal-gate v1 (red and green gems on the gate), backdrop-far v1 (clouds broke at the repeat seam), backdrop-mid v1 and backdrop-near v1 (red and green crystals in the scenery; mid also had a visible seam).

Rejected generations, quality=high pass: wall-tile, platform-tile (side seam), crystal-wall (top/bottom seam), ground-tile (red and green pebbles), backdrop-near (trees at both edges left a green ghost after the seam crossfade).

Rejected generations, no-green pass: backdrop-near and goal-gate re-rolled once with the unchanged prompt by a scripting mistake (still green vegetation and grass).
