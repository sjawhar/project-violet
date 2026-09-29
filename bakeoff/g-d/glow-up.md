# Lane G-D glow-up record (THROWAWAY)

THROWAWAY: Phase 1 bake-off process record; nothing here is canon. The rules are [docs/bakeoff/glow-up.md](../../docs/bakeoff/glow-up.md) (PR #35, at 75ee051d when round 0 was shot). This workstream improves lane G-D's 3D world and how Violet reads in it. Violet herself (`game/g-d/protagonist/`, from PR #28 at 9b22572d) stays as she is until Sami approves her glowed-up version.

## The bar

Scored against:

- GRIS: https://store.steampowered.com/app/683320/GRIS/
- Planet of Lana: https://store.steampowered.com/app/1608230/Planet_of_Lana/

Named only to find gaps, not to score (direction D: a 3D world seen side-on):

- INSIDE: https://store.steampowered.com/app/304430/INSIDE/. Playdead's side-on 3D platformer: restrained palette, volumetric light and fog layering, a small character that always reads against the world.
- Trine 4: The Nightmare Prince: https://store.steampowered.com/app/690640/Trine_4_The_Nightmare_Prince/. Frozenbyte's 2.5D fantasy platformer: a lush painterly 3D world with deep parallax, rich lighting and dense set dressing.

All four links returned HTTP 200 on 2026-09-29. No image from these games is downloaded, committed or used for generation.

## Fixed shots

Run from the lane workspace root (`/home/agent/src/violet-g-d`) on oryx, the same command and environment every round. Here `P=/home/agent/src/project-violet`:

```sh
export PATH="$(dirname $(cd $P && mise which godot)):$(dirname $(cd $P && mise which ffmpeg)):$PATH"
scripts/godot-fetch.sh game/g-d && godot --headless --path game/g-d --import
env -u DISPLAY __GLX_VENDOR_LIBRARY_NAME=mesa __EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/50_mesa.json scripts/capture-godot.sh g-d
```

With DISPLAY unset, the script renders in software (llvmpipe and lavapipe under Xvfb). The two mesa overrides keep GLX and EGL off oryx's NVIDIA driver. Its stills `bakeoff/g-d/capture/still-{05,20,40,60}.png` are copied to `bakeoff/g-d/glow-up/round-NN/`, and `bakeoff/g-d/capture/` is then removed again, because the judging captures are taken after the round.

## Rounds

| round | start (UTC) | end (UTC) | what changed | USD | letter mapping | axes better | axes worse | scores A and B (visual_quality / character_appeal / color_readability) | the new round's three gaps | kept |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2026-09-29T00:24:45Z | 2026-09-29T00:37:00Z | the look before the round | 0 | A = round 0 (only set) | — | — | | | yes |
