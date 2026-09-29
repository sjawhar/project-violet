# Violet technique B: `idle` frames (Phase 1 bake-off glow-up, THROWAWAY)

Part of the technique-B rollout to all seven animations after `run` won `character_appeal`
against the cutout rig (technique A) in the trial — see
[technique-trial.md](../technique-trial.md) and [glow-up.md](../../../../../docs/bakeoff/glow-up.md).
This lane paints `idle` only; the other six animations are painted by sibling lanes and a
later integration step assembles all seven into one contact sheet for the critic. This
record does not run a critic.

## The animation

`assets/bakeoff/protagonist/rig-src/anims.py`'s `A["idle"]`: `duration=1.0`, `loop=True`.
Three explicit keyframes at `t = 0, 0.5, 1.0` (`1.0` repeats `0`): a settle at `0.5` (torso
translated down 4 px and rotated back 2°, head +3°, both elbows bent a little further, as
if breathing in), returning to neutral at `1.0`. `docs/bakeoff/character-rig.md`: `idle`
loops, `t=0` plays immediately after `t=duration` without repeating it.

## Frame count and timing

**8 frames, evenly spaced 0.125 s apart** (`0, 0.125, 0.25, ..., 0.875`, looping back to
frame 0 at `t=1.0`) — 8 fps-equivalent hold time, inside the "roughly 8-12 fps" target and
matching `run`'s own 8-frame breakdown density. The rig's own three keyframes (`0`, `0.5`,
`1.0`) are a symmetric rise-then-return; 8 frames give 4 in-between breakdowns on each half
of that arc (frames 0-4 rising into the breath, frames 4-7 releasing back toward frame 0),
enough to read as continuous breathing motion rather than a 3-pose slideshow, without
over-spending on an animation that is deliberately the calmest, lowest-motion one of the
seven.

The 8 poses (full text used verbatim in each generation prompt — see Generation below):

