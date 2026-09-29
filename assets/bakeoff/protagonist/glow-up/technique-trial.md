# Violet technique trial: frame-by-frame painted sprites (technique B), `run` only (THROWAWAY)

Part of the Phase 1 bake-off glow-up round; see [glow-up.md](../../../../docs/bakeoff/glow-up.md), which
requires the Violet workstream to "try at least two animation techniques, and keep whichever the critic
prefers on `character_appeal`": technique A (the cutout Spine-JSON rig, polished — [rounds.md](rounds.md),
stopped at its round 2) and technique B (frame-by-frame painted sprites, this trial). This trial is
`run` only, blind-compared against technique A's latest kept round, exactly as `docs/bakeoff/glow-up.md`
and `rounds.md` require for the technique decision.

## The animation

`assets/bakeoff/protagonist/rig-src/anims.py`'s `A["run"]`: `duration=0.6`, `loop=True`. Five explicit
keyframes at `t = 0, 0.15, 0.3, 0.45, 0.6` (`0.6` repeats `0`): contact at `0` (front leg forward) and
`0.3` (back leg forward, mirrored), passing at `0.15` and `0.45` (support leg under the hips, other knee
driven up high). `docs/bakeoff/character-rig.md`: `run` loops, `t=0` plays immediately after `t=duration`
without repeating it.

## Frame count and timing

