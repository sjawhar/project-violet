# Technique B `fall` (THROWAWAY, Phase 1 bake-off) -- complete, 5 of 5 frames

Started by session `VioletBFallDJ` (frames 0-2, recovered by the lead after that
workspace went stale) and finished by session `VioletBFallDJ2` (frames 3-4, this update).
All 5 planned frames are now painted, finalized and committed.

## Plan

`rig-src/anims.py`: `A["fall"] = {"duration": 0.6, "loop": False, ...}` -- plays once and
holds its last frame (`character-rig.md`). **5 frames, evenly spaced 0.12 s apart**
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
| 3 | 0.36 | Still falling, continuing to open further: arms remain at shoulder height spread wide, torso arched back further, legs hanging loose and apart, the robe skirt and hem lifting and trailing upward from the building rush of air, head tilted down. | **Done** |
| 4 | 0.48 | The held pose: arms at shoulder height spread wide, torso arched back and fully open, legs hanging loose and apart, the entire robe skirt and scarf trailing straight upward above and around her from the sustained fall, head tilted down. This is what plays whenever the game holds `fall` past 0.48 s. | **Done** |

## Generation

Same recipe as the trial's `run` (STYLE + FRAME wrapper reused word-for-word where it
applies; two `gen image` calls per frame, `--provider openai --model gpt-image-2 --quality
high --size 1024x1024 --background transparent`):

- **Body**: `--input` the turnaround (`concept/violet-turnaround.png`) plus one run body
  anchor (`trial-b/frames/run-body-02.png`, the "passing" pose). Frame 0 was generated
  before a defect was diagnosed and used **two** run-body anchors (`run-body-00.png` +
  `run-body-02.png`); every frame after that (1-4) uses **one** anchor only (see
  "Generation defect" below).
- **Scarf**: `--input` that frame's own raw (pre-finalize) body PNG plus `parts/scarf1.png`
  (color reference), same as the trial.

Full prompt text is in each frame's own `.provenance.json` (`generator.prompt`). The pose
clauses are quoted in the table above and, verbatim, in each frame's provenance record.

### Generation defect found and fixed mid-lane (frames 0-2, `VioletBFallDJ`)

`gpt-image-2` intermittently painted an opaque dark vignette/spotlight background instead
of a transparent one, despite `--background transparent` and explicit "no vignette"
prompt language -- a real generation defect on some calls, not always a preview artifact
(confirmed on the frame-1/frame-2 rejections below by the provenance sidecar's own echoed
`params.background: "transparent"` not matching the actual pixels). Two things reduced its
rate:

1. **Fewer style-anchor inputs.** Using 2 run-body anchors (turnaround + `run-body-00` +
   `run-body-02`) failed more often than using 1 (turnaround + `run-body-02` only).
