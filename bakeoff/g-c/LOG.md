---
# THROWAWAY: bake-off lane G-C log (docs/bakeoff/lane-log-format.md).
# Check it with: uv run --project tools/bakeoff bakeoff log-check bakeoff/g-c/LOG.md
lane: g-c
direction: C
engine: godot
machine: oryx
status: in-progress
sessions:
  - {start: "2026-09-27T17:05:00Z", end: "2026-09-27T17:12:00Z", purpose: "workspace from bakeoff/g-a, read the brief, mechanic, plan Tasks 7 and 10 and G-A's art code; paused before any edit while the lead asked Sami whether G-C's art is hand-written SVG instead of Recraft"}
  - {start: "2026-09-27T17:38:11Z", end: "2026-09-27T18:13:38Z", purpose: "lane setup (game/g-a moved to game/g-c), eleven hand-written SVG pieces, VectorArt, provenance, G-A's rig reader ported, ci.sh, software capture and look at the stills"}
  - {start: "2026-09-27T17:58:00Z", end: "2026-09-27T19:38:48Z", purpose: "protagonist rig from PR #28 (phase1/protagonist-parts fd76d946, unmerged) copied into protagonist/; looked at in context; preliminary capture with Violet (scratch copy, not committed)"}
costs: []
interventions:
  - {at: "2026-09-27T17:37:00Z", who: sjawhar, what: "ruled that agents make the bake-off art themselves (no Recraft), which unpaused the lane; asked by the lead, not by this lane, so the minutes Sami spent are not known here and 0 is recorded", minutes: 0}
friction:
  - {at: "2026-09-27T17:12:00Z", what: "the lead paused the lane before any edit while Sami was asked whether G-C's art is hand-written SVG or Recraft", workaround: "none; resumed at 17:38 once Sami ruled that agents make the art (the workspace had no edits to keep)"}
  - {at: "2026-09-27T17:40:00Z", what: "PaintedArt draws each wall and crystal cell as one 256 px region of its texture picked by column and row mod 4 (ground and platform cells: the top 512 px, two cells wide), so a one-cell-wide crystal wall shows a single 256 px column strip and a one-row crystal platform shows a single 256 px band", workaround: "crystal-wall is four self-contained 256 px crystal-pillar strips that repeat vertically; crystal-platform repeats one ledge band four times; the wall strata repeat every 256 px so every cell edge and the ground/platform-to-wall joins sit in the base rock color"}
  - {at: "2026-09-27T17:41:00Z", what: "the reveal shader multiplies the crystal texture by the tag color, and the orb is drawn with the tag color as its modulate, so crystals drawn red or green would come out dark or muddy for the other color", workaround: "crystal-wall, crystal-platform and orb are drawn in neutral light grays; in game they render #e04a3a / #3fbf6a (lead confirmed this as the rule for tagged 2D and vector art)"}
  - {at: "2026-09-27T17:44:00Z", what: "my own preview tooling: ImageMagick's -flatten after +append/-append cropped the tiled seam previews back to the first image's page size, so they showed one tile and could not show a seam", workaround: "+repage before -flatten; seams checked on 2x2 tilings and with magick -roll +512+0 (tiles) / +768+0 (backdrops)"}
  - {at: "2026-09-27T17:47:00Z", what: "Godot 4.7.2's SVG import defaults to mipmaps/generate=false, while PaintedArt samples its textures with LINEAR_WITH_MIPMAPS (1024 px art drawn at 64 px per cell)", workaround: "set mipmaps/generate=true (and kept svg/scale=1.0, so each SVG rasterizes at its viewBox size) in every .svg.import; clean reimport has no errors"}
  - {at: "2026-09-27T17:51:00Z", what: "ThorVG ignored fill-rule=evenodd on the arch path drawn through <use>, so backdrop-mid's arch came out as a solid block with no opening", workaround: "drew the arch as one outline that runs around the opening"}
  - {at: "2026-09-27T17:58:00Z", what: "G-A gained the character-rig reader (docs/bakeoff/character-rig.md, #25/#26) and an export-smoke log check after this lane branched at 31283bc1; jj does not track the game/g-a to game/g-c rename, so a rebase would not carry them over", workaround: "copied bakeoff/rig.gd, bakeoff/rig_animator.gd, art/rig_character_2d.gd, tests/rig_test.* and tests/rig/* from bakeoff/g-a@origin (fa7bf9af) and applied G-A's diffs to greybox_art.gd, painted_art.gd, ci.sh and README.md by hand (lane=g-c kept); ci.sh prints rig-test: 0 failure(s)"}
  - {at: "2026-09-27T18:00:00Z", what: "oryx's NVIDIA GPU is off limits (wedged driver)", workaround: "scripts/capture-godot.sh with DISPLAY unset (llvmpipe and lavapipe under Xvfb) plus __GLX_VENDOR_LIBRARY_NAME=mesa; Godot reported Mesa llvmpipe; 66 s capture took 3.5-11 min"}
  - {at: "2026-09-27T18:05:00Z", what: "the preliminary capture with the rig took 12-14 minutes of wall time per Godot lane (g-a 848 s, g-d 795 s, g-c 735 s run back to back), not the 4 minutes measured earlier, on a machine shared with other sessions", workaround: "none needed; captures stay in scratch copies until the rig PR is approved"}
