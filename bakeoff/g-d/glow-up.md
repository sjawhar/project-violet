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
| 0 | 2026-09-29T00:24:45Z | 2026-09-29T00:37:00Z | the look before the round | 0 | A = round 0 (only set) | — (nothing to compare) | — | A: 2 / 2 / 2 | 1. red walls render peach (~255,175,115), on the sandstone hue, in 2 of 3 shots; 2. Violet is lost: hidden behind a wall in A-4, brown robe on tan mesa in A-3, no rim light or detail; 3. the world looks like greybox: one strata texture everywhere, sharp cuboids, repeated spikes, a horizon seam at y≈640, an empty sky, saturated low-poly mesas, black slivers ([critic.md](glow-up/round-00/critic.md)) | yes |
| 1 | 2026-09-29T00:41:00Z | 2026-09-29T01:18:00Z | Gap 3 (the world looks like greybox), picked as the one expected to lift the look most; gap 1 (red reads peach) and gap 2 (Violet lost) left for later rounds, and gap 2's "scale her up 1.5x" is the lead's Violet workstream, not this lane. Changes, all in `art/kit_art_3d.gd`: a painted golden-hour sky (`art/sky.png`, one `gen image` call) on a quad at z −165 that follows the camera; the sand plane runs back to it and fog ends at its colour, so the horizon seam is gone; flapping birds; a pale horizon layer of mesas and dunes 60–100 m back; the far and mid props hazed toward the horizon colour (35% and 15%) so they sit behind the play plane; dark acacia and saguaro silhouettes in the foreground, kept below the walking surface and off the pits; tiles darken toward violet with depth, and every other tile is turned round; two weak shadowless fill lights so the pit side faces are no longer black. Nothing expensive to draw: one extra textured quad, 5 birds of 2 boxes each, about 20 extra meshes, 2 directional lights without shadows. | about 0.22, estimated (1 gpt-image-2 call, 1536x1024, quality high, at the $0.22 per high-quality call measured in docs/bakeoff/shared-costs.md; gen logs no usage) | A = round 0 (kept), B = round 1 (new) | visual_quality | color_readability | A: 2 / 2 / 3; B: 3 / 2 / 3 | 1. the brushy painted sky clashes with the flat-shaded low-poly ground: two styles pasted together; 2. haze washes the play layer's platform tops into the dunes, and the flat navy foreground silhouettes are the darkest mass, cropped, and cover the main platform in B-3; 3. Violet still small, grey-brown, no rim light, lost on a pale mesa (B-2) and behind the pillar (B-4); strata repeat; red pillars salmon ([critic.md](glow-up/round-01/critic.md)) | yes |
| 2 | 2026-09-29T01:20:00Z | 2026-09-29T01:38:00Z | Gap 2 (the layering hurts the play layer), picked because it is what made color_readability worse in round 1 and it is fixable in this lane; gap 1 (sky and ground in two styles) left for a later round; gap 3 is mostly Violet herself (the lead's workstream), except her surroundings. Changes, in `art/kit_art_3d.gd`: the near backdrop (mid and far props, the sand behind the level) is hazed toward a dusty rose one value step darker than the sunlit sand tops instead of toward the bright horizon, and the sand plane behind the level is that darker tone too, so platform edges read against what is behind them; only the horizon layer still fades to the horizon colour; the dark foreground silhouettes are removed; the tiles' depth tint is gentler (5% per cell, was 8%). Nothing new to draw; 20-odd foreground meshes fewer. | 0 (no generation) | A = round 2 (new), B = round 1 (kept) | none | visual_quality | A: 2 / 2 / 3; B: 2 / 2 / 3 | 1. one depth plane: no dark soft foreground, and the cream platform tops (luma ~220) still melt into the haze (~217); 2. one strata texture tiled on every block, sharp box corners, faceted low-poly mesas with a repeated band; 3. Violet small, grey, noisy, no face, same grey-mauve as the sand shadows, stiff arms ([critic.md](glow-up/round-02/critic.md)) | no: reverted to round 1 |
| 3 | 2026-09-29T01:42:00Z | 2026-09-29T02:00:00Z | Gap 3 (peach red pillars; Violet hidden and blending in). Picked because red has been called peach in every critique so far and Violet disappearing behind a wall is the worst read in the set; gap 1 (foreground) and gap 2 (haze, strata) left for later. Of gap 3, Violet's face, arms and size are the lead's workstream, so this round only changes how she reads in the world. Changes, in `art/kit_art_3d.gd`: the tag-blocks' own lights no longer light the blocks (visual layer 2, excluded from their cull mask), which is what washed active red to peach; red is a crimson (#c4162a) that renders true red under the warm sun, and active glow is 0.3 (was 0.5); Violet is drawn 0.6 m in front of the play plane, so she stays in front of a wall she passes through; a dark 5 cm outline behind her gives her a value break from sand, sky and mesa. Nothing expensive: 14 extra unshaded sprites. | 0 (no generation) | | | | | | |
