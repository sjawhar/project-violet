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
costs: []
interventions: []
friction:
  - {at: "2026-09-27T08:46:00Z", what: "plan says project.godot has no [shader_globals], but the shared bakeoff/resonance.gd (byte-identical to G-A's) sets the world_saturation global on every color change; any rendered run logged 'Condition !global_shader_uniforms.variables.has(p_name) is true' each time (headless runs are silent)", workaround: "declared world_saturation under [shader_globals] in project.godot; no 3D shader reads it, the environment's adjustment_saturation carries the effect"}
  - {at: "2026-09-27T08:47:00Z", what: "plan's camera (fov 30 at 22 m) frames about 11.8 m of height, not the level's 16 m that the same step and mechanic.md (30 x 17 tiles visible) ask for", workaround: "camera 32 m from a rig that follows the player's x (clamped to [15, width - 15]) at the level's mid-height, still 2.5 m up and looking at the rig: the frame spans about 30 x 17 m"}
  - {at: "2026-09-27T08:48:00Z", what: "the replay runner's passable assert follows lane G-A's reading, not replay-format.md: the named kind names a color (bodies of that color passable, the other color solid), because mechanic.md makes platform_red passable alongside wall_red", workaround: "copied G-A's runner unchanged so both Godot lanes agree; the rule is with the lead"}
  - {at: "2026-09-27T08:50:00Z", what: "oryx's NVIDIA GPU is off limits (wedged driver), so looking at rendered Forward+ frames needs software Vulkan", workaround: "one full replay rendered with lavapipe under xvfb-run at 960x540, 28% of real time; captures stay with the lead on machine sami"}
blockers: []
deliverables: {build: bakeoff/g-d/reports/build.txt, capture: null, stills: [], tests: bakeoff/g-d/reports/replay.json}
---

THROWAWAY. Lane G-D (Godot 4.7.2 3D hybrid) of the Phase 1 bake-off. Nothing here is canon.

Greybox milestone (plan Task 8 Steps 1-5): toon-shaded greybox cubes, crystal omni lights on tagged cells, a peach-to-teal procedural sky, a warm sun with shadows, and the STAND-IN capsule character. Kit dressing (Step 6, needs the Meshy kit), the Spine rig and captures (Step 7) come later.

Lane G-A's replay passed unchanged in 3D: CharacterBody3D with a box shape against unit box colliders reached the goal at tick 3757, the same tick as G-A's 2D run, so no tick needed retuning. The key moments therefore sit on the same capture still times as G-A's (red orb about 5 s, air-dash over the pit 20 s, green orb 40 s, mid-air switch at col 57 60 s); capture mode runs to tick 3960 (66 s).

A hazard touch is reported twice when the player's box overlaps two hazard cells; the run fails either way.
