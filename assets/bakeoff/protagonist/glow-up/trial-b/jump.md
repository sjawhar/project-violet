# Technique B, `jump` (Phase 1 bake-off glow-up, THROWAWAY)

Part of the Violet workstream's full technique-B pass across all seven animations, per
[glow-up.md](../../../../../docs/bakeoff/glow-up.md)'s rule that the winning technique (B, frame-by-frame
painted sprites — [technique-trial.md](../technique-trial.md)) goes through every animation. This
record covers `jump` only. Pipeline, prompts, calibration and provenance conventions follow
`technique-trial.md`'s `run` trial, adapted per the glow-up task's per-animation rules — most notably
`jump`'s airborne head-position anchoring against technique A, in place of `run`'s ground-line anchoring.

## The animation

`assets/bakeoff/protagonist/rig-src/anims.py`'s `A["jump"]`: `duration=0.5`, `loop=False` — plays once
and holds its last frame (`docs/bakeoff/character-rig.md`). Three explicit rig keyframes: `t=0` a
grounded anticipation crouch (hips down, torso leaned back -24°, arms swept back/down, legs bent in a
"squat" that keeps the soles planted); `t=0.12` an explosive extension (hips translated up +12 from
setup, legs nearly straight, arms thrown up to ~140°/120°) — the toe-off/push-off instant; `t=0.3` and
`t=0.5` both hold the identical `RISE` pose (knees bent in a loose tuck, arms out and up at the sides,
slight backward torso lean) — the rig's own held airborne "rising" state.

## Frame count and timing

