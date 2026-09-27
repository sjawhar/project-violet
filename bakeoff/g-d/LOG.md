---
# THROWAWAY: bake-off lane G-D log (docs/bakeoff/lane-log-format.md).
# Check it with: uv run --project tools/bakeoff bakeoff log-check bakeoff/g-d/LOG.md
lane: g-d
direction: D
engine: godot
machine: oryx
status: in-progress
sessions:
  - {start: "2026-09-27T08:39:00Z", end: "2026-09-27T08:52:48Z", purpose: "greybox milestone: workspace, 3D player/builder/art/game, copied G-A scripts and replay, ci.sh (plan Task 8 Steps 1-5)"}
  - {start: "2026-09-27T17:10:00Z", end: "2026-09-27T17:40:41Z", purpose: "rig reader without Spine (Sami 2026-09-27: no Spine purchase): G-A's bakeoff/rig.gd copied, RigCharacter3D, rig tests, placeholder rig seen animating (shared with lane G-A)"}
  - {start: "2026-09-27T17:46:00Z", end: "2026-09-27T17:52:37Z", purpose: "rig reader hardening: malformed rigs fail loudly (push_error, exit 1, no STAND-IN fallback), ci.sh smoke run fails on logged errors, rig contract #26 (path, looping by name, refusals)"}
  - {start: "2026-09-27T17:58:00Z", end: "2026-09-27T19:38:48Z", purpose: "protagonist rig from PR #28 (phase1/protagonist-parts fd76d946, unmerged) copied into protagonist/; looked at in context; preliminary capture with Violet (scratch copy, not committed)"}
costs: []
interventions: []
friction:
  - {at: "2026-09-27T08:46:00Z", what: "plan says project.godot has no [shader_globals], but the shared bakeoff/resonance.gd (byte-identical to G-A's) sets the world_saturation global on every color change; any rendered run logged 'Condition !global_shader_uniforms.variables.has(p_name) is true' each time (headless runs are silent)", workaround: "declared world_saturation under [shader_globals] in project.godot; no 3D shader reads it, the environment's adjustment_saturation carries the effect"}
  - {at: "2026-09-27T08:47:00Z", what: "plan's camera (fov 30 at 22 m) frames about 11.8 m of height, not the level's 16 m that the same step and mechanic.md (30 x 17 tiles visible) ask for", workaround: "camera 32 m from a rig that follows the player's x (clamped to [15, width - 15]) at the level's mid-height, still 2.5 m up and looking at the rig: the frame spans about 30 x 17 m"}
  - {at: "2026-09-27T08:48:00Z", what: "the replay runner's passable assert follows lane G-A's reading, not replay-format.md: the named kind names a color (bodies of that color passable, the other color solid), because mechanic.md makes platform_red passable alongside wall_red", workaround: "copied G-A's runner unchanged so both Godot lanes agree; the rule is with the lead"}
  - {at: "2026-09-27T08:50:00Z", what: "oryx's NVIDIA GPU is off limits (wedged driver), so looking at rendered Forward+ frames needs software Vulkan", workaround: "one full replay rendered with lavapipe under xvfb-run at 960x540, 28% of real time; captures stay with the lead on machine sami"}
  - {at: "2026-09-27T17:33:00Z", what: "a GDScript type-inference parse error in art/rig_character_3d.gd broke the exported build's scripts (game_3d.gd failed to compile), yet ci.sh stayed green: the replay runs compiled, and the export smoke run (--headless --quit-after 120) exits 0 whatever its stderr says", workaround: "fixed the declaration; ci.sh now fails the export smoke run on SCRIPT ERROR: and ERROR: lines"}
  - {at: "2026-09-27T17:40:00Z", what: "mirroring the character by scale.x = -1 turned the shaded Sprite3Ds' normals away from the sun, so the placeholder rig rendered nearly black whenever it faced left", workaround: "each sprite is mirrored instead (x and angle negated, flip_h set): a documented lane deviation from character-rig.md, which mirrors with a negative x scale on the root"}
  - {at: "2026-09-27T17:24:00Z", what: "spinerig render (the rig contract's reference implementation) exists only on PR #25's branch, so the lane's own tools/spinerig cannot regenerate the reference fixture", workaround: "tests/rig/make-fixture.sh takes SPINERIG=<a tools/spinerig with render.py>"}
  - {at: "2026-09-27T17:55:00Z", what: "GDScript asserts do not stop anything: a failed one returns from the function and the game runs on, and release exports strip them, so a malformed rig would have loaded half-way", workaround: "rig.gd reports every refusal with push_error and returns null; attach_character then push_errors and quits with exit 1 instead of showing the STAND-IN"}
  - {at: "2026-09-27T17:58:00Z", what: "a Godot 4.7.2 release export swallows some runtime script errors (a missing Dictionary key reads as null, an out-of-range index prints nothing) and crashes with exit 139 and no log line on a method call through null", workaround: "ci.sh fails the export smoke run on a non-zero exit or any SCRIPT ERROR: or ERROR: line (compile errors, failed script loads, push_error); the silent release-only errors stay invisible to it"}
  - {at: "2026-09-27T18:05:00Z", what: "the preliminary capture with the rig took 12-14 minutes of wall time per Godot lane (g-a 848 s, g-d 795 s, g-c 735 s run back to back), not the 4 minutes measured earlier, on a machine shared with other sessions", workaround: "none needed; captures stay in scratch copies until the rig PR is approved"}
