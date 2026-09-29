# Technique B `double_jump` (THROWAWAY, Phase 1 bake-off) -- PARTIAL, 2 of 5 frames

Ran out of tool-call budget before finishing. **Frames 0-1 of a planned 5 are painted,
finalized and committed; frames 2-4 (the held tuck, the release, and the held final
"opened back out" frame) are not yet generated.** Everything below describes what exists.

## Plan

`rig-src/anims.py`: `A["double_jump"] = {"duration": 0.5, "loop": False, ...}` -- plays
once and holds its last frame. Planned **5 frames, evenly spaced 0.1 s apart** (`t = 0,
0.1, 0.2, 0.3, 0.4`, last frame held from 0.4 through 0.5 and beyond) -- 10 fps, inside the
assignment's 8-12 fps guidance. Matches the rig's own beat: a quick snap into a tuck by
0.08 s, held to 0.22 s, opening back out to the rising pose by 0.5 s.

Design brief (assignment, and Sami's explicit ruling): a quick tuck, knees up, arms out,
scarf flaring, **no flip or rotation** -- clearly different from a rising jump (peer lane)
and from fall's open/spread silhouette.

| # | t (s) | Pose (planned) | Status |
|---|---|---|---|
| 0 | 0.00 | Ordinary rising part of a jump, a beat before the extra push: legs extended below/behind, torso upright, arms starting to swing forward at shoulder height. | **Done** |
| 1 | 0.10 | Tight tuck just triggered: knees pulled up, silhouette compact, arms swept out to the sides (not overhead), scarf flaring. No rotation. | **Done** |
| 2 | 0.20 | Tuck held for a beat: same compact silhouette, scarf fully fanned out. | Not generated |
| 3 | 0.30 | Tuck beginning to release: knees dropping back down, torso straightening, scarf settling. | Not generated |
| 4 | 0.40 | Held pose: opened back out to the normal airborne rise. This is what plays whenever the game holds `double_jump` past 0.4 s. | Not generated |

## Generation

Same recipe as `fall` (see that file for the shared-defect story) and the trial's `run`:
two `gen image` calls per frame, `--provider openai --model gpt-image-2 --quality high
--size 1024x1024 --background transparent`.

- **Body**: `--input` the turnaround plus one run body anchor (`run-body-02.png`). Both
  committed frames used this 1-anchor recipe (the 2-anchor recipe was abandoned mid-lane
  after `fall`/this animation both hit the vignette-background defect more often with it --
  see `fall.md`).
- **Scarf**: `--input` that frame's own finalized body PNG plus `parts/scarf1.png`.

Full prompt text is in each frame's own `.provenance.json`.

### Calls and rejections

| Frame | Body calls | Rejected (why) | Scarf calls | Rejected |
|---|---|---|---|---|
| 0 | 3 | 2 -- 2-anchor recipe, dark vignette background (not transparent) both times | 1 | 0 |
| 1 | 1 | 0 (already on 1-anchor recipe by this point) | 1 | 0 |
| **Total (frames 0-1)** | **4** | **2** | **2** | **0** |

**6 `gen image` calls for frames 0-1, 2 rejected, 4 kept.** Frames 2-4 not attempted.

### Spend estimate

6 calls x ~$0.22/call = **~$1.32 est.** for `double_jump` alone. Combined with `fall`'s 8
calls (~$1.76), this lane's total spend was **14 calls, ~$3.08 est.**, well under the
~$6 cap -- the stop was the request-budget wrapping up the session, not the dollar cap.

## Post-processing

`trial-b/finalize_anim.py double_jump`, run once over the 2 raw generated frames present.
Same trim/scale/anchor approach as `fall.md` describes in detail:

- Shared alpha>8 bbox union trim between body and scarf.
- Rescaled by run's own `RIG_PER_RAW = 1.128227381210675`, unchanged.
- `head_x`/`head_y`: local alpha-weighted centroid of the body's top 18% band, in the
  finalized coordinate system.
- `target_head_x`/`target_head_y`: technique A's head-slot world center at `t = i * 0.1`,
  via `spinerig.render._placements()` + `world_to_canvas(cx, cy, REFERENCE_BOX, 1.0, 0)`.
  Unlike `fall`, A's own head position moves substantially during `double_jump` (canvas
  ~(737.5, 514.5) at t=0 to ~(776.7, 483.0) at t=0.1-0.2, back toward ~(751.5, 502.6) by
  t=0.4) -- the tuck's hip-lift keyframe (`hips: (0, 30)` in `anims.py`) actually raises
  the whole body, so B's frames 0-1 anchor to visibly different head positions, not a
  near-stack the way `fall`'s frames do.
- Records: `trial-b/frames/double_jump-finalize-record.json` (frames 0-1 only). Every
  frame's trim/rescale is a `provenance edit` on both PNGs; each scarf's stale
  `inputs[0]` hash reference (from its body frame's post-trim hash change) was corrected
  via a `human_edits` entry, same as `fall`.

## What isn't committed

- Frames 2, 3 and 4 (body + scarf, and their finalize-record entries) -- in particular
  frame 4, the pose the game actually holds indefinitely once `double_jump` finishes.
- A per-animation contact-sheet row / GIF -- out of scope per the assignment.

## Honest read

- **Style/design/proportions**: consistent with `run` and with `fall`; no off-model drift.
- **Scarf**: both scarf frames are a single opaque, neutral-gray flowing shape, no
  ghosting.
- **No rotation**: confirmed on both frames -- she stays upright and facing right in both;
  the tuck reads as knees-pulled-up-and-to-the-side rather than a spin or flip.
- **Pose distinctness**: frame 1's tuck is visibly more compact (knees drawn up, shorter
  overall silhouette) than either `fall`'s open/spread frames or the rising-jump register
  frame 0 shares with `fall`'s own frame 0 -- the differentiation the critic's round-0 gap
  called for is present between `double_jump`'s tuck and the other two air states. Frame
  1's knee-tuck is looser than the "heels near her hips" the prompt asked for (a folded,
  seated-looking tuck rather than a tight cannonball); acceptable but not the strongest
  possible read of "quick tuck," and **frame 2 (the tuck held) was meant to reinforce this
  reading more strongly and does not yet exist.** As with `fall`, the animation is
  incomplete: the sequence currently jumps from "about to tuck" straight into a hold
  (frame 1 stands in for the whole rest of the state machine's-worth of poses), which
  under-sells the "quick tuck -> hold -> release -> reopen" beat the rig's own keyframes
  describe.

## For the integrator

Both `fall` and `double_jump` are short 2-3 of a planned 5 frames. If the contact sheet
needs all seven animations to have a complete frame set before assembly, this lane's
output is not ready for that step as-is -- either the remaining frames need painting (by a
successor session, following the recipe and defect-avoidance notes above) or the
integration step needs to decide how to handle a lane that stopped early.
