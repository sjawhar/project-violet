# Technique B, `land` (Phase 1 bake-off glow-up, THROWAWAY)

Part of the Violet workstream's full technique-B pass across all seven animations, per
[glow-up.md](../../../../../docs/bakeoff/glow-up.md)'s rule that the winning technique (B, frame-by-frame
painted sprites — [technique-trial.md](../technique-trial.md)) goes through every animation. This
record covers `land` only. Pipeline, prompts, calibration and provenance conventions follow
`technique-trial.md`'s `run` trial exactly, adapted per the glow-up task's per-animation rules.

## The animation

`assets/bakeoff/protagonist/rig-src/anims.py`'s `A["land"]`: `duration=0.25`, `loop=False` — plays once
and holds its last frame (`docs/bakeoff/character-rig.md`: `land`, like `jump`/`fall`/`double_jump`/
`dash`, plays once and holds). The rig's own keyframes (`LAND` list, `squat()`): a deep impact crouch
already partway in at `t=0` (`d=34`), deepening to its lowest point (`d=40`) across `t=1/30..2/30`
(0.033-0.067 s), then steadily straightening back up, reaching fully upright (`d=0`) by `t=0.25` — the
held final pose is standing, not crouching.

## Frame count and timing

**3 frames, at `t = 0.05, 0.15, 0.25`** — roughly 12 fps-equivalent spacing (0.1 s/0.083 s holds) across
the 0.25 s duration, per the glow-up task's own "land 3" example. Three frames is enough to read the
move's three beats at a glance (impact → recovering → standing) without over-spending on a 0.25 s
animation with only three visually distinct beats in the rig itself. The third frame is the held final
pose (standing), matching the rig's own hold-on-last-frame behavior.

| # | t (s) | Pose |
|---|---|---|
| 0 | 0.05 | Impact crouch: the deepest point of the landing squash — lowest point of her whole body, both feet flat and planted, torso folded forward, arms swung forward for balance. |
| 1 | 0.15 | Recovering: partway back up from the crouch, knees still bent but straightening, torso uprighting, arms coming back toward her sides. |
| 2 | 0.25 | Standing, held: fully upright, calm, neutral stance — the pose the animation holds until the next state (e.g. `idle`) takes over. |

## Anchoring

`land` is a ground-contact animation throughout (impact crouch through recovery to standing — both feet
stay planted per `anims.py`'s comment, "grounded exactly by ground.py"), so it uses the same scheme as
`run`'s own grounded frames, not the airborne head-position match used for `jump`: each frame's own
`sole_y` (lowest alpha row) anchors to the shared ground line, and `head_x`/`head_y` are recorded for
consistency with the schema but aren't matched against technique A (no root-motion matching needed for
a purely grounded, non-traveling animation).

## Calibration

Reused the run trial's own `RIG_PER_RAW = 1.128227381210675` unchanged — not re-derived — per the glow-up
task's calibration rule ("one shared scale... reuse the trial's `rig_per_raw` approach... so every
animation is the same size as the run"). `trial-b/finalize_anim.py land --mode grounded --nframes 3`
(generalizes `finalize_frames.py`'s trim/scale/anchor logic to any held animation) trims each frame's
body+scarf pair to their shared alpha>8 bbox union, rescales both by that one factor, and writes
`frames/land-finalize-record.json`.

## Generation

Same two-layer pipeline as the run trial: for each frame, (1) her **body without the scarf**
(`--input` the approved turnaround, `assets/bakeoff/protagonist/concept/violet-turnaround.png`, plus
`trial-b/frames/run-body-00.png` as a second style/proportion anchor), gpt-image-2, quality high,
1024×1024, `--background transparent`; (2) the **scarf alone** on transparent (`--input` that frame's
own generated body, plus `assets/bakeoff/protagonist/parts/scarf1.png` for the neutral-gray color).

Prompt scaffold reused word-for-word from the run trial's STYLE and (grounded) FRAME wrapper text,
strengthened after `jump`'s repeated background-vignette drift (see below) with an explicit "zero
pixels painted outside her own silhouette... no glow, no halo... no dark or light background tint of
any kind" clause; the scarf prompt gained an explicit "painted as ONE single continuous opaque flowing
shape (never several overlapping or stacked semi-transparent copies)" clause, the run trial's own
documented scarf-ghosting defect (frames 1 and 5).

### Calls and rejections

| Frame | Body calls | Rejected (why) | Scarf calls | Rejected (why) |
|---|---|---|---|---|
| 0 (impact crouch) | 1 | 0 | 1 | 0 |
| 1 (recovering) | 1 | 0 | 1 | 0 |
| 2 (standing, held) | 1 | 0 | 1 | 0 |
| **Total** | **3** | **0** | **3** | **0** |

**6 `gen image` calls total, 0 rejected.** `land` had none of `jump`'s background-vignette problem —
plausibly because none of its poses read as a dramatic mid-air "hero" silhouette (see `jump.md`'s own
honest-read section for the pattern observed there).

### Spend estimate

6 calls × ~$0.22/call (`docs/bakeoff/shared-costs.md`'s measured rate) = **~$1.32 est.**

## QA / honest read of frame consistency

Reviewed every body and scarf frame at full size (montage) before finalizing:

- **Style/design/proportions:** consistent with the run trial and with `jump`'s frames — same palette,
  hood/robe/sash silhouette, visible eye/brow/nose/mouth every frame, same child-like proportions. No
  off-model drift.
- **Pose read:** the three frames read clearly as impact → recovery → standing at a glance, both at
  full size and mentally scaled to ~100 px (checked via the montage's relative proportions; frame 0's
  low crouch vs. frame 2's tall standing silhouette differ enough in overall height/shape that they're
  distinguishable even small).
- **Scarf:** all three scarf frames are single, opaque, continuous neutral-gray shapes — no stacked/
  ghosted copies, no color drift from neutral gray.
- **Ground/scale alignment:** all three frames' soles land on the same measured ground line (via
  `sole_y`) and share the one `RIG_PER_RAW` calibration factor with `run` and `jump`.

## What the integrator needs

- `frames/land-body-NN.png` / `frames/land-scarf-NN.png` (`NN` = 00-02), already trimmed/rescaled.
- `frames/land-finalize-record.json`: per-frame `sole_y`, `head_x`, `head_y`, `rig_per_raw`,
  `anchor_mode: "grounded"` — place each frame the same way `run`'s own row-building does (`sole_y` onto
  the shared ground line, horizontal placement by whatever convention the assembled sheet uses).
- Held-animation semantics: frame 2 (t=0.25) is the pose to hold indefinitely once `land` finishes
  playing, same as the rig's own last-keyframe hold.
- No cross-animation root-motion matching was needed for `land` (see Anchoring above), so its
  finalize record has no `target_head_x`/`target_head_y` fields, unlike `jump`'s.