2. **Plainer pose wording.** Intensifier phrasing ("flaring **dramatically**", "**must
   read unmistakably** as falling", "**the definitive** falling pose") reproduced the
   defect 2/2 times on one frame; rewriting to plainer wording with the same content fixed
   it 1/1 retry.

### Prompt guard added for frames 3-4 (`VioletBFallDJ2`)

The task instructions asked for an explicit anti-vignette prompt guard given the above
history. The body prompt's transparency clause was strengthened from a single sentence
("Transparent background, no ground plane, no floor, no cast shadow, no vignette, no
border...") into: **"The background must be fully transparent everywhere outside her
figure -- absolutely no vignette, no darkened or gradient backdrop, no glow or halo behind
her, no ground plane, no floor, no cast shadow or ground shadow of any kind, no border..."**
(full text in each frame's provenance sidecar). The scarf prompt's closing clause gained
"...fully transparent everywhere else, with no vignette or darkened backdrop of any kind."

With this guard, frame 3's first generation still rendered with an apparent dark
vignette/glow in this session's own image-preview tool -- but direct pixel inspection
(`PIL`, sampling the alpha channel at the corners and along the edges) showed alpha exactly
0 everywhere outside her figure and 250-254 inside it, i.e. a genuinely transparent PNG;
re-compositing it onto the actual neutral-gray build background confirmed a clean image
with no real vignette. This matches the sibling `dash` lane's own finding (`dash.md`): the
image-preview tool sometimes flattens transparent PNGs onto black for display, which reads
as a vignette but is not present in the file. Frame 4 rendered cleanly with no such preview
artifact either. Neither frame needed a retry; both are kept on the first call.

### Calls and rejections

| Frame | Body calls | Rejected (why) | Scarf calls | Rejected |
|---|---|---|---|---|
| 0 | 1 | 0 | 1 | 0 |
| 1 | 2 | 1 -- 2-anchor recipe, dark vignette background (not transparent) | 1 | 0 |
| 2 | 2 | 1 -- anchors=1 already, but "dramatically"/"must read unmistakably" wording, dark vignette background | 1 | 0 |
| 3 | 1 | 0 | 1 | 0 |
| 4 | 1 | 0 | 1 | 0 |
| **Total (frames 0-2, `VioletBFallDJ`)** | **5** | **2** | **3** | **0** |
| **Total (frames 3-4, `VioletBFallDJ2`)** | **2** | **0** | **2** | **0** |
| **Grand total** | **7** | **2** | **5** | **0** |

**12 `gen image` calls across `fall`'s full 5 frames, 2 rejected, 10 kept.**

### Spend estimate

- Frames 0-2 (`VioletBFallDJ`): 8 calls x ~$0.22/call = ~$1.76 est.
- Frames 3-4 (`VioletBFallDJ2`): 4 calls x ~$0.22/call = ~$0.88 est.
- **`fall` total: 12 calls, ~$2.64 est.** (`docs/bakeoff/shared-costs.md`'s measured rate).
  See the sibling `double_jump.md` for that animation's tally; combined lane spend is in
  this session's final report, not duplicated here.

## Post-processing

`trial-b/finalize_anim.py fall` (generalizes `finalize_frames.py`'s approach to airborne,
non-ground-contact frames), run once per newly-generated frame:

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
   `world_to_canvas(cx, cy, REFERENCE_BOX, 1.0, 0)`. A's own head position barely moves
   during `fall` (514.5 -> 515.5 canvas-y across frames 0-2; 515.3 and 515.4 for frames 3-4
   -- `fall`'s rig keyframes only rotate limbs, they don't translate the hip/root), so B's
   frames land almost exactly stacked, which is correct: the actual downward motion is
   physics-driven in-game, not baked into either rig's own pose data.
5. Records: `trial-b/frames/fall-finalize-record.json`, now covering all 5 frames. Every
   frame's union-bbox trim and rescale is a `provenance edit` on both its body and scarf
   PNG (see each file's `.provenance.json`); each scarf's own `inputs[0]` hash reference
   was also corrected via a `human_edits` entry after its body's trim changed the body's
   hash (the same staleness `rounds.md` describes for shared inputs, but between one
   frame's own body/scarf pair rather than a shared rig asset).

**Incremental finalize (added by `VioletBFallDJ2`).** `finalize_anim.py`'s `main()` now
loads any existing `<anim>-finalize-record.json`, and only trims+rescales frame indices
not already present in it -- previously it always reprocessed every `<anim>-body-*.png` it
found, which would have re-trimmed and re-rescaled (compounding `RIG_PER_RAW` a second
time) the already-finalized frames 0-2 the moment frames 3-4 were added to the same
directory. This was necessary, not a style choice: frames 0-2's on-disk pixels are already
post-trim/post-rescale, not raw 1024x1024 generations, so a second pass over them would
have corrupted their size. Frames 0-2's bytes and record entries are untouched by this
change (verified: re-running `finalize_anim.py fall` after 3-4 already exist prints
"already finalized, nothing to do" and leaves every file's hash unchanged).

A later build step (not written here -- out of scope per the assignment, which only asked
for frames + finalize + records) would place each frame with `dx = (target_head_x -
head_x) * canvas_scale`, `dy = (target_head_y - head_y) * canvas_scale`, no ground line.

## Honest read

- **Style/design/proportions**: consistent across all 5 frames and with `run` -- same
  palette, hood/robe/sash silhouette, visible face, child-like proportions. No off-model
  drift on any kept frame.
- **Scarf**: all 5 scarf frames are a single opaque, neutral-gray flowing shape (confirmed
  by sampling RGB channels across each scarf's opaque interior: R, G and B never differ by
  more than 3 out of 255, i.e. genuinely neutral gray, not tinted) -- none of the trial's
  run-frames-1-and-5 "three stacked semi-transparent copies" ghosting defect.
- **Pose distinctness and progression**: the full 5-frame sequence reads as a continuous
  opening-while-falling arc -- arms spreading to shoulder height, torso arching back, and
  (the change frames 3-4 add) the robe skirt and scarf progressively trailing further
  upward as the fall continues, culminating in frame 4's strong, wide "wings" silhouette
  that is the pose the game holds indefinitely. Viewed as a montage at both full size and
  ~100 px, `fall` reads clearly differently from `double_jump` (which compacts into a tight
  tuck at its midpoint, never seen anywhere in `fall`) and from `jump` (whose held rising
  pose, fetched from `phase1/violet-b-jumpland` for comparison, keeps the legs in a loose
  bent tuck under the body with one arm reaching forward/down -- `fall`'s frames never do
  either of those; both arms stay spread symmetrically to the sides and the legs hang
  loose and apart, not tucked). Frame 0 remains the weakest single frame in isolation (a
  transitional pose, closer to a generic "airborne" read than a strong "falling" read by
  itself), but it now sits inside a complete 5-frame arc rather than standing in for the
  whole animation, which was the concrete gap the previous session's own honest read named.
