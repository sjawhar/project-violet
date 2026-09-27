# Protagonist body parts (THROWAWAY)

> Everything under `assets/bakeoff` exists only to run the Phase 1 bake-off. Mechanics are undecided
> (decision 0009); nothing here is canon.

Fourteen painted body-part images for Violet's Spine cutout rig (Phase 1 Task 4, Steps 3-4 of
`docs/superpowers/plans/2026-09-27-phase-1-bake-off.md`), painted from the turnaround Sami approved
in #19 (`concept/violet-turnaround.png`). Task 5's `tools/spinerig` rig (`assets/bakeoff/protagonist/rig-src/rig.json`)
references every file here by name — do not rename them without updating that rig.

## Parts

Each part is one command: `gen image --provider openai --model gpt-image-2 --background transparent
--input concept/violet-turnaround.png --prompt "Only <part description> ... side view facing right,
same painted style and palette ... transparent background" --size 1024x1024`, generated at 1024x1024
then trimmed to its opaque bounding box (`magick <part>.png -trim +repage <part>.png`, recorded as a
`provenance edit --description 'trimmed transparent margin'`) so the rig's bone-relative pivots (a
fraction 0-1 of the trimmed image) stay tight.

| File | Final size (trimmed) | Description asked for |
|---|---|---|
| `head.png` | 903×947 | hooded head and neck |
| `torso.png` | 529×870 | robe torso, shoulders to waist |
| `hips.png` | 825×911 | robe skirt, waist to knee line |
| `arm_back_upper.png` | 546×792 | upper arm, shoulder to elbow (back) |
| `arm_back_lower.png` | 962×992 | forearm and hand (back) |
| `arm_front_upper.png` | 419×819 | upper arm, shoulder to elbow (front) |
| `arm_front_lower.png` | 898×947 | forearm and hand (front) |
| `leg_back_upper.png` | 594×846 | thigh under the robe hem (back) |
| `leg_back_lower.png` | 577×858 | shin and foot (back) |
| `leg_front_upper.png` | 505×723 | thigh under the robe hem (front) |
| `leg_front_lower.png` | 656×895 | shin and foot (front) |
| `scarf1.png` | 781×942 | one straight scarf segment |
| `scarf2.png` | 811×951 | one straight scarf segment |
| `scarf3.png` | 849×966 | one straight scarf segment |

All 14 were generated at 1024×1024 before trimming; every part carries a `<part>.png.provenance.json`
sidecar (`provenance check assets/bakeoff/protagonist` passes).

**Model:** `gpt-image-2` (OpenAI), `--quality high` (the tool's default), `--background transparent`.
Every part used the approved turnaround as its only `--input`.

**Scarf color:** the plan's protagonist brief describes the scarf as gray at rest and saturated only
when a color is active; the approved turnaround (#19) instead painted the scarf a saturated red
throughout (Sami: "love it"). The three scarf segments here follow the approved concept art, not the
brief's gray default — they are the saturated scarf red so Task 5's rig matches what Sami signed off
on.

## Rejects

- `leg_front_upper.png`: the first attempt (identical prompt to `leg_back_upper.png`, "bare skin or
  soft wrap") was rejected by OpenAI's safety system (`req_35b66a8b163840a4b19de583e1f83e59`, no
  image, no charge). Retried with "wrapped in the same muted fabric as the robe" instead of "bare
  skin or soft wrap"; the second attempt succeeded and is what ships. `leg_back_upper.png`'s original
  wording was left as-is since it never triggered the filter.
- No other part needed a retry; all 13 remaining parts passed on the first generation (isolated to the
  named part, facing right, matching the turnaround's palette, real alpha, and — for the scarves —
  the saturated red) on visual review.

## Estimated spend

15 `gen image` calls total: 14 that produced a billable image plus the one safety-rejected
`leg_front_upper` attempt above (rejected before generation, not expected to be billed). At
`gpt-image-2`, `--quality high`, `1024x1024` (~$0.17/image per `tools/gen/README.md`'s pricing
pointer — OpenAI's API does not report a dollar cost directly, so this is an estimate, not a billing
export): **14 × $0.17 ≈ $2.38.**
