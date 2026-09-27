# Protagonist body parts and rig (THROWAWAY)

> Everything under `assets/bakeoff` exists only to run the Phase 1 bake-off. Mechanics are undecided
> (decision 0009); nothing here is canon.

Violet's Spine-JSON cutout rig (Phase 1 Tasks 4 and 5 of
`docs/superpowers/plans/2026-09-27-phase-1-bake-off.md`), painted from the turnaround Sami approved
in #19 (`concept/violet-turnaround.png`):

- `parts/`: fourteen painted body parts, all at one shared scale (below).
- `rig-src/rig.json`: the `violet-rig` v1 description (bones, pivots, draw order, scarf, animations).
  Its layout and the reasoning behind each value are in `docs/bakeoff/protagonist-rig-notes.md`.
- `rig/violet.json` + `rig/violet.meta.json`: `spinerig generate`'s output, the Spine 4.3 JSON subset
  every lane reads (`docs/bakeoff/character-rig.md`). Regenerate it with
  `uv run --project tools/spinerig spinerig generate assets/bakeoff/protagonist/rig-src/rig.json --out assets/bakeoff/protagonist/rig/violet.json`.
- `preview/<anim>.gif`: `spinerig render` playback of each animation at `--scale 0.5`.

The rig references every part by file name, so renaming a part means updating `rig-src/rig.json`
too.

## Parts

Each part was one `gen image --provider openai --model gpt-image-2 --background transparent --input
concept/violet-turnaround.png --size 1024x1024` call (quality `high`, gen's default). Its prompt is in its
sidecar. Every later step is recorded as a `provenance edit` in that sidecar: the trim to the alpha > 8
bounding box, the scarf crops and gray conversion, the head collar recolor, and the rescale.

| File | Final size (px) | What it shows | Scale factor |
|---|---|---|---|
| `head.png` | 200×216 | hooded head, neck, gray collar | 0.335 |
| `torso.png` | 126×274 | robe torso with the dark sash | 0.40 |
| `hips.png` | 256×581 | ankle-length robe skirt, darker hem (regenerated) | 0.639 |
| `arm_back_upper.png` | 162×315 | bell sleeve, shoulder to cuff (back) | 0.40 |
| `arm_back_lower.png` | 164×177 | forearm sleeve, forearm and hand (back) | 0.235 |
| `arm_front_upper.png` | 164×325 | bell sleeve, shoulder to cuff (front) | 0.40 |
| `arm_front_lower.png` | 192×108 | forearm sleeve, forearm and hand (front) | 0.223 |
| `leg_back_upper.png` | 109×312 | thigh wrapped in robe fabric, tapering to the knee (regenerated) | 0.352 |
| `leg_back_lower.png` | 137×263 | wrapped shin and bare foot (back) | 0.31 |
| `leg_front_upper.png` | 116×321 | thigh wrapped in robe fabric, tapering to the knee | 0.476 |
| `leg_front_lower.png` | 141×293 | wrapped shin and bare foot (front) | 0.33 |
| `scarf1.png` | 79×217 | straight neutral-gray scarf segment, root end (regenerated) | 0.62 |
| `scarf2.png` | 79×217 | straight neutral-gray scarf segment, middle (regenerated) | 0.62 |
| `scarf3.png` | 111×260 | straight neutral-gray scarf segment, frayed tail end (regenerated) | 0.65 |

The scale factor applies to the part after its trim (and, for the scarves, after the crop).

### Shared scale: how the sizes were derived

Target: the figure is 1000 rig px from the crown of the hood to the sole, standing in the setup pose,
with the root at the feet. `violet.meta.json` records `height_px` 990.5, the setup pose's bounding box.

**Measured** on the turnaround's side view (1536×1024 PNG, the right-hand figure), read off a 2× crop
with a 10 px grid:

| Landmark | Turnaround y (px) | Rig px below the crown |
|---|---|---|
| hood crown | 80 | 0 |
| chin | 235 | 176 |
| shoulder line | 295 | 244 |
| sash | 395–432 | 358–400 |
| wrist (where the hand leaves the sleeve) | ~540 | 522 |
| fingertips | 602 | 593 |
| robe hem | 885–900 | 914–931 |
| sole | 960 | 1000 |
| foot, toe to heel | 108 px long | 123 px long |

Crown to sole is 880 turnaround px, so the scale is 1000 / 880 = 1.136 rig px per turnaround px.
`docs/bakeoff/protagonist-rig-notes.md`'s first pass had 68 → 963 (895 px). That used a looser alpha
threshold at the hood crown; the same notes give ~82 for a strict threshold, and the strict edge is
the one the painted hood matches.

**Inferred.** The robe hides the elbow, the hip joint and the knee, so these come from standard
proportions, not pixels:

- Elbow: upper arm 55% and forearm 45% of the 278 px from shoulder to wrist, so bones of 153 and 125.
- Hip joint: 460 px below the crown (540 above the floor), 82 px below the sash centre.
- Knee: thigh 54% of the 540 px from hip to floor, so bones of 292 and 248. Each lower-leg part is
  sized by its foot, so the foot matches the turnaround's.

Each part's factor maps one painted span onto its rig span; each sidecar's rescale edit names the span
it used. The head, torso and sleeves were then fitted by overlaying the setup pose on the turnaround's
side view (`docs/bakeoff/protagonist-rig/setup-over-turnaround.png`). The painted hood is fuller than
the turnaround's, so the head was fitted to the crown, face and chin rather than to the hood's width.

## Fixes over the first painting pass

- **Scarf (`scarf1-3`):** the first versions were each a whole red flowing scarf. They are now three
  straight segments painted neutral light gray, because lanes tint the scarf by multiplying and red
  art can't become green that way (`docs/bakeoff/character-rig.md`, brief: "gray when no color is
  active"). Only `scarf3` frays. gpt-image-2 painted each segment as a long, thin strip (about 1:7), so
  each was cropped to a third of the scarf's length and about 1:2.8 proportions. It was then converted
  to exact neutral gray (the paint came out warm beige, mean saturation 0.09). The cropped ends were
  feathered so the joints blend where the segments overlap.
- **Head collar:** the red scarf collar at the head's neck was recolored to the same neutral gray.
  Otherwise the collar would stay red while the scarf chain turns green.
- **`leg_back_upper`:** the first version read as a bare arm beside a drape. It was regenerated with
  `leg_front_upper`'s exact prompt (a thigh wrapped in the robe's fabric, tapering to the knee).