**8 frames, evenly spaced 0.075 s apart** (`0, 0.075, 0.15, ..., 0.525`, then loops back to frame 0 at
`t=0.6`) — chosen because it doubles the rig's own 4 keyframes-per-half-cycle into a full classic
animator's "wheel" (contact / recoil-down / passing / drive-up, mirrored for the second half-stride),
giving the painted cycle proper in-between breakdowns rather than only the rig's 4 extremes, while
staying a modest, boundable number of paid generations for a technique *trial*. `0.075 s = 13.3` fps-
equivalent hold time, a typical hand-drawn run-cycle frame rate (compare Hollow Knight's own sprite
cycles, this trial's named technique-B reference in `rounds.md`).

The 8 poses, matched to the rig's own semantics:

| # | t (s) | Pose |
|---|---|---|
| 0 | 0.000 | Contact A: front (lead) leg planted, sole/ball at the lowest point; back leg trailing, bent, airborne. |
| 1 | 0.075 | Recoil A (breakdown): weight settling onto the planted leg, hips at their lowest; other leg lifting behind. |
| 2 | 0.150 | Passing A: support leg vertical under the hips; other knee driven up high in front (recovery). |
| 3 | 0.225 | Drive A (breakdown): support leg pushing off/extending behind; recovering leg opening forward. Tallest pose. |
| 4 | 0.300 | Contact B: mirror of 0 (the other leg leads). |
| 5 | 0.375 | Recoil B: mirror of 1. |
| 6 | 0.450 | Passing B: mirror of 2. |
| 7 | 0.525 | Drive B: mirror of 3. |

## Generation

Every frame is two `gen image` calls (`--provider openai --model gpt-image-2 --quality high --size
1024x1024 --background transparent`), matching the requirement that the scarf stay a separate
neutral-gray tintable layer: (1) her **body without the scarf** (bare gray robe collar at the neck), `
--input` the approved turnaround (`assets/bakeoff/protagonist/concept/violet-turnaround.png`); (2) the
**scarf alone** on transparent background, `--input` that same body frame (for pose/framing) plus the
live rig's own `parts/scarf1.png` (for the established neutral-gray color), painting nothing but a wide
flowing gray scarf shape.

Full prompt text (STYLE + pose + FRAME wrapper for bodies, one SCARF_PROMPT for scarves) is in
`trial-b/build.py`'s companion generation record below; the poses table above gives the per-frame pose
text used.

### Calls and rejections

| Frame | Body calls | Rejected (why) | Scarf calls | Rejected |
|---|---|---|---|---|
| 0 | 3 | 2 — both read as an ambiguous leap/floating pose with no foot clearly grounded, despite explicit "contact, not a jump" prompt language; kept the 3rd after adding "this is NOT a jump... lowest point of the whole image... clearly resting on a floor" | 1 | 0 |
| 1 | 1 | 0 | 1 | 0 |
| 2 | 1 | 0 | 1 | 0 |
| 3 | 1 | 0 | 1 | 0 |
| 4 | 1 | 0 | 1 | 0 |
| 5 | 1 | 0 | 1 | 0 |
| 6 | 1 | 0 | 1 | 0 |
| 7 | 1 | 0 | 1 | 0 |
| **Total** | **10** | **2** | **8** | **0** |

**18 `gen image` calls total, 2 rejected (not committed; the rejected pixels were overwritten by the
kept 3rd attempt, so only the kept attempt's bytes and provenance exist on disk — the rejections are
recorded here, in this table, as the record of what happened).** 16 calls kept.

### Spend estimate

18 calls × ~$0.22/call (`docs/bakeoff/shared-costs.md`'s measured per-call rate for `gpt-image-2`,
quality high, 1024×1024, from OpenAI's own reported usage) = **~$3.96 est.** (~$3.30 kept, ~$0.44
rejected).

## Post-processing (deterministic, recorded as `provenance edit`)

`trial-b/finalize_frames.py`, run once over all 16 raw generated frames:

1. **Trim.** For each frame index, the alpha>8 bounding box of the body image and of the scarf image are
   unioned, and *both* images are cropped to that one shared box — so the two layers stay pixel-aligned
   (no separate offset bookkeeping needed) while still being tightly trimmed.
2. **Scale.** Calibrated once, against technique A's own round-00 `contact-sheet.png` run row, t=0
   column (the fixed layout's own contact pose): its alpha bbox height is 208 canvas px at `SCALE=0.22`,
   i.e. 945.4545 rig units. Frame 0's raw body bbox height (838 px after the alpha>8 trim) gives
   `RIG_PER_RAW = 945.4545 / 838 = 1.128227`. This single factor is applied to *every* frame (not
   re-derived per pose), so shorter/crouched poses come out correctly shorter, the same way technique
   A's own passing frames are naturally shorter from real hip-lowering, not a rescale artifact.
3. Each of the 16 files was overwritten in place and given a `provenance edit` describing the exact
   union bbox and scale factor used (see each file's `.provenance.json`).

## Shooting technique B's `run`

`trial-b/build.py` reuses `shoot.py`'s own constants (`REFERENCE_BOX`, `SCALE=0.22`, `BACKGROUND
=#808080`, `FRAMES_PER_ROW=6`, cell-size formula) so the sheet is byte-comparable in scale/layout to
technique A's:

- **Reference box placement (feet at the root).** Technique B has no skeleton, so "the root" is defined
  operationally from technique A's own measurements: the **ground line** is the fraction of the cell's
  height where A's run row's sole sits (`306/316` of the cell, measured across all six of A's own
  columns), and the **horizontal anchor** is the fraction of the cell's width where A's run row's visual
  center sits on average (`135/290`). Both are fractions of the cell (not fixed px), so they carry over
  correctly to the in-game sheet's smaller cells too. Every technique-B frame is placed so its own
  head-region alpha centroid lands on the horizontal anchor and its own sole (lowest alpha row) lands on
  the ground line.
- **Six sample times**, `t = i·0.6/6` for `i=0..5` (`shoot.py`'s own `sample_times` rule for looping
  animations): `0, 0.1, 0.2, 0.3, 0.4, 0.5`. Each maps to "the frame showing at that time" — technique
  B has no in-between interpolation, so this is a **held/step** lookup, `frame_index = floor(t /
  0.075)`, matching real discrete-sprite playback: `[0, 1, 2, 4, 5, 6]` (contact-A, recoil-A, passing-A,
  contact-B, recoil-B, passing-B — a good spread of 6 of the 8 distinct poses).
- **GIF at 30 fps.** Each of the 8 painted frames holds from its own start time to the next frame's
  start time (a discrete "on the frame" hold, not resampled at every 1/30 s tick). Durations are each
  frame's held span in ms, rounded to the GIF format's 10 ms (centisecond) granularity by *cumulative*
  rounding (not by rounding one `1000/30` figure and repeating it), so the 8 stored durations
  (`80,70,70,80,80,70,70,80` ms) sum to exactly 600 ms rather than drifting to 540 ms.
- **In-game-scale row**, at `character-rig.md`'s own formula `(1.6·64)/height_px` evaluated at the live
  rig's own `height_px` (988.58081) — the same standard technique A's own `contact-sheet-ingame.png` is
  held to.

Deliverables, all under `assets/bakeoff/protagonist/glow-up/trial-b/`:

- `frames/run-body-NN.png`, `frames/run-scarf-NN.png` (`NN` = 00-07): the 16 finalized painted layers.
- `run-row.png`: the six-sample run row at `SCALE=0.22`, same cell size (290×316) and background as
  technique A's contact sheet.
- `run-row-ingame.png`: the same six samples at in-game scale (136×149 cells).
- `run.gif`: 30 fps, 8 frames, exact durations above.
- `build.py`, `finalize_frames.py`: the two THROWAWAY scripts that do all of the above, so the pipeline
  is reproducible.

## Comparison set

**A (technique A, cutout rig): round 2**, `rounds.md`'s latest kept round as of this trial (round 0 was
superseded; round 1 was reverted; round 2 was kept, and technique A's workstream stopped there — two
rounds in a row with no axis better, `glow-up.md`'s own stop condition). A's set is `round-02/contact-
sheet.png`'s run row (cropped, same six columns) and `round-02/run.gif`, unmodified.

**B (technique B, painted): this trial's `run-row.png` and `run.gif`**, above.

## Critic

A fresh `astra` subagent, given only neutral file names and the verbatim prompt from `rounds.md`/
`glow-up.md` (never told which set is newer or what changed). Letters assigned with Python's `random`
module in a scratch directory outside the repo (`/tmp/violet-technique-trial-critic/`, never committed):

**Letter map:** `A = technique A (cutout, round 2)`, `B = technique B (painted, this trial)`.

Full reply: [`trial-b/critic.md`](trial-b/critic.md).

### Per-axis verdict

| Axis | Winner |
|---|---|
| visual_quality | **B** |
| character_appeal | **B** |
| color_readability | **A** |

### Scores (1-5, 5 = GRIS/Planet of Lana bar)

| | visual_quality | character_appeal | color_readability |
|---|---|---|---|
| **A** (cutout, round 2) | 3 | 2 | 3 |
| **B** (painted, this trial) | 4 | 4 | 2 |

### The critic's own reasoning (full text in `trial-b/critic.md`)

The critic decoded both GIFs frame-by-frame (not just the six-panel sheets) and found the decisive
gap in A: isolating the leg region across all 18 of A's GIF frames shows the legs and torso barely
move — front/back leg placement is nearly frozen in one "one leg up, one leg back" pose for the whole
loop, only the scarf and a slight arm-sway animate, so it "reads as gliding/floating, not running."
B's leg strip shows a genuine alternating stride with real contact/passing poses and a body bob. That
drove most of the visual_quality and character_appeal gap. Going the other way, A's color_readability
win comes from its scarf being one coherent white ribbon in every frame (clean silhouette despite low
body-to-background contrast), while B's scarf renders as three stacked, semi-transparent copies at
different offsets in 2 of its 8 frames (indices 1 and 5) — a real generation artifact, not a taste call
(see "Honest read of frame consistency" below; I re-inspected both flagged frames and the critic is
right).

A's three biggest gaps the critic named: (1) the run cycle doesn't cycle (near-frozen legs across all
18 GIF frames); (2) hands are a featureless flesh wedge, no finger/knuckle separation; (3) the scarf
tail is a hard-edged frayed fringe, reading as a torn flag rather than flowing cloth.

B's three biggest gaps the critic named: (1) scarf ghosting in frames 1 and 5 (three stacked
semi-transparent copies, reads as a glitch); (2) low figure-to-background value contrast (the robe's
mid-brown sits close in luminance to the neutral-gray backdrop); (3) frame index 6 (front knee pulled
in tight, legs nearly crossed) reads as a stumble/crouch rather than a clean running passing-position.

## Winner on `character_appeal`

**Technique B (frame-by-frame painted) wins on `character_appeal`, 4 vs. 2**, and also on
`visual_quality`, 4 vs. 3. Technique A wins on `color_readability`, 3 vs. 2, driven almost entirely by
B's scarf-ghosting flaw in 2 of 8 frames (a fixable generation-QA issue, not a limit of the technique)
versus A's frozen-legs problem (a limit of that specific round's rig animation, already known from
`rounds.md`'s own round-2 critique). Per `glow-up.md`'s rule ("tries at least two animation techniques,
and keeps whichever the critic prefers on `character_appeal`"), **technique B is the winner** for
Violet's `run` animation, and by implication the technique the Violet workstream should carry forward
for the remaining six animations if the full glow-up continues past this trial.

## What the lanes would need if technique B ships (it won `character_appeal`)

`docs/bakeoff/character-rig.md` currently defines only a Spine-JSON bone/rotate/translate/region-
attachment skeleton; it has no notion of a discrete sprite sequence at all. Carrying technique B past
this trial needs a **new contract**, not an extension of the existing one:

- **Sprite-sheet format.** Per animation: an ordered list of frame image paths (or a packed sheet plus
  per-frame rects), a hold-duration per frame (or a shared fps plus a loop/hold flag, matching
  `character-rig.md`'s existing `idle`/`run` loop vs. the other five hold-last-frame distinction), and
  a `facing: right` + mirror-for-left convention (mirroring a flat painted sprite is exact, unlike
  mirroring a bone).
- **Separate scarf layer.** Two image lists per animation (body, scarf), composited scarf-then-body
  (or body-then-scarf, whichever a lane's engine draws correctly) at the same per-frame index, so a
  lane can still tint just the scarf layer the way it tints the current rig's `scarf1-3` slots.
- **A ground/root anchor per frame** (this trial's `sole_y`/`head_x` fields in `finalize-record.json`,
  or equivalent), so a lane's reader can place each frame without every source image needing pixel-
  identical framing.
- **`tools/spinerig`'s replacement**: a reader/renderer for this format analogous to `spinerig render`,
  so a human can proof playback before any lane wires it in, and each lane owner ports its reader
  (`glow-up.md`: "the Violet workstream changes the contract and `tools/spinerig` in a PR, and each
  lane owner ports its reader"). **Not implemented here** — Main's instructions were to record the
  need, not build the contract change.

## Honest read of frame consistency

Reviewed every one of the 8 body frames and 8 scarf frames by eye (montage grids), plus every composited
pair, before finalizing:

- **Style/design/proportions:** very consistent across all 8 frames — same palette, same hood/robe/sash
  silhouette, same face (visible eye, brow, nose, mouth in every frame), same child-like proportions.
  None drifted off-model; no frame needed a design-drift rejection (only frame 0's *pose* was rejected
  twice, not its design).
- **Scarf alignment:** generating the scarf with the body frame as `--input` worked geometrically (no
  manual per-frame offset correction needed anywhere — the shared-crop pipeline kept every frame's
  scarf pixel-aligned to its own body frame). But 2 of 8 frames (1 and 5) have a real *rendering* flaw
  the critic caught and I confirmed by re-opening both files: the scarf paints as three overlapping,
  semi-transparent copies of the same ribbon at slightly different offsets, instead of one opaque
  flowing shape — a generation artifact I should have caught myself before the critic call, not a
  misalignment. I did not regenerate to fix it after the critic scored it, since that would invalidate
  the blind comparison; it stands as a known, fixable gap (see below).
- **Leg "mirroring":** frames 4-7 were prompted as literal mirror-images of 0-3 (other leg forward), but
  a side-view running *silhouette* with two visually-symmetric bare legs has no visual information that
  distinguishes "left leg forward" from "right leg forward" — confirmed by measuring technique A's own
  round-00 contact-sheet run row: its t=0 and t=0.3 columns (nominally mirror poses) have an **identical**
  208 px bbox height. So this is not a technique-B defect; independent per-frame generation naturally
  produced 8 frames with real (if not perfectly bilaterally mirrored) pose variation, not two literal
  repeats — the GIF montage shows 8 distinct drawings, not a 4-frame cycle playing twice.
- **Ground/scale alignment:** solid. All 8 frames' soles land on the same measured ground line and all
  8 share one calibration factor (not re-derived per frame), so the GIF doesn't jitter vertically or
  grow/shrink between frames the way independent, uncalibrated generations often do.
- **QA fix (2026-09-29, full glow-up pass, `VioletBDashRunFix`):** regenerated the scarf layer only
  for frames 1 and 5, the two flagged above. Each used that frame's existing (unchanged) body PNG as
  `--input`, exactly this trial's own recipe, plus an explicit "paint exactly one solid, opaque scarf
  shape" guard added to the scarf prompt. Both came back as a single coherent flowing ribbon on the
  first call (no rejections). The new scarves trail slightly further than the old defective ones, so
  each was cropped to its own alpha bbox rather than clamped to the frame's original body+scarf union
  box, rescaled by the same shared factor, and given a recorded `scarf_offset_final` (rig units) so
  `build.py`'s `render_cell` places it correctly relative to the untouched body
  (`finalize_run_scarf_fix.py`). `run-row.png`/`run.gif` were rebuilt; frames 1 and 5 now read as one
  opaque scarf, matching the other six. The body frames and the other six scarves are unchanged.

