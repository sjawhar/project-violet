# Lane G-A glow-up (THROWAWAY)

THROWAWAY bake-off record of lane G-A's glow-up round, run by the rules in [docs/bakeoff/glow-up.md](../../docs/bakeoff/glow-up.md). This lane's workstream is the painted world and how Violet reads in it; Violet herself (protagonist/, PR #28 at 9b22572d) stays as she is until Sami approves her glowed-up version.

## The bar

Scored against:

- GRIS: https://store.steampowered.com/app/683320/GRIS/
- Planet of Lana: https://store.steampowered.com/app/1608230/Planet_of_Lana/

Named only to find gaps, not to score (direction A, a painted 2D world):

- Ori and the Will of the Wisps: https://store.steampowered.com/app/1057090/Ori_and_the_Will_of_the_Wisps/. A hand-painted forest platformer with deep layered parallax, strong rim light on the character against dark foregrounds, and dense ambient particles.
- Child of Light: https://store.steampowered.com/app/256290/Child_of_Light/. Watercolour-painted 2D worlds with soft washes and a small character who stays readable against busy painted backdrops.

All four links returned HTTP 200 on 2026-09-29. None of their images is downloaded, committed or used for generation.

## Fixed shots

Run from the lane workspace root with no DISPLAY, which gives software rendering under Xvfb (llvmpipe/lavapipe, per scripts/capture-lib.sh). It is the same command and environment every round:

```bash
env -u DISPLAY PATH=/home/agent/.mise/installs/godot/4.7.2-stable:/home/agent/.mise/installs/ffmpeg/9.0.2/.mise-bins:$PATH bash scripts/capture-godot.sh g-a
```

The four stills (`bakeoff/g-a/capture/still-{05,20,40,60}.png`) are copied to `bakeoff/g-a/glow-up/round-NN/`. bakeoff/g-a/capture/ is then emptied again, because the judging captures are taken after the round.

## Rounds

| round | start (UTC) | end (UTC) | what changed | USD | letter mapping (which letter was the new round) | axes better | axes worse | scores A and B (visual_quality / character_appeal / color_readability) | the new round's three gaps | kept |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2026-09-29T00:25:02Z | 2026-09-29T00:34:00Z | the look before the round | 0 | A = round 00 (one set) | n/a | n/a | A: 2 / 3 / 3 | 1. terrain is flat grid rectangles: one stone fill, same sand strip, no edges/corners/contact shadow, pits are pasted panels; 2. red/green walls are flat unlit bars, red value varies, red and green equal luminance (colorblind fail); 3. Violet is muddy unlit grey, no warm rim, sinks into purple trees, thin dark scarf. Full text: [critic.md](glow-up/round-00/critic.md) | yes |

Round 0's capture took 7 min 50 s wall time (00:25:26-00:33:16Z; 3961 frames at 15% of real time, with other lanes shooting at the same time).
