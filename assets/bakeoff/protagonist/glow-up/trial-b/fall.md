# Technique B `fall` (THROWAWAY, Phase 1 bake-off) -- PARTIAL, 3 of 5 frames

Ran out of tool-call budget before finishing. **Frames 0-2 of a planned 5 are painted,
finalized and committed; frames 3-4 (the "continuing to settle" frame and the held final
"settled falling" frame) are not yet generated.** Everything below describes what exists.

## Plan

`rig-src/anims.py`: `A["fall"] = {"duration": 0.6, "loop": False, ...}` -- plays once and
holds its last frame (`character-rig.md`). Planned **5 frames, evenly spaced 0.12 s apart**
(`t = 0, 0.12, 0.24, 0.36, 0.48`, last frame held from 0.48 through 0.6 and beyond) --
~8.3 fps, inside the assignment's 8-12 fps guidance, and cleanly divides 0.6 s the same way
run's `FRAME_DT = duration/NFRAMES` convention does.

Design brief (assignment): descending, body opening, arms up and out, robe and scarf
trailing upward -- clearly different from a rising jump and from double_jump's compact
tuck.

| # | t (s) | Pose (planned) | Status |
|---|---|---|---|
| 0 | 0.00 | Transitioning out of the shared airborne "rise": body just starting to uncurl and open, arms lifting to shoulder height, legs loosening and separating. | **Done** |
| 1 | 0.12 | Falling, opening further: arms at shoulder height swept out to the sides, legs hanging loose apart, robe skirt starting to billow, torso beginning to arch back, head starting to tilt down. | **Done** |
| 2 | 0.24 | Falling, body fully open: arms at shoulder height spread wide, torso arched back and open, legs loose and apart, robe billowing around the waist/thighs, head tilted down. | **Done** |
| 3 | 0.36 | Continuing the drop, settling into the open pose, robe lifted along her whole body. | Not generated |
| 4 | 0.48 | The held pose: arms at shoulder height spread wide, robe and scarf trailing straight up above/around her, head tilted down. This is what plays whenever the game holds `fall` past 0.48 s. | Not generated |

## Generation

Same recipe as the trial's `run` (STYLE + FRAME wrapper reused word-for-word where it
applies; two `gen image` calls per frame, `--provider openai --model gpt-image-2 --quality
high --size 1024x1024 --background transparent`):

- **Body**: `--input` the turnaround (`concept/violet-turnaround.png`) plus one run body
  anchor (`trial-b/frames/run-body-02.png`, the "passing" pose). Frame 0 was generated
  before a defect was diagnosed and used **two** run-body anchors (`run-body-00.png` +
  `run-body-02.png`); every frame after that uses **one** anchor only (see "Generation
  defect" below).
- **Scarf**: `--input` that frame's own finalized body PNG plus `parts/scarf1.png` (color
  reference), same as the trial.

Full prompt text is in each frame's own `.provenance.json` (`generator.prompt`). The pose
clauses live in `finalize_anim.py`'s sibling generation driver (not itself committed --
see "What isn't committed" below); the exact pose sentences used are quoted in the table
above and, verbatim, in each frame's provenance record.

### Generation defect found and fixed mid-lane

`gpt-image-2` intermittently painted an opaque dark vignette/spotlight background instead
of a transparent one, despite `--background transparent` and explicit "no vignette"
prompt language -- a real generation defect, not a preview artifact (confirmed by the
provenance sidecar's own echoed `params.background: "transparent"` not matching the actual
pixels). Two things reduced its rate:

1. **Fewer style-anchor inputs.** Using 2 run-body anchors (turnaround + `run-body-00` +
   `run-body-02`) failed more often than using 1 (turnaround + `run-body-02` only). Not a
   full fix on its own (see next point).
