# Blind Critic Comparison: Set A vs Set B

## Method note (read this first)

Before scoring, I decoded every GIF frame-by-frame (accumulating frames per the GIF spec — a naive per-frame decode produces spurious solid-gray flicker artifacts that are **not** real; I caught and discarded that false read) and diffed A against B pixel-for-pixel across all 8 poses, plus the two master contact-sheet PNGs.

**Finding: A and B are the same character art, not two different designs.** Average pixel difference is ~0.7–1.0 on a 0–1020 scale (RGBA channel sum) for every animation, including the un-recompressed contact-sheet PNGs. The only place the (tiny) differences concentrate is the hood/face gradient, consistent with palette-quantization noise in separately-exported GIFs, not an intentional redesign. Frame counts, timings, poses, proportions, palette, and shading are identical in every pose I inspected at up to 8x zoom (idle, run, jump, fall, double_jump, dash, land). I could not find a single frame where the two sets are visually distinguishable to a viewer.

Given that, every axis below is scored **"same"** for the head-to-head call, and the gap list is identical for both sets because it is the same artwork.

## Axis winners

| Axis | Winner |
|---|---|
| visual_quality | same |
| character_appeal | same |
| color_readability | same |

## Scores (1–5, 5 = GRIS/Planet of Lana bar)

| Set | visual_quality | character_appeal | color_readability |
|---|---|---|---|
| A | 3 | 2 | 3 |
| B | 3 | 2 | 3 |

Reasoning, grounded in what's actually on screen:
- **visual_quality (3/5):** The cloth shading itself is a competent soft painterly gradient with paper-grain texture (not flat-shaded), and the scarf's trailing secondary motion during run/dash reads well. But close inspection turns up unfinished-looking details (see gaps) that a GRIS/Lana-level asset wouldn't ship with.
- **character_appeal (2/5):** Proportions and the flowing-scarf idea are appealing in concept, but the performance is flat — see gaps. This is the weakest axis.
- **color_readability, scarf+silhouette only (3/5):** The outline shape (rounded hood, single bell skirt, one trailing scarf tail) is distinct and would silhouette-read fine. The scarf itself has strong value contrast. But I measured the robe body at luminance ≈124 against this sheet's own neutral-gray backdrop at ≈127 — a ~1% difference — so on anything but a pure neutral floor, most of the body will read as one dark blob with the scarf/hair as the only strong marks, not a fully legible silhouette.

## Three biggest gaps vs. the bar (identical for Set A and Set B)

1. **The face never changes expression across any of the 8 poses.** I cropped and compared the eye/brow/mouth region across idle, jump, fall, land, dash, and double_jump at 6x zoom — it is the same neutral eye/mouth line copy-pasted into every pose, including the fall and the dash. Planet of Lana keeps Lana's face legible and reactive even at small scale; GRIS compensates for a hidden face with dramatic full-body pose changes this sprite doesn't have either. Action: give land a squint/wince, dash a determined brow, fall a wider eye — at minimum 3 distinct face states.
2. **Hands are blank cone shapes with a single skin-toned point, no fingers or thumb.** Zoomed 8x on the jump reach pose: each hand is a triangular sleeve-cuff with one pale sliver poking out — no palm, no finger separation. This is most visible exactly when the pose calls attention to the hands (jump/double_jump/dash reach poses). Action: add at minimum a thumb break and 2–3 finger silhouette notches, or commit to fully-hidden sleeves if fingers aren't intended.
3. **The robe body sits at nearly the same luminance as a neutral gray backdrop (measured 124 vs. 127, a ~1% difference), and there's a lighter tan patch on the mid-right skirt (roughly hip-to-thigh) that cuts across the fabric folds at a hard, straight-ish edge** — it doesn't follow the drape and reads as a leftover paint/texture seam rather than a fold. Action: darken/warm the patch to match the surrounding gradient, and push the robe's overall value down or up so it clears the midtone band the game's neutral surfaces are likely to occupy — right now only the hair and scarf will reliably pop against a mid-value environment.

Not scored, but worth flagging since the axis definition calls out red/green: this character carries no red or green anywhere in the design (it's brown/tan/white/skin only), so the red/green resonance-wall contrast this axis is ultimately meant to protect hasn't been tested yet by this asset — that's a gap in coverage, not a defect in what's shown.
