# Round 8 critique (technique B idle hybrid, against round 7)

A fresh critic subagent, spawned as `astra` but run by omp on **anthropic/claude-opus-5-5** (from the transcript's model_change event). Blind: neutral file names, letters from Python's `random`, and the verbatim prompt from rounds.md. **Letter map: A = round 8 (new), B = round 7 (kept).** Its reply, verbatim:

```json
{
  "verdict": {
    "visual_quality": "A",
    "character_appeal": "same",
    "color_readability": "A"
  },
  "scores": {
    "A": {
      "visual_quality": 3,
      "character_appeal": 3,
      "color_readability": 3
    },
    "B": {
      "visual_quality": 2,
      "character_appeal": 3,
      "color_readability": 3
    }
  },
  "key_finding": "The two sets differ only in the idle animation. The other six GIFs (run, jump, fall, double_jump, dash, land) have identical md5 hashes in A and B, and rows 1 to 6 of the two contact sheets match pixel for pixel (0 pixels differ by more than 30). Only the idle row differs (53,909 pixels). That makes the axis verdicts a judgment of the idle alone. The scores cover the whole set, so they are close.",
  "idle_comparison": {
    "A": "Almost a still image. Across the 8 frames (130/130/130/90 ms, repeated), the top of the head moves only between y 68 and 70. The body's centre stays within x 133.9 to 134.2 and the feet stay fixed at x 120 to 158. Only the hem of the scarf sways. The character stays on-model and registered, but nothing reads as breathing, weight shift or a glance. Frame-to-frame change is 590 to 1,280 pixels.",
    "B": "Each frame is a separate redraw. In frame 1 the lowest pixel sits at y 291 instead of 305, so the figure shrinks and lifts about 14 px. The body's centre drifts from x 134.3 to 128.7 over frames 1 to 6. The head tilts up to the sky in frame 4 and snaps back within about 0.5 s. One foot disappears in frame 3. The knot and outline of the scarf change every frame. Frame-to-frame change is 8,500 to 12,400 pixels, about ten times A's. The look up at the sky is the most characterful beat in either set. At this timing it will probably read as a pop or twitch rather than acting [INFERENCE: judged from the decoded frames and their durations, not from watching it play in-engine].",
    "scarf_value": "The scarf behind the back has a mean luminance of 176 to 178 in every A idle frame; the background is 128. In B it falls to 166, 162, 155, 152 and 151 over frames 2 to 6, which roughly halves its contrast against the background, then jumps back to 172 in frame 7. That brightness flicker is why A wins color_readability."
  },
  "gaps": {
    "A": [
      "The scarf and robe change from frame to frame instead of moving as one piece of cloth. In run, jump, dash and land, the scarf's length, outline and attachment point are redrawn on every frame. In some frames it is painted as a flat, untextured light-gray shape with hard edges (run frame 6; dash frames 3 and 6) while the robe beside it is textured. In land frames 4 to 6 it swaps from in front of the body to behind it. The robe's hem folds are redrawn each frame too, so the fabric shimmers. Fix: drive the scarf with one cloth rig or simulation, or trace one scarf through all frames, and give it one consistent texture and shading.",
      "The idle is effectively a still. The body moves 2 px at most over its 8 frames (about 0.9 s), and only the scarf hem sways. Fix: lengthen the loop to 2 to 3 s. Add a 2 to 4 px rise and fall in the chest and shoulders, a slight sway of the hood and hair, and a blink or glance. Keep the feet fixed in place.",
      "The colors carry no identity. The scarf is neutral gray (mean RGB 184, 183, 183, about 55 levels above the gray background), and the robe is a dark, low-saturation brown (mean RGB 88, 75, 67). There is no hue accent. In a world of red and green walls, the brown robe will likely merge into dark red surfaces [INFERENCE: this sheet shows no walls]. In Planet of Lana, by contrast, Lana's light top over dark trousers makes a crisp two-value silhouette against the saturated forest. Fix: give the scarf a saturated hue outside the red and green used for the mechanic, and add a lighter rim or edge value to the robe so the outline survives against dark backgrounds."
    ],
    "B": [
      "The idle is not registered or kept on-model. The figure changes size (frame 1's lowest pixel is 14 px higher), the body drifts 5.6 px sideways, a foot vanishes in frame 3, and the head turns up and back within about 0.5 s. Fix: pin the feet, the ground line and the scale to one base frame, and build the idle from deformations of that frame. If the look up at the sky stays, give it an ease-in, a hold of at least 600 ms and an ease-out, on a loop of 2 s or more.",
      "The scarf's brightness flickers during the idle. Its luminance drops from 178 to 151 over frames 4 to 6 against the 128 background, then jumps back to 172. Fix: lock the scarf to one palette or value range in every frame.",
      "B has the same scarf and robe discontinuity as A in run, jump, dash and land, because those six animations are identical: the scarf is redrawn each frame, some frames are flat hard-edged fills (run frame 6; dash frames 3 and 6), it swaps sides in land frames 4 to 6, and the hem folds shimmer. The fix is the same as for A."
    ]
  },
  "additional_findings_both_sets": [
    "Sprites are cut off by the 290×316 cell. The following frames touch the left edge (x=0): run frames 1, 2 and 5; jump frame 1; dash frames 2, 4 and 5; land frames 1 and 2. These touch the bottom edge (y=315): run frame 7; jump frame 3; fall frames 3 and 5; double_jump frames 1 and 5. The scarf tips come out with straight vertical cuts (clearly visible on the left edge of dash frame 4). Fix: render on a larger canvas with at least 16 px of padding.",
    "All animations are short pose-to-pose sequences with no in-between frames: dash is 6 frames at 30 ms each (0.18 s), and jump, fall and double_jump are 5 frames each. The motion depends on the poses snapping from one to the next rather than on arcs."
  ],
  "method": "Pillow and numpy, run through `uv run --no-project --with pillow --with numpy`. GIFs were decoded frame by frame with ImageSequence and convert(), which composites each frame correctly for its disposal method; every frame in both sets uses disposal 0 and is an opaque 290×316 frame on RGB (128, 128, 128). Measured: md5 hashes of each GIF, pixel diffs between A and B per frame and per contact-sheet row, bounding boxes, the centre of the dark robe pixels, the head top, the width of the feet, and the scarf's luminance. Zoomed strips, magnified crops and the scripts are in /tmp/lead-r8-critic-scratch/.",
  "scoring_note": "Scores are whole numbers from 1 to 5, where 5 means as good as GRIS or Planet of Lana. For character_appeal and color_readability, both sets score the same because the gap between them is smaller than one point; the verdict above still names a winner where there is one. Individual frames are competently painted, with a textured robe and an appealing design: a hooded child with large eyes, wrapped bare feet and a flowing scarf. The scores are held down by cloth that doesn't hold together from frame to frame, the idle, and the neutral palette. Nothing shown reaches the finish of Planet of Lana.",
  "references": {
    "opened": [
      "https://planetoflana.com/: the page loaded, and I viewed two official screenshots: pol-2-storm.jpg and pol-2-wemari-forest.jpg.",
      "https://www.orithegame.com/screenshot_category/ori-and-the-blind-forest/: text only. The page listed screenshots 05 to 14 but exposed no image URLs, so I saw no Ori images.",
      "https://www.hollowknight.com/: text only. The image URLs were listed, but I didn't view any images."
    ],
    "not_opened": [
      "https://www.devolverdigital.com/games/gris: HTTP 429 twice through the reader tool and once through curl with a browser user agent. I compared nothing against GRIS directly."
    ]
  }
}
```