2. **Plainer pose wording.** Intensifier phrasing ("flaring **dramatically**", "**must
   read unmistakably** as falling", "**the definitive** falling pose") reproduced the
   defect 2/2 times on one frame; rewriting to plainer wording with the same content fixed
   it 1/1 retry. Frames 2-4's pose text (config, not committed) was toned down
   accordingly before frame 2's successful generation.

### Calls and rejections

| Frame | Body calls | Rejected (why) | Scarf calls | Rejected |
|---|---|---|---|---|
| 0 | 1 | 0 | 1 | 0 |
| 1 | 2 | 1 -- 2-anchor recipe, dark vignette background (not transparent) | 1 | 0 |
| 2 | 2 | 1 -- anchors=1 already, but "dramatically"/"must read unmistakably" wording, dark vignette background | 1 | 0 |
| **Total (frames 0-2)** | **5** | **2** | **3** | **0** |

**8 `gen image` calls for frames 0-2, 2 rejected, 6 kept.** Frames 3-4 not attempted.

### Spend estimate

8 calls x ~$0.22/call (`docs/bakeoff/shared-costs.md`'s measured rate) = **~$1.76 est.**
for `fall` alone. See the sibling `double_jump.md` for that animation's tally; combined
lane spend is in this session's final report, not duplicated here.

## Post-processing

`trial-b/finalize_anim.py fall` (generalizes `finalize_frames.py`'s approach to airborne,
non-ground-contact frames), run once over the 3 raw generated frames present:

1. **Trim.** Same shared alpha>8 bbox union between body and scarf as `finalize_frames.py`.
2. **Scale.** Reuses run's own calibrated `RIG_PER_RAW = 1.128227381210675` unchanged (per
   the assignment: "one shared scale, reuse the trial's `rig_per_raw` approach and
   calibration so every animation is the same size as the run") -- not re-derived.
3. **Anchors** (airborne, so no ground line): each frame's `head_x`/`head_y` are the local
   alpha-weighted centroid of the body layer's top 18% band (same heuristic as run's
   `head_x`, extended to also return `head_y`), in the frame's own cropped+rescaled
   coordinate system. Valid here because every fall pose keeps both hands at or below the
   crown of the hood by prompt constraint, so the topmost significant alpha mass is always
   the head/hood.
4. **Cross-technique root-motion match.** Each frame also records `target_head_x`/
   `target_head_y`: technique A's own head-slot world center at that frame's designated
   time `t = i * 0.12`, computed via `spinerig.render._placements()` +
   `world_to_canvas(cx, cy, REFERENCE_BOX, 1.0, 0)` (`REFERENCE_BOX` is `rounds.md`'s fixed
   layout box; `scale=1.0` keeps the result in raw rig units, not canvas px, so a later
   build step multiplies by whatever `canvas_scale` it renders at). A's own head position
   barely moves during `fall` (514.5 -> 515.5 canvas-y across the 3 measured frames --
   `fall`'s rig keyframes only rotate limbs, they don't translate the hip/root), so B's
   frames land almost exactly stacked, which is correct: the actual downward motion is
   physics-driven in-game, not baked into either rig's own pose data.
5. Records: `trial-b/frames/fall-finalize-record.json` (frames 0-2 only). Every frame's
   union-bbox trim and rescale is a `provenance edit` on both its body and scarf PNG (see
   each file's `.provenance.json`); the scarf's own `inputs[0]` hash reference to its body
   frame was also corrected via a `human_edits` entry after the body's trim changed its
   hash (the same staleness `rounds.md` describes for shared inputs, but between one
   frame's own body/scarf pair rather than a shared rig asset).

A later build step (not written here -- out of scope per the assignment, which only asked
for frames + finalize + records) would place each frame with `dx = (target_head_x -
head_x) * canvas_scale`, `dy = (target_head_y - head_y) * canvas_scale`, no ground line.

## What isn't committed

- Frames 3 and 4 (body + scarf, and their finalize-record entries).
- A per-animation contact-sheet row / GIF (`build.py`-equivalent) -- out of scope per the
  assignment; the integration step assembles all seven animations.
- The generation driver script that built each prompt from a config
  (`/tmp/vbf_gen_frame.py`, `/tmp/vbf_config.json`) lived outside the repo as scratch
  tooling, not `trial-b/finalize_*.py`; `finalize_anim.py` (the deterministic,
  reproducible post-processing step) is the one committed here.

## Honest read

- **Style/design/proportions**: consistent across all 3 frames and with `run` -- same
  palette, hood/robe/sash silhouette, visible face, child-like proportions. No off-model
  drift on any kept frame.
- **Scarf**: all 3 scarf frames are a single opaque, neutral-gray flowing shape -- none of
  the trial's run-frames-1-and-5 "three stacked semi-transparent copies" ghosting defect.
- **Pose distinctness**: frames 0-2 read as an opening/descending sequence (arms rising to
  shoulder height and spreading, robe billowing) that is visibly different from a
  compact tuck (double_jump) and starts from, rather than repeats, the shared airborne
  "rise" pose jump ends on. Frame 0 is the weakest of the three on its own (a transitional
  pose, closer to a generic "airborne" read than a strong "falling" read by itself) --
  acceptable as an opening frame in a 5-frame sequence, but **the sequence is incomplete
  without frames 3-4**, and frame 4 (the pose that holds indefinitely in-game whenever
  `fall` plays out) is exactly the frame not yet made. Until it exists, this animation
  cannot be judged as a finished "falling" read the way the assignment's QA bar requires.
