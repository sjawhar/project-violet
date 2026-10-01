# Technique B, `dash` (Phase 1 bake-off glow-up, THROWAWAY)

Part of the full glow-up pass carrying technique B (frame-by-frame painted sprites, winner
of the technique trial, #38) to all seven animations; see
[glow-up.md](../../../../docs/bakeoff/glow-up.md) and
[technique-trial.md](technique-trial.md) (the trial record, `run` only, whose pipeline this
reuses). Session `VioletBDashRunFix`.

## The animation

`assets/bakeoff/protagonist/rig-src/anims.py`'s `A["dash"]`: `duration=0.2`, `loop=False`
(plays once and holds its last frame — `docs/bakeoff/character-rig.md`). Three keyframes:
`t=0` (a partial lean-in: torso -10°, arms swept back ~25-30°, one leg lifting), `t=0.08`
and `t=0.2` (both the same full `DASH` pose: hips -12°, torso -22° hard forward lean, head
+20°, both arms swept back 65-75°, both legs bent and trailing) — so the rig is static
(constant pose) for the whole `[0.08, 0.2]` interval; `t=0.08` and `t=0.2` are visually
identical.

`docs/bakeoff/mechanic.md`: dash is `Shift`, 30 t/s for 0.2 s (6 tiles), gravity suspended
during the dash, **one air-dash per airborne period (resets on landing) but ground dashes
are unlimited** — so dash genuinely happens both grounded and airborne, using the same
animation either way. The rig's own `dash` timeline has **no bone `translate` at all**
(every keyframe in `pose_keys(...)` for `dash` passes an empty translate dict) — the
in-place skeleton pose never encodes a "ground line"; the 30 t/s horizontal (and, for an
air-dash, however-suspended-gravity) motion is entirely the game's own physics translating
the character box, layered on top of this local pose animation.

## Frame count and timing

**3 frames, evenly spaced 0.2/3 ≈ 0.0667 s apart** (`t = 0, 0.0667, 0.1333`, then holds) —
chosen over the example's own suggested count for the same reason `run`'s 8-for-0.6s did:
`0.0667 s ≈ 15 fps`-equivalent hold time is inside the requested 8-12 fps range only if
rounded generously, but 0.2 s at a literal 8-12 fps gives just 1.6-2.4 frames, too few to
show anticipation → burst → held-release as three distinct beats for a move whose whole
*point* is a sudden, felt speed change; 3 frames is the smallest count that still reads as
a real acceleration rather than a 2-frame flicker, and matches the assignment's own
worked example ("dash 3"). Times were chosen evenly across the duration (matching `run`'s
own even-spacing convention) rather than snapped to the rig's own two distinct keyframe
times (0, 0.08) — since the rig holds one constant pose across `[0.08, 0.2]` anyway, frame
1 (`t=0.0667`) and frame 2 (`t=0.1333`) both fall inside or near that same held interval,
so both painted frames legitimately show (slightly different degrees of) the same "full
burst" silhouette, and frame 2 — the last painted key — is the pose that stays held past
the animation's own end, per the assignment's "held animations end on the pose that's
held."

| # | t (s) | Pose |
|---|---|---|
| 0 | 0.000 | Anticipation/coil: torso already leaning forward and down, front leg bent and pushing off, back leg trailing and lifting, both arms beginning to sweep back past the hips, head tilted forward — the instant a fast dash begins. |
| 1 | 0.067 | Peak burst: torso bent into a steep, hard forward lean (much steeper than the running lean), head tucked low and forward, both arms swept sharply back and bent, both legs bent and trailing, body compact and streamlined — an explosive burst of pure horizontal speed. |
| 2 | 0.133 | Held release: the same explosive burst pose, held an instant later — same steep lean, same swept-back arms, same trailing legs — with the scarf carrying more of the sense of continued forward momentum. This is the pose that stays held once the dash state ends. |

All three are deliberately **not** a jump/leap silhouette (no vertical liftoff cue), **not**
a normal running stride (no alternating-leg mid-stride reads), and clearly distinct from
`jump`/`fall`/`double_jump`'s own poses (which read as rising, falling-open, and a tucked
knees-up flare respectively, per those animations' own records): dash's identifying read is
the extreme, sustained forward torso lean with both arms and legs swept the same direction,
which none of the other airborne moves show.

## Generation

Every frame is two `gen image` calls (`--provider openai --model gpt-image-2 --quality
high --size 1024x1024 --background transparent`), exactly the trial's own two-layer recipe:

1. **Body** (no scarf): `--input` the approved turnaround
   (`assets/bakeoff/protagonist/concept/violet-turnaround.png`) **plus** `run-body-00.png`
   (the trial's own kept contact frame) as an extra style anchor — per the assignment,
   since we are now a generation further from the original reference than the trial was.
2. **Scarf** (alone, transparent): `--input` that same frame's kept body image (for
   pose/framing) plus the live rig's own `parts/scarf1.png` (for the established
   neutral-gray color).

