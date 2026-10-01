# Round 5 critique (technique B value pass, against round 4)

A fresh critic subagent, spawned as `astra` but run by omp on **anthropic/claude-opus-5-5** (from the transcript's model_change event). Blind: neutral file names, letters from Python's `random`, and the verbatim prompt from rounds.md. **Letter map: A = round 4 (kept), B = round 5 (new).** Its reply, verbatim:

## verdict

- visual_quality: B
- character_appeal: same
- color_readability: B

## scores

| Set | visual_quality | character_appeal | color_readability |
|---|---|---|---|
| A | 2 | 3 | 2 |
| B | 3 | 3 | 3 |

## axis_rationale

- visual_quality: Both sets use the same drawings. Every frame has the same poses, bounding boxes, frame count and timing (for example, run is 8 frames at 90/60/60/60/90/60/60/60 ms in both). The only difference is tone. B is a contrast-expanded version of A: per channel, B ≈ 1.17·A − 42, with r = 0.955–0.986 on the overlapping character pixels. A's darks lift to about lum 63 at the 5th percentile, against about 40 in B, so A looks faded and washed out. B's underskirt, belt and folds hold as solid masses, and the image reads as finished rather than hazy.
- character_appeal: The design, face, poses and timing are identical. B's darker hair and eyes make the face slightly crisper, but that is not enough to change how appealing or alive she feels. Both have the same strengths: a Ghibli-like hooded girl with bare wrapped feet, big eyes, and a good crouch in land frames 1–2. Both have the same weaknesses: jittery cycles and a scarf that isn't continuous from frame to frame.
- color_readability: Measured on the contact sheets against the 128-gray background, using the colored pixels of the robe and body (the neutral scarf excluded): in A, 40.8% of body pixels fall within ±15 luminance of the background, with body median lum 115. In B the figures are 15.7% and median lum 93. A's robe dissolves into the gray, and its silhouette hangs on the dark underskirt and the hair. B's whole figure separates. The scarf is identical in both and weak in both: colorless (saturation ≤ 12), translucent, median lum about 171.

## gaps

### Set A

1. The silhouette's value sits on top of mid-gray. 41% of the robe's pixels are within ±15 luminance of a 128 background, and the robe's median lum is 115, so on any mid-value wall or platform the body vanishes and only the hair and underskirt read. Push the robe's base value to about lum 80–95, or add a consistent 1–2 px darker outline or a rim light on the side away from the key light, so the figure separates in a squint test at in-game size. Lana and GRIS both separate the figure from the background by value first.
2. The cycles aren't built as cycles. In run (8 frames, in place), the top of the head jumps around with no rhythm: 99, 104, 97, 100, 90, 100, 82, 94 px. There is no two-beat up/down bob, the feet sit on the y = 302–305 ground line in 7 of 8 frames with no airborne phase, and the body's center of mass slides 24 px sideways (x 103→127) within a loop that should have a fixed root. In idle, the head moves 16 px vertically (top at 78→94) and the scarf goes from hanging limp to a 60 px billow within an 8-frame breathing loop, so it reads as a wind gust. Fall frame 5 pops to a head-down tumble (the top of the frame jumps from about 80 to 41 px). Re-key run as contact/down/passing/up with the pelvis locked on x and a regular 4–6 px bob, and cut the idle scarf swing to under 10 px of drift.
3. The scarf, the character's signature element, is colorless, has no persistent shape, and is clipped by the frame. It is pale translucent gray (lum about 171, saturation ≤ 12), so it has no hue and will disappear against light walls. Its length, silhouette and opacity change every frame; in double_jump frames 3–4 it fades to a ghost blob. It is also cut flat at the left edge of the frame, where the bounding box hits x = 0, in run frames 1/2/5/6, jump frame 1 and land frames 1–2 (visible in contact land frames 5–6). Give it one saturated signature hue at full opacity, drive it as one continuous cloth simulation or hand-keyed follow-through across all animations, and widen the frame so the trailing end never clips.

### Set B

1. The cycles aren't built as cycles, the same defect as A because the drawings are identical. Run's head-top y goes 99, 104, 97, 100, 90, 100, 82, 94 px with no rhythm, the feet stay on the ground line in 7 of 8 frames with no airborne phase, and the body's center of mass drifts 24 px sideways inside an in-place loop. Idle's head moves 16 px and its scarf billows 60 px in 8 frames. Fall frame 5 pops to a head-down tumble with the top jumping about 40 px. Dash is 3 nearly identical frames with no anticipation or smear, and double_jump has no burst or other cue that tells it apart from jump. Re-key run with a locked root and a regular 4–6 px two-beat bob, give dash one anticipation frame and one stretch/smear frame, and add a distinct double-jump flourish.
2. The scarf is identical to A's: colorless translucent gray (lum about 171, saturation ≤ 12); its shape and opacity change every frame, and it nearly vanishes in double_jump frames 3–4; and it is clipped flat at x = 0 in run 1/2/5/6, jump 1 and land 1–2. B's darker robe makes the pale scarf stand out more by contrast, but it is still the least readable part of the character and carries no identity color. Give it one saturated hue at full opacity, one consistent cloth shape and length across all animations, and a wider frame.
3. The rendering is uniform grain rather than designed light and shape. The whole robe carries the same fine scribble texture at a single frequency, with no clear key-light direction, no lit plane versus shadow plane, and no rim light. The underskirt is a near-black ragged mass (5th-percentile lum about 40) whose edge is noisy fringe rather than a designed shape. GRIS and Lana read through big, simple shapes with 2–3 value steps and clean edges. Simplify the robe to a lit side and a shadow side (roughly lum 110 and 75), cut the texture noise by about half, and turn the underskirt hem into 3–4 deliberate scalloped shapes instead of pixel fringe.

## observations

- sets_share_drawings: A and B are the same frames under different tone curves. Bounding boxes match exactly in every GIF frame, and B's luminance maps from A's by a near-linear contrast stretch: bands at 64→55, 96→86, 128→120, 160→172.
- gif_format: All 14 GIFs are 290×316, loop forever, have disposal 0 and are painted over an opaque 128-gray background. I decoded them frame by frame with Pillow's ImageSequence. Frame counts: idle 8, run 8, jump 5, fall 5, double_jump 5, dash 3, land 3.
- scratch_outputs: Scripts and crops are in /tmp/lead-r5-critic-scratch/ (cr5_decode.py, cr5_bbox.py, cr5_crop*.py, *-strip.png, AB-*.png, face.png).

## references

### Set opened

1. https://planetoflana.com/: I read the page and viewed two official screenshots, pol-2-storm.jpg and pol-2-wemari-forest.jpg.
2. https://www.orithegame.com/screenshot_category/ori-and-the-blind-forest/: the page text loaded (a list of screenshots) but no images rendered, so I made no visual comparison.
3. https://www.hollowknight.com/: the page text loaded; I viewed no images.

### Set could_not_open

1. https://www.devolverdigital.com/games/gris: HTTP 429 on two attempts. The GRIS comparisons (flat watercolor shapes, a graphic silhouette) come from general knowledge of the game, not screenshots I viewed this session [INFERENCE].

## method

I viewed both contact sheets at full size, compared paired crops (idle, run, jump, fall, double_jump, dash, land and the face) side by side at 1.4–4× zoom, and viewed each GIF's frames as horizontal strips. The measurements (bounding boxes, head-top y, centroid drift, luminance and saturation distributions, silhouette-versus-background overlap, the A→B channel regression) come from Pillow/numpy scripts in a scratch uv venv. Environment color readability for the red and green walls wasn't testable because the sheets show only the character, so that axis covers the scarf and silhouette only.
