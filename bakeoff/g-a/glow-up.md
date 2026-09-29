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
| 1 | 2026-09-29T00:41:38Z | 2026-09-29T01:07:00Z | Gap 1, the terrain (Violet's grey and the walls are later gaps). A terrain shader on every stone cell (art/terrain.gdshader): open sides eroded by 6-26 px of noise, open top corners rounded, the rock mass darkening with a smooth distance-to-air field so the foreground reads as a dark mass under a lit lip, a warm rim on the sunlit top and sides, broad value variation. A soft contact shadow on the backdrop beside every open rock face, and gloom rising out of each pit over the spikes. Collision unchanged. Draw cost: one extra fragment shader (about 7 value-noise lookups per pixel) on the roughly 270 terrain sprites, plus about 60 vertex-coloured shadow quads; no extra passes or render targets. | 0 (no generation calls) | B = round 01 (A = round 00) | visual_quality, color_readability | none | A (round 00): 2 / 2 / 3; B (round 01): 2 / 2 / 3 | 1. lighter rectangular halo strips beside every block, blotchy dark smears inside blocks read as dirt; 2. pits still rectangular windows onto a different painting with vertical seams, one repeated spike sprite on a flat navy band, blocks still square brick boxes; 3. Violet unchanged: mid-grey robe, no rim light, stiff cloth, red scarf vanishes against the red wall. Full text: [critic.md](glow-up/round-01/critic.md) | yes |
| 2 | 2026-09-29T01:13:38Z | 2026-09-29T01:28:00Z | Gap 1 of round 01 (the halo strips and interior smears that round 1 introduced; gap 3 is mostly a Violet change, gap 2 is next). The contact shadow now starts under the rock instead of at the cell edge, so the eroded margin shows the same gradient and the lighter strips are gone. The rock's darkening follows a new field: the cheapest path up to open air (up or diagonally up cost 1, sideways 2, never down, capped at 5 cells), which gives a smooth top-to-bottom ramp with no dark columns under raised blocks and no blotches in big blocks; the painted value variation is broader and weaker. Ambient occlusion darkens the ground at the foot of every block that rises out of it. Collision unchanged. Draw cost: unchanged from round 1 (the same terrain shader and shadow quads). | 0 (no generation calls) | | | | | | |

Round 0's capture took 7 min 50 s wall time (00:25:26-00:33:16Z; 3961 frames at 15% of real time, with other lanes shooting at the same time).