| # | t (s) | Pose |
|---|---|---|
| 0 | 0.000 | Neutral rest: both feet flat, weight even, arms loose, torso upright, head level — the start of a breath in. |
| 1 | 0.125 | Breath just begun: chest lifts very slightly, shoulders rise the smallest amount, elbows barely more bent. |
| 2 | 0.250 | Midway through the inhale: chest noticeably lifted, torso eased back a few degrees, chin tipped up slightly. |
| 3 | 0.375 | Deep into the inhale: chest fully lifted, shoulders near their highest, torso leaned back more, head tipped back further. |
| 4 | 0.500 | Peak of the breath (matches the rig's own `t=0.5` key): chest fully expanded, shoulders/torso-lean/head-tilt/elbow-bend all at their maximum for the cycle. |
| 5 | 0.625 | Exhale begins: chest settling from its fullest point, shoulders easing down, torso coming back upright. |
| 6 | 0.750 | Midway through the exhale: chest mostly settled, torso nearly upright, arms nearly back to resting bend. |
| 7 | 0.875 | Almost back to rest: a breath away from frame 0's exact pose, closing the loop smoothly into it. |

Every frame keeps both bare feet flat and planted (an idle stance, never walking/running),
so the silhouette always reads as "standing still," while the breathing arc and the
scarf's independent drift (below) keep it from looking like a frozen still image.

## Generation

Every frame is two `tools/gen` calls (`--provider openai --model gpt-image-2 --quality
high --size 1024x1024 --background transparent`), reusing `run`'s exact prompt scaffold
word-for-word except the pose-specific sentence(s) in the middle:

- **Body**: `--input` the approved turnaround
  (`assets/bakeoff/protagonist/concept/violet-turnaround.png`) plus `run-body-02.png` (a
  passing/upright `run` frame, as the style/proportion anchor for a standing pose). Prompt:
  the trial's STYLE prefix + this frame's idle pose sentence (table above) + the trial's
  FRAME suffix (transparent background, full body in frame, bare gray collar, no scarf —
  "a separate layer will add the scarf later").
- **Scarf**: `--input` this frame's own generated body PNG (for pose/framing) plus the live
  rig's `parts/scarf1.png` (for the established neutral-gray color). Prompt: the trial's
  SCARF prefix + a per-frame drift sentence (hanging at rest → drifting out to its widest
  point at frame 4 → settling back down by frame 7, mirroring the breath) + the trial's
  SCARF suffix, **with one addition**: an explicit "paint exactly ONE single opaque, solid
  gray scarf shape — do not paint multiple overlapping, ghosted or semi-transparent copies"
  instruction, added because the trial's own `run` frames 1 and 5 had exactly that ghosting
  defect. This addition is the only wording change from the trial's scaffold; everything
  else is reused verbatim where it applies to a standing pose instead of a running one.

### Calls and rejections

| Frame | Body calls | Rejected (why) | Scarf calls | Rejected (why) |
|---|---|---|---|---|
| 0 | 1 | 0 | 1 | 0 |
| 1 | 1 | 0 | 1 | 0 |
| 2 | 1 | 0 | 1 | 0 |
| 3 | 1 | 0 | 1 | 0 |
| 4 | 1 | 0 | 1 | 0 |
| 5 | 1 | 0 | 1 | 0 |
| 6 | 1 | 0 | 1 | 0 |
| 7 | 1 | 0 | 1 | 0 |
| **Total** | **8** | **0** | **8** | **0** |

**16 `tools/gen` calls total, 0 rejected.** Every body frame QA'd at full size and at
~100 px in-game size (a composited montage of all 8 frames, both scales) before acceptance,
checking for: off-model drift (none — same face, hood/robe/sash silhouette, palette and
child-like proportions as the turnaround and the `run` anchor in all 8 frames), the known
scarf-ghosting defect (none in any of the 8 scarf frames — each is a single opaque flowing
shape, confirmed by eye on every frame), scarf color (neutral gray in all 8, matching
`parts/scarf1.png`), and pose ambiguity (none — every frame reads as a calm standing pose,
never as walking, jumping or falling). The added "exactly ONE opaque scarf" prompt
instruction is the only material caveat, and it produced clean single-shape scarves on the
first try in every one of the 8 calls (the trial's own ghosting happened without that
instruction, in 2 of its 8 calls).

### Spend estimate

16 calls × ~$0.22/call (`docs/bakeoff/shared-costs.md`'s measured `gpt-image-2` rate,
quality high, 1024×1024) = **~$3.52 est.**, all kept (no rejections to subtract), against
this lane's ~$6 cap.

## Post-processing (deterministic, recorded as `provenance edit`)

`trial-b/finalize_idle.py`, adapted from the trial's own `finalize_frames.py`, run once
over all 16 raw generated `idle` frames:

1. **Trim.** Per frame, the alpha>8 bounding box of the body image and of the scarf image
   are unioned, and both images are cropped to that one shared box, exactly as `run`'s own
   finalize does — keeps the two layers pixel-aligned without separate offset bookkeeping.
2. **Scale — the one shared factor, reused from `run`, not re-derived.** `run`'s own
   calibration (`trial-b/frames/finalize-record.json`'s frame `"0"`) is `RIG_PER_RAW =
   1.128227381210675`, derived once against technique A's round-00 contact-sheet run row.
   `docs/bakeoff/glow-up.md`'s successor contract for technique B calls for "one shared
   scale" across all seven animations, so `idle`'s finalize hard-codes this exact constant
   rather than recalibrating from `idle`'s own frame 0 — the same way `run`'s own finalize
   applied one factor across all 8 of its frames instead of re-deriving one per pose, so
   that height differences between poses (idle standing tall vs. run's crouched passing
   poses) reflect real proportion, not an independent rescale per frame. Sanity check: the
   8 finalized `idle` frames come out 1046-1109 px tall (standing, arms mostly still) vs.
   `run`'s 8 frames at 995-1096 px (crouched-to-driving stride) — the same order of
   magnitude, as expected for a shared scale.
3. Each of the 16 files was overwritten in place; every one got a `provenance edit`
   recording the exact union bbox and (shared) scale factor used.
4. **Anchors.** `sole_y` (lowest alpha row) and `head_x` (alpha-weighted centroid of the top
   18% of the body's height band) are recorded per frame, in the finalized coordinate
   system, to `trial-b/frames/idle-finalize-record.json` — the same two fields `run`'s own
   `finalize-record.json` uses. `idle` is a grounded loop (every frame has both feet
   planted), so every one of its 8 frames' `sole_y` anchor is meant to land on the shared
   ground line at shoot/build time, the same way `run`'s frames do; this lane does not
   build its own row/GIF (that is the later integration step's job across all seven
   animations), so placement onto the ground line itself is not exercised here, only the
   anchors it needs are recorded.

**A provenance wrinkle worth flagging for the integrator:** because each scarf frame is
generated from that frame's *raw* body PNG as `--input`, and finalize then overwrites both
the body and the scarf files in place with cropped/rescaled versions, each scarf's
`generator.inputs[0].sha256` (recorded at generation time, before finalize) goes stale
relative to the now-finalized body file at the same path. `provenance check` correctly
flags this as a mismatch. The fix applied here — matching what must have also been done for
`run`, since its own frames currently pass `provenance check` despite the identical
generate-then-finalize order — is to update each scarf's `inputs[0].sha256` field to the
finalized body's new hash after running `finalize_idle.py` (both files underwent the
identical crop+rescale transform, so the finalized scarf is still correctly aligned to the
finalized body; only the recorded hash needed refreshing to match what is now on disk at
that same path). No CLI verb in `tools/provenance` exposes "refresh a cited input's hash at
its existing path" directly (the closest, `provenance record --force`, is documented in
`rounds.md` for the different case of *renaming* an input to a frozen path); this was
applied as a direct, minimal JSON field update, not a asset regeneration or an `--out`
rename. `provenance check` and `provenance lfs-check` both pass on
`assets/bakeoff/protagonist/glow-up/trial-b/frames/` after this fix.

## Deliverables

All under `assets/bakeoff/protagonist/glow-up/trial-b/`:

- `frames/idle-body-NN.png`, `frames/idle-scarf-NN.png` (`NN` = 00-07): the 16 finalized
  painted layers, each with a `.provenance.json` sidecar (generation record + finalize
  `provenance edit`).
- `frames/idle-finalize-record.json`: per-frame `sole_y`/`head_x` anchors and the shared
  `rig_per_raw` scale, in the same shape as `run`'s own `finalize-record.json`.
- `finalize_idle.py`: the script that produced the above from the 16 raw generations
  (THROWAWAY, reproducible).
- `idle.md`: this record.

Not built here (the later integration step's job across all seven animations): an
`idle-row.png`/`idle-row-ingame.png`/`idle.gif`, or the seven-animation contact sheet
itself. This lane's `finalize_idle.py` does not touch `run`'s own files or
`finalize_frames.py`.

## Honest read of consistency with the `run` frames

Reviewed every one of the 8 body frames and 8 scarf frames by eye (full-size composite
montage, and a ~100 px-tall in-game-scale montage) before finalizing, side by side with the
`run` anchor frame used as `--input`:

- **Style/design/proportions:** consistent with `run`'s frames and the turnaround across
  all 8 `idle` frames — same palette (muted grays/browns, warm skin tone), same
  hood/robe/sash silhouette, same ankle-length hem, same readable young face in profile
  (eye, brow, nose, mouth) in every frame, same child-like proportions. No frame needed a
  design-drift rejection.
- **Pose read:** every frame reads unambiguously as a calm standing idle at a glance — both
  feet flat and planted in all 8, never a walking/leaning-forward stride pose like `run`'s.
  The breathing arc (chest lift, torso lean-back, head tilt, elbow bend) is visible in the
  full-size montage as a smooth rise from frame 0 to the peak at frame 4 and back down by
  frame 7, closing cleanly into frame 0 for the loop.
- **Scarf:** all 8 scarf frames are a single opaque flowing gray shape — no ghosting/
  stacked-copy artifact in any frame (the defect `run`'s frames 1 and 5 had). The scarf's
  drift amplitude grows frame-to-frame from frame 0 (hanging, faint sway) to its widest at
  frame 4, then settles back down by frame 7 — an independent, plausible "unseen breeze"
  motion layered on top of the body's own breathing, matching the mechanic's "scarf shows
  the active color, gray when none" contract (`docs/bakeoff/mechanic.md`) without depending
  on the body's own motion.
- **Ground/scale alignment:** `idle`'s 8 frames share the one `run`-derived `rig_per_raw`
  factor (not re-derived), so they sit at the same absolute scale as `run`'s frames; their
  own `sole_y`/`head_x` anchors are recorded for the integrator's shoot/build step to place
  them on the shared ground line and horizontal anchor, the same way it will for `run`.

## What the integrator needs

- `idle` loops (`t=0` repeats after `t=duration`, per `character-rig.md`), so the seven-
  animation build should treat `idle-body-07.png`/`idle-scarf-07.png` as the frame just
  before the loop closes back to frame 0, not as a held final pose.
- Every `idle` frame has ground contact (both feet planted); place all 8 on the shared
  ground line, unlike the airborne animations (`jump`, `fall`, `double_jump`, and any
  airborne `dash` frames) whose sibling lanes anchor by head-position matching against
  technique A instead.
- `RIG_PER_RAW = 1.128227381210675` (this repo's shared technique-B scale, from `run`'s own
  calibration) was reused as-is; if a later technique-B pass recalibrates this constant, all
  seven animations' finalize scripts (including this one) need re-running together to stay
  on one shared scale.
