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
| 0 | 2026-09-29T00:25:01Z | 2026-09-29T00:33:29Z | the look before the round (lane at 804ca911: hand-written SVG kit, tag-wall/tag-platform, curved-blade brush, Violet 9b22572d) | 0 | A = round 0 (only set) | — | — | pending critic | pending critic | yes |