- **`hips`:** the first version was a knee-length skirt flaring to 0.86:1 width to height. At the
  turnaround's ankle-length hem that made a skirt 488 px wide against the turnaround's ~235.
  Regenerated as an ankle-length robe skirt with a darker hem and gentle flare, 0.44:1, close to the
  turnaround's 0.42:1.
- **Scale:** every part now shares the one scale above. The first pass's parts each filled their own
  1024 canvas, so the forearm was nearly as big as the head. The old trims were also inflated by faint
  alpha specks: `magick -trim` kept pixels with alpha 1–8.

## Rejects and regeneration count

Five new `gen image` calls in the rig pass, none rejected: `scarf1`, `scarf2`, `scarf3`,
`leg_back_upper`, `hips`. Each result was checked by eye against the turnaround before use: isolated
part, facing right, real alpha, and the requested shape and colour. The scarf crops and gray
conversion above are post-processing on the kept images, not rejections. The earlier painting pass had
one safety-filter rejection (`leg_front_upper`'s first prompt, "bare skin or soft wrap",
`req_35b66a8b163840a4b19de583e1f83e59`, no image and no charge).

## Estimated spend

OpenAI's API reports no dollar cost, so these are estimates at ~$0.17 per `gpt-image-2` high-quality
1024×1024 image (`tools/gen/README.md`'s pricing pointer), plus the reference image's input tokens:

- First painting pass: 14 billable images, about $2.38.
- Rig pass: 5 billable images, about $0.85–1.00.
- Total: about $3.25–3.40.