blockers: []
deliverables: {build: bakeoff/g-d/reports/build.txt, capture: null, stills: [], tests: bakeoff/g-d/reports/replay.json}
---

THROWAWAY. Lane G-D (Godot 4.7.2 3D hybrid) of the Phase 1 bake-off. Nothing here is canon.

Greybox milestone (plan Task 8 Steps 1-5): toon-shaded greybox cubes, crystal omni lights on tagged cells, a peach-to-teal procedural sky, a warm sun with shadows, and the STAND-IN capsule character. Kit dressing (Step 6, needs the Meshy kit), the protagonist rig itself (Task 5) and captures (Step 7) come later.

Rig reader (in place of Step 6's SpineSprite3D; Sami ruled on 2026-09-27 that the bake-off buys no Spine): G-A's `bakeoff/rig.gd` and `bakeoff/rig_animator.gd`, unchanged, read and pose the Spine 4.3 JSON subset of docs/bakeoff/character-rig.md; `art/rig_character_3d.gd` draws one shaded Sprite3D per slot in the player's XY plane, pixel_size = 1.6 / height_px, mirrored per sprite for the facing, scarf slots tinted with the active color. `tests/rig_test.tscn` (G-A's) passes here too. Looked at in a throwaway copy with the placeholder rig as `protagonist/`, rendered with lavapipe: idle, run, jump, fall, land, dash (red scarf) and the double-jump flip (green scarf), lit by the sun and the crystal lights; unshaded through an orthographic camera it matches `spinerig render` frames to within 31 edge pixels of about 8000.

Lane G-A's replay passed unchanged in 3D: CharacterBody3D with a box shape against unit box colliders reached the goal at tick 3757, the same tick as G-A's 2D run, so no tick needed retuning. The key moments therefore sit on the same capture still times as G-A's (red orb about 5 s, air-dash over the pit 20 s, green orb 40 s, mid-air switch at col 57 60 s); capture mode runs to tick 3960 (66 s).

A hazard touch is reported twice when the player's box overlaps two hazard cells; the run fails either way.


Protagonist rig: `protagonist/rig/violet.json`, `violet.meta.json` and `protagonist/parts/*.png` are copied byte for byte, with their provenance sidecars, from PR #28 (branch phase1/protagonist-parts, fd76d946, not merged yet; real PNGs from the violet-rig workspace, not LFS pointers). Re-copy them if #28 changes. `attach_character` now shows Violet instead of the STAND-IN; the replay, the tag checks, rig-test and the export smoke run pass with it loaded.
