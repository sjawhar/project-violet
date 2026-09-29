# Technique B `double_jump` (THROWAWAY, Phase 1 bake-off) -- complete, 5 of 5 frames

Started by session `VioletBFallDJ` (frames 0-1, recovered by the lead after that
workspace went stale) and finished by session `VioletBFallDJ2` (frames 2-4, this update).
All 5 planned frames are now painted, finalized and committed.

## Plan

`rig-src/anims.py`: `A["double_jump"] = {"duration": 0.5, "loop": False, ...}` -- plays
once and holds its last frame. **5 frames, evenly spaced 0.1 s apart** (`t = 0, 0.1, 0.2,
0.3, 0.4`, last frame held from 0.4 through 0.5 and beyond) -- 10 fps, inside the
assignment's 8-12 fps guidance. Matches the rig's own beat: a quick snap into a tuck by
0.08 s, held to 0.22 s, opening back out to the rising pose by 0.5 s.

Design brief (assignment, and Sami's explicit ruling): a quick tuck, knees up, arms out,
scarf flaring, **no flip or rotation** -- clearly different from a rising jump (peer lane)
and from fall's open/spread silhouette.

| # | t (s) | Pose (planned) | Status |
|---|---|---|---|
| 0 | 0.00 | Ordinary rising part of a jump, a beat before the extra push: legs extended below/behind, torso upright, arms starting to swing forward at shoulder height. | **Done** |
| 1 | 0.10 | Tight tuck just triggered: knees pulled up, silhouette compact, arms swept out to the sides (not overhead), scarf flaring. No rotation. | **Done** |
| 2 | 0.20 | Tuck held for a beat, painted **tighter** than frame 1: both knees pulled up sharply against her chest, heels drawn in close against her hips, a compact cannonball silhouette, scarf fully fanned out. No rotation. | **Done** |
| 3 | 0.30 | Tuck beginning to release: knees dropping back down and opening away from her chest, torso straightening, arms easing down from shoulder height, scarf settling from its widest flare. No rotation. | **Done** |
| 4 | 0.40 | Held pose: opened back out to the ordinary airborne rise -- legs loosely bent and apart, arms swept out to the sides (not overhead, not reaching forward), scarf drifting but settled. This is what plays whenever the game holds `double_jump` past 0.4 s. | **Done** |

## Generation

Same recipe as `fall` (see that file for the shared-defect story) and the trial's `run`:
two `gen image` calls per frame, `--provider openai --model gpt-image-2 --quality high
--size 1024x1024 --background transparent`.

- **Body**: `--input` the turnaround plus one run body anchor (`run-body-02.png`). Every
  committed frame (0-4) uses this 1-anchor recipe (the 2-anchor recipe was abandoned
  mid-lane after `fall`/this animation both hit the vignette-background defect more often
  with it -- see `fall.md`).
- **Scarf**: `--input` that frame's own raw (pre-finalize) body PNG plus `parts/scarf1.png`.

Full prompt text is in each frame's own `.provenance.json`. Frames 2-4's body and scarf
prompts also carry the strengthened anti-vignette guard `fall.md` describes ("The
background must be fully transparent everywhere outside her figure -- absolutely no
vignette, no darkened or gradient backdrop, no glow or halo behind her..."); none of the 3
new frames showed even the preview-tool-flattening false positive `fall`'s frame 3 did.

### Calls and rejections

| Frame | Body calls | Rejected (why) | Scarf calls | Rejected |
|---|---|---|---|---|
| 0 | 3 | 2 -- 2-anchor recipe, dark vignette background (not transparent) both times | 1 | 0 |
| 1 | 1 | 0 (already on 1-anchor recipe by this point) | 1 | 0 |
| 2 | 1 | 0 | 1 | 0 |
| 3 | 1 | 0 | 1 | 0 |
| 4 | 1 | 0 | 1 | 0 |
| **Total (frames 0-1, `VioletBFallDJ`)** | **4** | **2** | **2** | **0** |
| **Total (frames 2-4, `VioletBFallDJ2`)** | **3** | **0** | **3** | **0** |
| **Grand total** | **7** | **2** | **5** | **0** |

**12 `gen image` calls across `double_jump`'s full 5 frames, 2 rejected, 10 kept.**

### Spend estimate

- Frames 0-1 (`VioletBFallDJ`): 6 calls x ~$0.22/call = ~$1.32 est.
- Frames 2-4 (`VioletBFallDJ2`): 6 calls x ~$0.22/call = ~$1.32 est.
- **`double_jump` total: 12 calls, ~$2.64 est.**

Combined with `fall`'s 12 calls (~$2.64), this session's (`VioletBFallDJ2`) own spend was
**10 calls, ~$2.20 est.** Combined with the previous session's (`VioletBFallDJ`) 14 calls
(~$3.08 est.), the lane's full-run total across both sessions is **24 calls, ~$5.28 est.**

## Post-processing

`trial-b/finalize_anim.py double_jump`, run once per newly-generated frame. Same
trim/scale/anchor approach as `fall.md` describes in detail:

- Shared alpha>8 bbox union trim between body and scarf.
- Rescaled by run's own `RIG_PER_RAW = 1.128227381210675`, unchanged.
- `head_x`/`head_y`: local alpha-weighted centroid of the body's top 18% band, in the
  finalized coordinate system.
- `target_head_x`/`target_head_y`: technique A's head-slot world center at `t = i * 0.1`,
  via `spinerig.render._placements()` + `world_to_canvas(cx, cy, REFERENCE_BOX, 1.0, 0)`.
  A's own head position moves substantially during `double_jump` (canvas ~(737.5, 514.5)
  at t=0 to ~(778.6, 483.3) at t=0.2, back through ~(767.4, 491.6) at t=0.3 to ~(753.4,
  502.7) by t=0.4) -- the tuck's hip-lift keyframe (`hips: (0, 30)` in `anims.py`) actually
  raises the whole body, so B's frames anchor to visibly different head positions across
  the sequence, not a near-stack the way `fall`'s frames do.
- Records: `trial-b/frames/double_jump-finalize-record.json`, now covering all 5 frames.
  Every frame's trim/rescale is a `provenance edit` on both PNGs; each scarf's stale
  `inputs[0]` hash reference (from its body frame's post-trim hash change) was corrected
  via a `human_edits` entry, same as `fall`.

**Incremental finalize.** As with `fall`, `finalize_anim.py` was made to merge into the
existing finalize record and skip indices already present in it, so adding frames 2-4
never re-trims/re-rescales the already-committed frames 0-1 (see `fall.md`'s "Incremental
finalize" note for the full reasoning; the same script serves both animations).

## Honest read

- **Style/design/proportions**: consistent with `run` and with `fall`; no off-model drift
  across all 5 frames.
- **Scarf**: all 5 scarf frames are a single opaque, neutral-gray flowing shape (RGB
  channels within 3 of each other everywhere the scarf is opaque, i.e. genuinely neutral
  gray), no ghosting.
- **No rotation**: confirmed on all 5 frames -- she stays upright and facing right
  throughout; the tuck reads as knees-pulled-up-and-forward rather than a spin or flip.
- **Tuck tightness (the concrete gap the previous session named)**: frame 1's tuck was
  judged looser than the brief ("a folded, seated-looking tuck rather than a tight
  cannonball"). Frame 2 was painted explicitly tighter -- both knees pulled up sharply
  against her chest, heels drawn in close to her hips -- and reads as a materially more
  compact silhouette than frame 1 in a side-by-side montage: frame 2 is the shortest,
  roundest frame in the whole 5-frame sequence, both at full size and at ~100 px. The
  "quick tuck -> hold -> release -> reopen" beat the rig's own keyframes describe is now
  present as a real 5-beat progression rather than one frame standing in for the rest.
- **Pose distinctness**: viewed as a montage against `fall`'s row and against `jump`'s row
  (fetched from `phase1/violet-b-jumpland` for comparison) at both full size and ~100 px,
  `double_jump` reads clearly differently from both. It never shows `fall`'s wide,
  arms-spread-at-shoulder-height, robe-trailing-upward silhouette. Its held final frame
  (4) shares `jump`'s and `fall`'s frame-0 underlying rig pose (`RISE`, by the rig's own
  design -- see `rig-src/anims.py`'s comment: "airborne rising pose shared by jump's end,
  fall's start, double_jump's end"), but is painted with both arms swept symmetrically to
  the sides rather than `jump`'s one-arm-reaching-forward/down read, and the sequence as a
  whole is unmistakable: no other animation in this set compacts into a tight knees-to-chest
  tuck at its midpoint.

## For the integrator

`fall` and `double_jump` are both now complete at 5/5 frames, finalized, provenance-clean,
committed and pushed to `phase1/violet-b-falldj`. No per-animation contact-sheet row or GIF
was built for either -- out of scope per the assignment; the integration step assembles all
seven animations into one contact sheet and per-animation GIFs for the critic.