The body prompt reuses the trial's STYLE sentence and FRAME wrapper **word for word**
(same character description, same "generous empty margin," same "no scarf or neck wrap of
any kind" line), with only the pose sentence rewritten per frame (see the pose table
above, expanded into full prompt text in `finalize_dash.py`'s neighbor `dash-body-NN.png`
provenance sidecars). The scarf prompt reuses the trial's scarf scaffold word for word
except "a running girl"/"her running motion" → "a dashing girl"/"her sudden dash burst"
(matching the actual pose), plus one added line responding directly to the trial's own
known defect: **"Paint exactly one solid, opaque scarf shape — not several overlapping or
duplicated semi-transparent copies."** (also applied to the `run` QA fix, see
`technique-trial.md`'s frame-consistency section).

### Calls and rejections

| Frame | Body calls | Rejected (why) | Scarf calls | Rejected (why) |
|---|---|---|---|---|
| 0 | 1 | 0 | 1 | 0 |
| 1 | 1 | 0 | 1 | 0 |
| 2 | 1 | 0 | 1 | 0 |
| **Total** | **3** | **0** | **3** | **0** |

**6 `gen image` calls total, 0 rejected.** Every body and scarf frame was reviewed both at
full size and composited onto the neutral-gray background at in-game scale (~100 px tall,
via a throwaway preview script) before acceptance. None showed off-model drift (face,
costume, proportions, style all matched the turnaround/run anchors), none showed the
scarf-ghosting defect (each scarf is one continuous, opaque, neutral-gray shape — measured:
interior alpha mostly 200-255, corner alpha ~0, average RGB within a few points of R≈G≈B,
no color tint), and none read as an ambiguous pose. (One frame's first composited preview,
`dash-body-02.png`, appeared to have a black vignette background in this session's own
image-preview tool; measuring the actual PNG's alpha channel directly showed corner alpha
already 0 (fully transparent) and interior alpha 250-254 — a preview-tool flattening
artifact, not a real defect in the file, confirmed by re-compositing onto the actual
neutral-gray background used at build time.)

### Spend estimate

6 calls × ~$0.22/call (`docs/bakeoff/shared-costs.md`'s measured `gpt-image-2` rate) =
**~$1.32 est., all kept.**

## Post-processing (deterministic, recorded as `provenance edit`)

`finalize_dash.py`, run once over the 6 raw generated frames — the same recipe as the
trial's own `finalize_frames.py`, generalized:

1. **Trim.** Each frame's body+scarf alpha>8 bounding boxes are unioned and both images are
   cropped to that one shared box (pixel-aligned, no separate offset bookkeeping).
2. **Scale.** The trial's own `rig_per_raw = 1.128227381210675` is **reused verbatim, never
   re-derived** — per the assignment's calibration requirement ("one shared scale... every
   animation is the same size as the run") — so dash's own varying silhouette height (a
   compact, leaning burst is naturally shorter than an upright run contact pose) comes out
   at the correct *relative* size without a second, frame-count-dependent calibration step.
