# Protagonist body parts and rig (THROWAWAY)

> Everything under `assets/bakeoff` exists only to run the Phase 1 bake-off. Mechanics are undecided
> (decision 0009); nothing here is canon.

Violet's Spine-JSON cutout rig (Phase 1 Tasks 4 and 5 of
`docs/superpowers/plans/2026-09-27-phase-1-bake-off.md`), painted from the turnaround Sami approved
in #19 (`concept/violet-turnaround.png`):

- `parts/`: fourteen painted body parts, all at one shared scale (below).
- `rig-src/rig.json`: the `violet-rig` v1 description (bones, pivots, draw order, scarf, animations).
  It is written by the THROWAWAY scripts beside it, so edit those scripts rather than the JSON.
  The layout and the reasoning behind each value are in `docs/bakeoff/protagonist-rig-notes.md`.
  - `mkrig.py`: bones, parts, draw order and scarf config; it runs the other scripts.
  - `anims.py`: the seven animations.
  - `ground.py`: puts the soles on the floor.
  - `feet.py`: measures foot heights per frame.
- `rig/violet.json` + `rig/violet.meta.json`: `spinerig generate`'s output, the Spine 4.3 JSON subset
  every lane reads (`docs/bakeoff/character-rig.md`). Regenerate it with
  `uv run --project tools/spinerig spinerig generate assets/bakeoff/protagonist/rig-src/rig.json --out assets/bakeoff/protagonist/rig/violet.json`.
- `preview/<anim>.gif`: `spinerig render` playback of each animation at `--scale 0.5`.

The rig references every part by file name, so renaming a part means updating `rig-src/mkrig.py`
too.

## Painted sequence preview

The glow-up's painted sequence is a review candidate, separate from the cutout
reader used by the game lanes. Its scarf and body are separate tintable layers.
`glow-up/scarf_attachments.json` records the visually checked neck and knot
landmarks for all 43 painted frames, bound to the source PNG hashes. A shared
canvas or crop origin is not an attachment point.

After finalizing frames, bind and validate them before rendering:

```sh
uv run --project tools/spinerig python assets/bakeoff/protagonist/glow-up/apply_scarf_attachments.py apply
uv run --project tools/spinerig python assets/bakeoff/protagonist/glow-up/shoot_b.py \
  --rig assets/bakeoff/protagonist/rig/violet.json \
  --out out/violet-attached-preview
```

The renderer refuses stale or missing bindings. Changed artwork requires new
visually verified landmarks, not updated hashes alone. The scarf is drawn above
the clothing to preserve its neck wrap. Historical round captures are kept
unchanged; `glow-up/attachment-fix/` shows the attachment correction separately.

## Changing an animation or the rig

Run everything from the repository root:

1. Edit `rig-src/anims.py` to change an animation (angles are deltas on the setup pose; its header
   explains the sign conventions). Edit `rig-src/mkrig.py` for bones, pivots, draw order or the scarf.
2. Rewrite `rig.json`:
   `uv run --project tools/spinerig --with numpy python assets/bakeoff/protagonist/rig-src/mkrig.py`.
   It re-solves the grounded feet each time. To print every animation's per-frame foot heights (0 is
   the floor), run `feet.py` the same way.
3. Regenerate the rig:
   `uv run --project tools/spinerig spinerig generate assets/bakeoff/protagonist/rig-src/rig.json --out assets/bakeoff/protagonist/rig/violet.json`.
4. Re-render each changed animation, then copy the GIF over `preview/<anim>.gif`:
   `uv run --project tools/spinerig spinerig render assets/bakeoff/protagonist/rig/violet.json --parts assets/bakeoff/protagonist/parts --anim <anim> --out /tmp/<anim> --scale 0.5`.
5. Refresh the provenance records of everything that changed: the edited script, `rig.json`,
   `violet.json`, `violet.meta.json` and the re-rendered GIFs. The commands are in each sidecar's
   fields. Then run `provenance check`.

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
| `arm_back_upper.png` | 82×204 | upper arm in the robe sleeve, shoulder to a rounded elbow (back; repainted) | 0.295 |
| `arm_back_lower.png` | 76×227 | forearm in the sleeve from the elbow to the cuff, relaxed hand below (back; repainted) | 0.25 |
| `arm_front_upper.png` | 82×203 | upper arm in the robe sleeve, shoulder to a rounded elbow (front; repainted) | 0.315 |
| `arm_front_lower.png` | 69×232 | forearm in the sleeve from the elbow to the cuff, relaxed hand below (front; repainted) | 0.25 |
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
- **Arms (all four):** in the first rig the upper-arm piece was the whole bell sleeve, shoulder to
  cuff. That is about twice the upper-arm bone, so the elbow sat halfway down a stiff piece. The
  forearm turned underneath it and poked out of the cuff at an angle, which read as a broken wrist.
  `docs/bakeoff/protagonist-rig-notes.md` has the frames that show it. The four arm parts are
  repainted:
  - Each upper arm is the sleeve from the shoulder to a closed, rounded elbow.
  - Each forearm is the rest of the sleeve, from the elbow to the cuff, with a relaxed hand below
    it, painted straight along the bone.
  - The rounded elbow end draws over the forearm's top, and its centre is the pivot, so the seam
    stays hidden at any bend.
- **Scale:** every part now shares the one scale above. The first pass's parts each filled their own
  1024 canvas, so the forearm was nearly as big as the head. The old trims were also inflated by faint
  alpha specks: `magick -trim` kept pixels with alpha 1–8.

## Rejects and regeneration count

Rig pass: five `gen image` calls, none rejected: `scarf1`, `scarf2`, `scarf3`, `leg_back_upper`,
`hips`. Arm round: six calls.
- Kept: the two forearms (first try) and the two upper arms (second try).
- Rejected: the two first-try upper arms. The prompt asked for no cuff, but both came back as bell
  sleeves flaring to a wide open cuff at the elbow. That would leave a sleeve opening halfway down
  every arm.

Each result was checked by eye against the turnaround before use: isolated part, facing right, real
alpha, and the requested shape and colour. The scarf crops and gray conversion above are
post-processing on the kept images, not rejections. The earlier painting pass had one safety-filter
rejection (`leg_front_upper`'s first prompt, "bare skin or soft wrap",
`req_35b66a8b163840a4b19de583e1f83e59`, no image and no charge).

## Spend

OpenAI reports token usage per call, not dollars. The arm round logged each response's `usage`: every
call was 1,536 image-input, 102–126 text-input and 7,024 image-output tokens. At the pricing page's
`gpt-image-2` rates ($8 / $5 / $30 per million), that is $0.2236 per call.

- Arm round (from the reported usage): 6 calls, $1.34. Kept $0.89, rejected $0.45.
- Earlier passes: usage was not logged. The same per-call figure gives 14 calls ≈ $3.13 for the first
  painting pass and 5 calls ≈ $1.12 for the rig pass. They were first estimated at $0.17 per call.
- Total: ≈ $5.59.