blockers: []
deliverables: {build: bakeoff/g-c/reports/build.txt, capture: bakeoff/g-c/capture/capture.mp4, stills: [bakeoff/g-c/capture/still-05.png, bakeoff/g-c/capture/still-20.png, bakeoff/g-c/capture/still-40.png, bakeoff/g-c/capture/still-60.png], tests: bakeoff/g-c/reports/replay.json}
---

THROWAWAY. Lane G-C (Godot 4.7.2 2D, flat-vector desert kit, environment only) of the Phase 1 bake-off. Nothing here is canon.

G-C is G-A's project (level, physics, replay, tag check, rig reader) with its own look: the eleven pieces of the desert brief written by hand as SVG code, with no image generation and nothing bought (so `costs` is empty). `art/vector_art.gd` (VectorArt, a PaintedArt) and `art/lane_art.tres` point PaintedArt's slots at `art/*.svg`. The character is the STAND-IN capsule: G-C is environment-only by definition, and the rig reader only swaps it out once `protagonist/rig/violet.json` exists. G-A's evidence stays under `bakeoff/g-a/`, untouched. G-A's painted PNGs and their sidecars were removed from `game/g-c/art/`.

The pieces: `ground-tile`, `wall-tile`, `platform-tile`, `hazard-tile` (sandstone spikes in rock and shadow violet on a violet rubble base, never tag colors), `crystal-wall`, `crystal-platform`, `orb`, `goal-gate` (sandstone arch with the low sun in it), `backdrop-far` (flat teal-to-peach sky bands, sun, cloud streaks), `backdrop-mid` (mesas, a butte and a wind-cut arch; transparent sky), `backdrop-near` (two dune ridges; saguaro, acacia and dry brush as shadow-violet silhouettes, no green). Each uses 4-6 flat fills from the brief palette and its tints, with no gradients and no strokes. Each has a `generated` provenance record (tool hand-written-svg, provider anthropic, model claude-opus-5-5, the id the harness reports for the authoring model).

Looked at: every piece rasterized by Godot's own ThorVG path (a throwaway `Image.load_svg_from_string` script), tiled 2x2 and rolled half a tile, with no seams; the capture stills at 5/20/40/60 s: flat colors read, the red and green crystals stand out against the ochre and teal world (gray until acquired, bright and pulsing while active), no green anywhere but the green crystal. The capture was re-rendered after the rig port.

Rejected along the way: crystal-platform v1 (a zigzag of triangles: read as saw teeth, and its hanging tips as hazard spikes) and v2 (the crystal prism laid on its side: read as arrows on a rail), then a gap at the band seam in v3; wall-tile v1 (too many violet cracks and pebbles: in big blocks they repeated as a grid of squiggles); orb v1 (after the tint multiply the green orb was a dark blob on the sand; its grays were raised); backdrop-mid v1 (arch opening filled, see friction) and v2 (the opening sat below the near dunes; arch raised).

Still visible and not changed by this lane: the camera shows 1080 px of a 1024 px level, so dark bars show above and below (G-A's camera); wall cells under an open-topped ground cell change from the ground tile's strata to the wall tile's, which shows as a small step at block edges (PaintedArt's per-cell tile choice).


Protagonist rig: `protagonist/rig/violet.json`, `violet.meta.json` and `protagonist/parts/*.png` are copied byte for byte, with their provenance sidecars, from PR #28 (branch phase1/protagonist-parts, fd76d946, not merged yet; real PNGs from the violet-rig workspace, not LFS pointers). Re-copy them if #28 changes. `attach_character` now shows Violet instead of the STAND-IN; the replay, the tag checks, rig-test and the export smoke run pass with it loaded.