**5 frames, at `t = 0.0, 0.1, 0.2, 0.3, 0.4`** — 10 fps-equivalent, inside the task's "roughly 8-12 fps"
guidance and matching its own "jump 5" example. This samples the rig's three real keyframes plus two
in-between transitional beats (`t=0.1` near the push-off extension, `t=0.2` transitioning from
extension into the rise), so the read is: crouch → push-off extension → transitioning → rising tuck →
rising tuck held. The rig holds an *identical* `RISE` pose from `t=0.3` through `t=0.5`, so frame 4
(`t=0.4`) is the held final pose, matching frame 3 in silhouette but independently painted (same
approach the run trial's own "mirrored" frames took, and found to be not a defect — see
`technique-trial.md`'s "Honest read of frame consistency").

| # | t (s) | Pose |
|---|---|---|
| 0 | 0.0 | Anticipation crouch: deep, compressed, weight sinking, arms swept back, coiled to launch. |
| 1 | 0.1 | Push-off extension: legs driving straight, body stretched tall, just leaving the ground, arms swinging up in front. |
| 2 | 0.2 | Transitional rise: climbing, legs beginning to bend/tuck, arms opening out to the sides. |
| 3 | 0.3 | Rising tuck (held): knees pulled up in a loose tuck, arms out and slightly up, calm airborne silhouette. |
| 4 | 0.4 | Same rising tuck, held an instant later — the pose the animation holds until it hands off (e.g. to `fall` or `double_jump`). |

This progression keeps `jump` visually distinct at every beat from `fall` (body opening, arms up and
out, descending) and `double_jump` (a quick knee-tuck snap with the scarf flaring, no rotation) — the
critic's round-0 gap for technique A was exactly that these three read as one pose; `jump`'s five frames
never share a silhouette with either sibling animation's poses (confirmed against `fall.md`/
`double_jump.md`'s own pose tables, painted by a sibling lane in the same workstream).

## Anchoring

`jump` is airborne throughout — the crouch is anticipation on the ground, but per the glow-up task's own
classification ("Airborne frames (jump, fall, double_jump, and dash if airborne)... Place them so the
head centroid matches technique A's head position in the same animation at the same time"), every one
of `jump`'s frames anchors by head position against technique A, not by a ground line.

**Measurement.** For each of the 5 sample times, technique A's own head-slot world centre was read
directly via FK (`spinerig.render._placements()`, not a rendered raster), then converted to canvas
space against the fixed `REFERENCE_BOX` from `rounds.md`'s "Fixed layout" (`x=-763.6, y=-40.0,
width=1316.9, height=1434.7`) at `scale=1.0, margin=0` — i.e. raw rig units, y-down, in the same
coordinate space every technique's frames are ultimately composited into (not an arbitrary per-call
`spinerig render` auto-bounding-box, which would only be self-consistent within one call). This is the
scheme `finalize_anim.py --mode airborne` implements (`technique_a_head_targets()`), matching the
approach used for `fall`/`double_jump` in the same workstream so the integration step reads every
animation's finalize record the same way.

Technique A's own head position at each sample time (raw rig units, `REFERENCE_BOX`/scale=1.0/margin=0):

| t | target_head_x | target_head_y |
|---|---|---|
| 0.0 | 726.72 | 558.84 |
| 0.1 | 730.19 | 500.75 |
| 0.2 | 734.45 | 503.23 |
| 0.3 | 739.45 | 514.52 |
| 0.4 | 739.45 | 514.52 |

(t=0.3 and t=0.4 are identical because A's rig holds the same `RISE` keyframe across both times.) Each
of B's frames records its own `head_x`/`head_y` (alpha-weighted centroid of the top ~18% of its own
trimmed+rescaled bbox — the same heuristic `run`'s `head_x` used, extended to also return `y`) plus
these `target_head_x`/`target_head_y` values, so a build step can place frame `i` at
`dx = (target_head_x - head_x) * canvas_scale`, `dy = (target_head_y - head_y) * canvas_scale` — no
ground line anywhere in `jump`.

## Calibration

Reused the run trial's own `RIG_PER_RAW = 1.128227381210675` unchanged — one shared scale across every
animation, per the glow-up task's rule, not re-derived per animation. `trial-b/finalize_anim.py jump
--mode airborne --nframes 5 --times 0.0 0.1 0.2 0.3 0.4` trims each frame's body+scarf pair to their
shared alpha>8 bbox union, rescales both by that one factor, and writes
`frames/jump-finalize-record.json`.

## Generation

Same two-layer pipeline as the run trial: for each frame, (1) her **body without the scarf** (`--input`
the approved turnaround plus one of the trial's own frames as a style/proportion anchor — `run-body-00.png`
for most frames, `jump-body-00.png` itself for two retries, see below), gpt-image-2, quality high,
1024×1024, `--background transparent`; (2) the **scarf alone** on transparent (`--input` that frame's
own generated body, plus `parts/scarf1.png` for the neutral-gray color).

Prompt scaffold reused from the run trial's STYLE text word-for-word. The FRAME wrapper was adapted for
airborne poses (dropped the grounded "same distance... to the ground line" continuity clause, which
doesn't hold for a rising jump; added "she is airborne... keep her at the exact same body scale... never
bigger or smaller" instead). The scarf prompt kept the run trial's own text, with an added explicit
"painted as ONE single continuous opaque flowing shape (never several overlapping or stacked
semi-transparent copies)" clause addressing the run trial's own documented scarf-ghosting defect.

### The vignette problem, and how it was fixed

Three of `jump`'s five body-frame poses (frames 1, 2 in one instance, and 3) repeatedly generated with a
**dark radial vignette/glow painted into the "transparent" background** instead of a clean transparent
canvas — confirmed a real pixel-level defect, not a preview artifact, by checking the alpha channel
directly (`Image.getchannel("A").histogram()`): the vignetted frames had a large area of *partial*, non-
near-zero alpha (a soft glow halo) rather than a crisp cutout's small antialiasing band. This did not
correlate with which FRAME-wrapper wording was used (both the original and a "no glow/no halo/no radial
light" reinforced wrapper produced it); it correlated with the **pose's own dramatic-sounding phrasing**
("explosive push-off... maximum vertical extension... reaching high overhead", "the high point of a
jump's rise... fully airborne... no part of her touching anything") — plausibly the model reading these
as movie-poster/action-hero framing cues. The fix that worked, applied to all three failing frames:
rewriting the pose text into plain, mechanical, non-cinematic language (dropping words like "explosive",
"propelling", "high point", "reaching overhead") and, for frame 3, swapping the style anchor from
`run-body-00.png` to `jump-body-00.png` (a frame from this same animation that had already generated
cleanly). Frame 1 needed 3 rejections before a plain-language rewrite succeeded; frame 3 needed 2.

### Calls and rejections

| Frame | Body calls | Rejected (why) | Scarf calls | Rejected (why) |
|---|---|---|---|---|
| 0 (crouch) | 1 | 0 | 1 | 0 |
| 1 (push-off extend) | 4 | 3 — dark vignette/glow painted into the background instead of transparent, on both the original and a reinforced "no glow" wrapper; fixed by rewriting the pose text plainly (no "explosive"/"reaching overhead" wording) | 1 | 0 |
| 2 (transitional rise) | 1 | 0 | 2 | 1 — same vignette defect on the first scarf call (using the clean `jump-body-02.png` as its own pose reference); fixed by adding an explicit "no vignette/no glow... exactly like the reference swatch's own plain transparent background" clause to the scarf prompt |
| 3 (rising tuck, held) | 3 | 2 — same vignette defect twice, including after the "isolated game sprite/sticker" reinforcement; fixed by plain-language pose text + swapping the style anchor to `jump-body-00.png` | 1 | 0 |
| 4 (rising tuck, held, later) | 1 | 0 | 1 | 0 |
| **Total** | **10** | **5** | **6** | **1** |

**16 `gen image` calls total, 6 rejected, 10 kept.**

### Spend estimate

16 calls × ~$0.22/call (`docs/bakeoff/shared-costs.md`'s measured rate) = **~$3.52 est.** (~$2.20 kept
+ ~$1.32 rejected).

## QA / honest read of frame consistency

Reviewed every body and scarf frame at full size before finalizing (in addition to the vignette
rejections above):

- **Style/design/proportions:** consistent across all 5 kept frames — same palette, hood/robe/sash
  silhouette, visible eye/brow/nose/mouth every frame, same child-like proportions as the turnaround and
  the run trial. No off-model drift beyond the background defect above.
- **Pose distinctness:** all 5 read as clearly different beats at a glance — crouch (compressed, low)
  vs. extension (tall, legs straight) vs. transitional (legs bending, arms opening) vs. rising tuck
  (knees up, calm). Frames 3 and 4 are intentionally near-identical (the rig's own held pose), but each
  was independently painted, not duplicated.
- **Scarf:** all 5 scarf frames are single, opaque, continuous neutral-gray shapes — no stacked/ghosted
  copies (the run trial's frames 1/5 defect), no color drift from neutral gray.
- **Root motion:** frame 0 (grounded crouch) sits noticeably lower than frames 1-4, and frame 1 (push-off)
  sits highest among the non-held frames per A's own head-position measurements above (t=0.1's
  `target_head_y=500.7` is the smallest, i.e. highest, value in the table) — consistent with a real
  launch-then-settle root motion, not a monotonic climb (A's own rig relaxes the hips slightly between
  the push-off extension and the held rise, a stylized "release" the painted frames should match, not a
  literal record of ever-increasing height, since that's supplied separately by the game's physics).

## What the integrator needs

- `frames/jump-body-NN.png` / `frames/jump-scarf-NN.png` (`NN` = 00-04), already trimmed/rescaled.
- `frames/jump-finalize-record.json`: per-frame `head_x`, `head_y`, `target_head_x`, `target_head_y`,
  `rig_per_raw`, `anchor_mode: "airborne_head"`, `t`. No `sole_y` field — `jump` never touches the
  ground line.
- Held-animation semantics: frame 4 (t=0.4) is the pose to hold indefinitely once `jump` finishes
  playing, until the state machine hands off to `fall`/`double_jump`/etc.
- The vignette failure mode above is worth watching for in any remaining painted frames across the
  workstream (`dash`, `idle`) that use dramatic/action pose language.
