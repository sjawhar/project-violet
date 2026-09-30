# Round 4 critique (technique B across all seven animations, against round 3)

A fresh critic subagent, spawned as `astra` but run by omp on **anthropic/claude-opus-5-5** (from the transcript's model_change event; see rounds.md on the critic's model). Blind: neutral file names, letters from Python's `random`, and the verbatim prompt from rounds.md. **Letter map: A = round 3 (technique A, kept), B = round 4 (new).** Its reply, verbatim:

## Summary

Both sets show only the character, so color_readability here covers just the scarf and the silhouette. B wins clearly on visual_quality and character_appeal. The two tie on color_readability: A's scarf reads better and B's silhouettes read better, and both bodies are low-contrast mid-brown against the gray.

## Verdicts

- visual_quality: **B**
- character_appeal: **B**
- color_readability: **same**

## Scores (1-5, 5 = as good as GRIS or Planet of Lana)

| Set | visual_quality | character_appeal | color_readability |
|---|---|---|---|
| A | 2 | 2 | 2 |
| B | 3 | 4 | 2 |

## Rationale

**visual_quality:** A looks like a flat 3D toon render. The robe behaves like a rigid shell, the scarf is solid geometry with a sawtooth tip, and the palette is dull (warm body pixels have median luminance about 101 and saturation about 23 out of 255). B looks painterly and finished in any single frame: textured linen, a layered hem, wrapped ankles and a well-drawn face. It loses points because the drawings don't hold together from frame to frame.

**character_appeal:** A moves stiffly. The run is an upright shuffle, and jump, fall and double_jump all use the same pose with both arms raised. B feels alive: it has a real run cycle with a kick-back leg, a tucked double jump, a horizontal dash, and a lot of cloth motion. It also has the more appealing face. It stops short of 5 because its identity drifts from frame to frame and some frames are chaotic.

**color_readability:** A's scarf is opaque and bright (luminance about 185–207 on a 128 gray background) and reads as a crisp stripe even at quarter size. A's silhouettes are nearly the same across all the airborne states. B's silhouettes differ clearly by action at quarter size, but its scarf is a pale, semi-transparent haze (luminance about 163–180) that nearly disappears in some frames. Neither body stands out from the background: A's median luminance is about 101 and B's about 113, against 128. Planet of Lana's white shirt and black trousers do that instantly. The scarf has no color of its own in either set.

## Gaps

### Set A

1. The scarf is a rigid, opaque white slab ending in a jagged polygon sawtooth. It keeps the same folded shape in every idle frame and points straight back at almost the same angle in all 18 run frames. Replace it with simulated or hand-keyed cloth: a tapered, soft-edged end, a travelling wave through the run, and lag and overshoot on stops (idle, land).
2. The action poses are indistinct and stiff. The run keeps the torso vertical with feet barely clearing the ground; the feet stay at y 306–308 and body height varies only 208–221 px, so there is no bob or lean. Jump, fall and double_jump share one pose, arms up with pointed fingers, so double_jump looks like the fall pose drifting upward. Dash is a lunge-walk with arms swept back, lasting 180 ms, with no stretch or smear. Key a distinct pose for each state: a crouched jump takeoff, an arms-out fall, a tucked spin or burst for the double jump, and a forward-leaning stretch for the dash. Add anticipation and follow-through frames instead of uniform 30 ms interpolation.
3. The surface rendering is untextured CG. The robe doesn't flow; in the dash the wrapped leg sticks out through the front of the robe. The hands end in dark claw-like fingertips. The value range is narrow and the character has no rim light. Add a painted texture or paint-over pass to the materials, cloth simulation on the robe hem, clean hand shapes, and a rim or edge light so the brown body separates from mid-value backgrounds.

### Set B

1. The drawings are unstable from frame to frame. Each frame looks newly drawn: 10k–18k pixels change per frame, against about 1k in A's idle. Hair length changes, and the scarf vanishes in idle frame 1 and becomes a large wing in idle frame 5 while she stands still. Idle height jitters between 218 and 244 px. The feet anchor drifts: the bottom edge of the figure moves from 288 to 316 px within the jump. The sprite touches or clips the 316 px bottom edge in jump frame 3, fall frame 3 and double_jump frames 1 and 5, and the scarf touches the left edge (x = 0) in jump frame 1. Fix the character's proportions, hair and scarf on a model sheet, pin a fixed foot or pelvis anchor, and give the canvas margin.
2. The animation is too sparse to feel fluid. Dash and land have 3 frames each, and jump, fall and double_jump have 5, held 60–130 ms, with large pose jumps and no in-betweens. B's contact sheet repeats frames in pairs (for example dash and land) to fill six columns. The last fall frame is a tangled mass with the robe wrapped over the head and doesn't read as a pose. Add in-betweens so dash and land have at least 6 frames and the airborne loops 8–10, and replace the tangled fall frame with a clear fall pose.
3. The scarf and body don't separate from the background. The scarf is semi-transparent pale gray (median luminance about 163 on a 128 background); at quarter size it turns into a haze, and in double_jump frame 3 it is barely visible. The body is mid-value brown, close to the background gray. Make the scarf opaque, with its own value and ideally its own hue, keep its shape consistent, and add a darker line or rim light around the body so the figure stands out at gameplay size, the way Planet of Lana's white-on-black costume does.

## references

```json
{
  "opened": [
    "Planet of Lana: https://planetoflana.com/ page text, plus two in-game screenshots (pol-2-storm.jpg and pol-2-wemari-forest.jpg). Lana is a small, simple-shaped figure with a high-contrast white top and black trousers.",
    "GRIS: the Devolver page (https://www.devolverdigital.com/games/gris) only loaded in a headless browser. It has just the hero key art (a close-up face illustration) and a poster, with no gameplay screenshots. What I say about GRIS gameplay characters comes from prior knowledge, not from an image I looked at.",
    "Ori and the Blind Forest: one screenshot from the official screenshot page (screenshot_blind_forest_13, a landscape with no character). Used only to name gaps, not to score."
  ],
  "could_not_open": [
    "GRIS page through the read tool and through curl: HTTP 429, three attempts. The CMS image URL also returned 429.",
    "Hollow Knight (https://www.hollowknight.com/): not tried. It is optional and wasn't needed to name the gaps."
  ]
}
```

## method

I looked at both contact sheets. I decoded every GIF frame by frame with Pillow; all frames use disposal 0 with a full opaque gray background, so no compositing was needed. For each frame I measured its bounding box, how many pixels changed from the previous frame, and scarf and body luminance. I made enlarged crops of single frames and faces, and a quarter-scale readability strip showing the middle frame of each animation. A has 6–30 frames per animation at a uniform 30 ms; B has 3–8 frames at 60–130 ms. Scratch files are in /tmp/lead-r4-critic-scratch/.
