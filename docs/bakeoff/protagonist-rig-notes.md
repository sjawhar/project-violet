# Protagonist rig — WIP measurement notes (not final, THROWAWAY)

Checkpoint handoff. This file records pixel measurements taken from
`assets/bakeoff/protagonist/concept/violet-turnaround.png` (1536×1024, right-side view is the
right half, right-side-view figure roughly x ∈ [948, 1450]) so the next agent does not have to
redo the analysis. **No part images or rig.json have been changed yet** — this session got only
as far as measurement before a checkpoint interrupt (laptop shutdown). Method: `uv run --with
pillow --with numpy python3 <script>` cropping the right-side view with a labelled 5px/25px grid
overlay and reading landmark rows by eye (scripts were throwaway, not committed).

## Landmarks measured (absolute px in the 1536×1024 concept PNG, right-side view)

| Landmark | y (px) | Confidence |
|---|---|---|
| head top (crown of hood) | ≈68 | firm — mask bbox top edge (~82 with a stricter threshold) matches the visible hood crown |
| head/neck bottom → shoulder line (torso top) | ≈295–300 | firm — the rounded shoulder curve becomes visible starting here |
| waist | **not measured** — the sash/belt visible in the FRONT view (left half) is occluded by the trailing scarf in the side view. Next step: crop the front view's belt band (script `analyze5.py`-style, front-view fg cols found via mask, box e.g. `(cols.min()-10, 340, cols.max()+10, 460)`) and take that band's fraction of the *front* view's own total height, then apply that fraction to the *side* view's total height (895 px, see below) for scale-consistency, since the task wants the side view specifically. I was one tool call away from this front-view crop when interrupted. |
| hand/fingertip (forearm+hand visible past the sleeve cuff) | ≈520 (wrist/cuff) – 600 (fingertips) | medium — hand shape clearly visible in the `waist_grid` crop, but the wrist/cuff boundary is a soft estimate |
| outer robe hem (bottom of the "hips" skirt part, before the ankle wrap) | ≈880–895 | medium — a few drape-fold cusps extend a little lower (~900–910); 880–895 is the main hemline |
| ankle wrap top (grayish leg-wrap begins, per brief "bare feet or soft wraps") | ≈920 | firm |
| ankle wrap → bare foot | ≈950 | firm |
| foot sole / floor contact | ≈963 | firm — the floor shadow (a separate horizontal band, constant width ≈460px across the sampled x-range) starts plateauing right after this, at row ≈968+ |

**Total side-view height ≈ 963 − 68 = 895 px** (crown to sole). Cross-check the front view's own
total height before trusting this number for the final scale — I ran out of time to do that
cross-check (`analyze5.py`, not yet executed/read).

## What is NOT directly measurable from the turnaround (occluded by robe/sleeve)

- **Elbow position** (upper vs. lower arm split): the sleeve runs the full arm length in this
  painting; only the hand emerges past the cuff. No pixel landmark exists for the elbow. Plan:
  use the *total* shoulder(≈295)-to-wrist(≈520) span and split it by a standard human proportion
  (upper arm ≈ 55%, forearm ≈ 45% of shoulder-to-wrist, since the actual human elbow sits a bit
  past the midpoint) rather than a 50/50 split. State this as an inferred split in the PR, not a
  measured one.
- **Knee position** (upper vs. lower leg split): the thigh is entirely under the robe hem in the
  turnaround (compare the already-generated `leg_front_upper.png`/`leg_back_upper.png` parts,
  which show the thigh-to-knee wrap in isolation but at their own, currently-inconsistent, scale).
  The turnaround gives only the *total* leg length (hip/waist-y down to floor-y = 963), not the
  thigh/shin split. Plan: same approach as the arm — infer a standard human ratio (thigh ≈ 53–55%
  of hip-to-floor, shin+foot ≈ 45–47%) rather than measuring a knee pixel that isn't drawn.

## Known part problems (from PR #28, still unfixed at checkpoint)

1. **Scarf** (`scarf1.png`, `scarf2.png`, `scarf3.png`): each is a whole flowing scarf tail
   (long, twisted, frayed at the bottom, saturated red) — needs to become ONE straight segment
   each (~1/3 of a full scarf tail's length), painted **neutral light gray** (lanes tint by
   multiplying: gray at rest, red/green when a color is active — saturated red art can't become
   green by multiplication). Only `scarf3` (the tail end) should fray.
2. **`leg_back_upper.png`**: currently reads as a bare skin thigh next to a separate drape (looks
   like "an arm under a drape", not a wrapped leg). Regenerate using `leg_front_upper.png`'s
   working wording (a thigh fully wrapped in the robe's muted fabric, tapering to the knee) —
   `leg_front_upper.png` itself is fine and already reviewed as good.
3. **Scale mismatch**: every part was generated independently into its own 1024×1024 canvas at an
   arbitrary zoom, so there is no shared pixel scale across parts (per the current README table:
   `arm_back_lower` 962×992 vs. `head` 903×947 — the forearm is nearly as big as the head; `head`
   903 wide vs. `torso` 529 wide — the head is wider than the torso). Every part needs a per-part
   resize (different factor per part, since none share a common origin scale) so that, once
   resized, every part's real-world length matches the turnaround's true proportions expressed in
   one shared "rig units" coordinate system (target total character height ≈ 1000 rig px). Record
   every resize as `provenance edit <png> --by <model> --description 'rescaled to shared rig
   proportions (see docs/bakeoff/protagonist-rig-notes.md)'`.

## Not yet started

- No part image has been regenerated or resized.
- No `assets/bakeoff/protagonist/rig-src/rig.json` exists yet.
- `tools/spinerig generate`/`render` (already on master, merged into this branch via the merge
  commit below) have not been run against any rig for this character yet.

## Repo state at checkpoint

Working copy is a merge commit on top of `0a365525` (PR #28's current head, the 14 unfixed parts)
and `master`'s tip at the time (`e79343e0`, which already has `tools/spinerig generate|render` and
`docs/bakeoff/character-rig.md` merged — PR #28's original base predates those, so the merge was
needed to get `spinerig render` for verification). The merge was clean (no conflicting paths). See
this commit's parents for exact shas.