3. Each of the 6 files is overwritten in place with a `provenance edit` describing the
   exact union bbox and the reused scale factor (see each file's `.provenance.json`).

## Anchoring (airborne/either — not sole-to-ground)

`docs/bakeoff/mechanic.md` and the rig's own zero-translate `dash` timeline (above) both
say dash is not reliably grounded, so — per the assignment's explicit rule for this case —
every dash frame is anchored by **head position**, never by a sole-to-ground line, matched
against technique A's own `dash` at the same time:

- Technique A's `dash` was measured directly from forward kinematics
  (`spinerig.render._placements`, the `"head"` slot's attachment centre — not a rendered
  raster — for exactness), at the same 3 evenly-spaced times as the painted frames
  (`t = 0, 0.0667, 0.1333`), expressed as a fraction of `build.py`'s own fixed
  `REFERENCE_BOX` (the same box `shoot.py`/`build.py` use for every animation's contact-
  sheet cell, so the fraction is scale-invariant and carries to the in-game sheet too):

  | # | t (s) | A's head_x_fraction | A's head_y_fraction |
  |---|---|---|---|
  | 0 | 0.000 | 0.609333 | 0.359167 |
  | 1 | 0.067 | 0.659343 | 0.386450 |
  | 2 | 0.133 | 0.668700 | 0.392181 |

  (Measured with: `uv run --project tools/spinerig` + a small script importing
  `spinerig.render._placements` directly, rather than the CLI's `spinerig render`, because
  the CLI's own `--out` frames use each animation's own auto-computed bounding box/margin —
  different per animation — while `build.py`'s fixed `REFERENCE_BOX` is what the final
  contact sheet actually places every animation's frames into; measuring straight from FK
  against that same fixed box skips a raster round-trip entirely.)
- Each painted frame's **own** head position (`head_x`, `head_y`) is the alpha-weighted
  centroid of the top 18% of the body's own alpha bbox (the same head-locating band
  `finalize_frames.py` used for `head_x` alone; extended here to both x and y), in the
  frame's final (cropped+rescaled) coordinate space.
- `dash-finalize-record.json` (one file, all 3 frames) records both: each frame's own
  `head_x`/`head_y` (and `sole_y`, kept for completeness/consistency with the schema even
  though unused for placement) and A's `target_head_x_fraction`/`target_head_y_fraction`
  for that same frame — so a renderer places each frame at
  `target_head_{x,y}_fraction * cell_{w,h} − head_{x,y} * canvas_scale`, the same shape of
  formula `build.py`'s `render_cell` already uses for `run`, just with the head as the one
  shared anchor point (for both body and scarf, since both are cropped from the shared
  union box) instead of head_x/sole_y as two separate anchors.
- QA'd with a throwaway preview script that composites all 3 frames at `SCALE=0.22` with a
  red cross marking each frame's target head position: the cross lands on/at the painted
  head in all 3 frames, and the three poses read as a continuous anticipation → burst →
  held-release progression at a consistent character scale (see `finalize_dash.py`'s
  module docstring for the exact method; the preview script itself was not committed,
  matching the project's "don't keep scratch" convention).
- `ground_anchored: false` is recorded explicitly per frame in `dash-finalize-record.json`
  so a lane-side renderer building all seven animations from these records can tell dash
  apart from `idle`/`run`'s ground-line convention without inspecting the animation name.

## Deliverables

All under `assets/bakeoff/protagonist/glow-up/trial-b/`:

- `frames/dash-body-NN.png`, `frames/dash-scarf-NN.png` (`NN` = 00-02): the 6 finalized
  painted layers, each with a `.provenance.json` sidecar (generation + trim edit).
- `frames/dash-finalize-record.json`: per-frame anchors and A's per-frame target, above.
- `finalize_dash.py`: the script that produced the above from the raw generations.
- This file.

No contact-sheet row, in-game row, or GIF was built for `dash` alone — the assignment's
integration step assembles all seven animations into one contact sheet for the critic, and
this lane's acceptance criteria list frames/record/script/this record/provenance, not a
standalone sheet.

## Calibration note: why reuse, not re-derive

Re-deriving `rig_per_raw` from dash's own frame 0 (the way the trial derived it once, from
`run`'s frame 0) would calibrate dash's scale against dash's *own* silhouette height at
`t=0` — but that pose is a partial lean, not the trial's own reference contact height, so a
second independent calibration would size dash relative to a different, arbitrarily-chosen
reference frame than every other animation uses, breaking the "one shared scale" the
assignment asks for. Reusing the trial's one factor verbatim keeps every animation's
painted pixels in the same rig-unit space `run`, `idle`, and (eventually) the rest already
share, so a taller pose comes out taller and a crouched/leaning pose comes out shorter for
the *right* reason (the pose itself), not as an artifact of which frame happened to anchor
that animation's own scale.
