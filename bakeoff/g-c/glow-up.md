# Lane G-C glow-up record (THROWAWAY)

THROWAWAY: part of the Phase 1 bake-off's glow-up round; the rules are in [docs/bakeoff/glow-up.md](../../docs/bakeoff/glow-up.md). This lane improves the vector world and how Violet reads in it; Violet herself stays at `game/g-c/protagonist/` from PR #28 at 9b22572d until Sami approves her glowed-up version.

## The bar

Scored against:

- GRIS — https://store.steampowered.com/app/683320/GRIS/
- Planet of Lana — https://store.steampowered.com/app/1608230/Planet_of_Lana/

Named for gaps only, not for scoring (direction C, flat vector):

- Alto's Odyssey — https://altosodyssey.com/press (Snowman's official press kit): flat-vector desert dunes, canyons and sky with layered parallax, atmospheric haze and dynamic lighting.
- Old Man's Journey — https://store.steampowered.com/app/581270/Old_Mans_Journey/: flat illustrated landscapes built from layered hills with soft light and texture.

All four links returned HTTP 200 on 2026-09-29. None of their images is downloaded, committed or used for generation.

## Fixed shots

From the lane workspace root (`/home/agent/src/violet-g-c`), every round:

```
env -u DISPLAY PATH=/home/agent/.mise/installs/godot/4.7.2-stable:/home/agent/.mise/installs/ffmpeg/9.0.2/.mise-bins:$PATH \
  __GLX_VENDOR_LIBRARY_NAME=mesa __EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/50_mesa.json \
  bash scripts/capture-godot.sh g-c
```

This is software rendering: Mesa llvmpipe under Xvfb, launched by `capture-lib.sh` because `DISPLAY` is unset. Then `cp bakeoff/g-c/capture/still-{05,20,40,60}.png bakeoff/g-c/glow-up/round-NN/` and `jj restore bakeoff/g-c/capture`, so the judging capture stays untouched.

## Rounds

| round | start (UTC) | end (UTC) | what changed | USD | letter mapping | axes better | axes worse | scores A and B (visual_quality / character_appeal / color_readability) | the new round's three gaps | kept |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2026-09-29T00:25:01Z | 2026-09-29T00:33:29Z | the look before the round (lane at 804ca911: hand-written SVG kit, tag-wall/tag-platform, curved-blade brush, Violet 9b22572d) | 0 | A = round 0 (only set) | — (single set) | — (single set) | A: 2 / 2 / 3 | 1. no light or atmosphere: flat sky and sun, pill clouds, backdrop repeats every ~1530 px, dirt tile every ~255 px, flat beige pits; 2. Violet reads as a soft grey rendered figure, ~95 px, face unreadable, wall-cling floats; 3. tag red and green drift (salmon to red, mint to forest), hue-only split, red scarf lost on red wall ([critic.md](glow-up/round-00/critic.md)) | yes |
| 1 | 2026-09-29T00:39:38Z | 2026-09-29T00:51:35Z | gap 1 of round 0 (light, atmosphere, repetition), chosen because it is the biggest visual_quality gap and wholly the lane's (gap 2 asks to redraw and rescale Violet, which is the lead's; gap 3 is partly hers, the scarf outline): backdrops widened to 3072 px with new second halves (a screen no longer shows the same art twice); sky as a teal-to-peach gradient, sun bloom, clouds with lit tops and shaded bases, distant ranges and mesas fading into haze, warm rim light on sunward rock edges, sunlit dune crests; two wall-tile and two ground-tile variants picked per block; pits darken toward the spikes; sky and rock fill the strips above and below the level. Draw cost: three 3072x1024 backdrop textures with mipmaps (about 16 MB each in VRAM) instead of 1536 px ones; everything else is the same sprites and one extra gradient quad per hazard cell | 0 (no generation; hand-written SVG and GDScript) | B = round 1 (new), A = round 0 | visual_quality | none | A (round 0): 2 / 2 / 3; B (round 1): 3 / 2 / 3 | 1. lighting stops at the sky: foreground blocks and dunes evenly lit, no cast shadow, contact darkening or warm tops, no depth haze before the playfield; 2. tile seams show as vertical strata breaks, motif repeats, pit fade is a hard-edged off-palette grey box; 3. Violet grey and soft in a vector world, low contrast on sand, red scarf lost on the salmon wall ([critic.md](glow-up/round-01/critic.md)) | yes |
| 2 | 2026-09-29T00:55:56Z | 2026-09-29T01:21:18Z | gap 1 of round 1 (the lighting stops at the sky), chosen as the largest visual_quality gap that is wholly the lane's (gap 3 is Violet's look; gap 2, seams and the pit box, is smaller): the low sun on the left now lights the foreground. Warm light on open block tops and sunward faces, shade on far faces, and each far face throws a feathered shadow 44 px right onto the backdrop; rock darkens with depth below the surface; a haze gradient between the dunes and the playfield; a contact shadow under Violet while she is grounded (her parts and rig untouched). A first version cast the terrain shadow through a CanvasGroup blurred with mipmaps: the compatibility renderer drew it hard-edged, a dark copy of every block and tag wall, so it was dropped before shooting. Draw cost: up to four vertex-coloured quads per solid cell (about 700 small polygons) and one full-level gradient rect; no offscreen buffers | 0 (no generation; GDScript only) | pending critic | pending critic | pending critic | pending critic | pending critic | pending |
