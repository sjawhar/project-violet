# Protagonist rig notes (THROWAWAY)

How `assets/bakeoff/protagonist/rig-src/rig.json` is laid out and why. Part sizes and the scale
derivation (which landmarks are measured on the turnaround and which are inferred) are in
`assets/bakeoff/protagonist/README.md`. Rig units are pixels at that shared scale: 1000 from crown to
sole. Spine conventions throughout: y up, angles in degrees, counter-clockwise positive, and the
character faces right. The turnaround's side view faces left, so every comparison mirrors it.

## Setup pose against the turnaround

- `protagonist-rig/setup-vs-turnaround.png`: the rig's setup pose beside the turnaround's side view
  (mirrored), scaled to the same height, with a line every 100 rig px.
- `protagonist-rig/setup-over-turnaround.png`: the setup pose over the turnaround at 45% opacity,
  aligned at crown and sole.

Crown, chin, shoulder line, sash, hand, hem and sole land within about 15 px of the turnaround's. The
visible differences: the scarf is one gray tail instead of two red ones; the feet are slightly apart,
so both show; and the torso's short peplum shows over the skirt at the back of the sash.

## Bones

The root sits at the feet. Bone `x`/`y` are in the parent's frame. `rotation` is local; "world" is
the setup-pose absolute angle (-90 is straight down).

| Bone | Parent | x, y | Rotation (world) | Length | Why |
|---|---|---|---|---|---|
| root | — | 0, 0 | 0 | 0 | feet on the floor |
| hips | root | 0, 540 | 0 (0) | 60 | hip joint, 460 below the crown (inferred) |
| skirt | hips | 0, 82 | -90 (-90) | 520 | hinges the skirt at the sash so it can trail, swing over raised knees, or fold in the tuck |
| torso | hips | 0, 82 | 90 (90) | 134 | waist (sash centre) to shoulder line |
| head | torso | 176, -6 | 0 (90) | 170 | neck, just above the shoulders |
| scarf1 | head | -8, 34 | 158 (-112) | 180 | back of the neck, hanging down-back like the turnaround's tail |
| scarf2 | scarf1 | 180, 0 | -6 (-118) | 180 | |
| scarf3 | scarf2 | 180, 0 | -6 (-124) | 200 | the three total 560, the turnaround tail's length |
| arm_back_upper | torso | 128, 4 | -182 (-92) | 153 | shoulder; 55% of shoulder-to-wrist (inferred elbow) |
| arm_back_lower | arm_back_upper | 153, 0 | 14 (-78) | 125 | elbow; forearm bent slightly forward |
| arm_front_upper | torso | 128, -4 | -178 (-88) | 153 | |
| arm_front_lower | arm_front_upper | 153, 0 | 12 (-76) | 125 | |
| leg_back_upper | hips | -6, 0 | -91 (-91) | 292 | 54% of hip-to-floor (inferred knee) |
| leg_back_lower | leg_back_upper | 292, 0 | 0 (-91) | 228 | knee |
| leg_front_upper | hips | 6, 0 | -89 (-89) | 292 | |
| leg_front_lower | leg_front_upper | 292, 0 | 0 (-89) | 228 | |

`skirt` is one bone beyond the plan's list. A rigid ankle-length skirt fixed to `hips` made every
leg pose look like legs poking out from behind a board, and the flip looked like a cone tumbling.

## Parts: pivots and rotations

A part's `pivot` is the point of its image (0–1, origin bottom-left) that sits on its bone's origin,
always the joint end. Its `rotation` is `-φ`, where φ is the direction, in the upright painting,
from the joint along the limb. Every part was painted upright facing right, so the rotation depends
on how the painting lies, not on the bone's world angle:

- 90 for parts that hang down from their joint: skirt, sleeves, thighs, shins, scarf segments.
- -90 for parts that rise from their joint: torso, head. This is character-rig.md's "limb along its
  bone needs -90" case.
- 48 (`arm_back_lower`) and 21 (`arm_front_lower`) for the forearms, which were painted reaching
  forward and down at those angles below horizontal.

| Slot | Bone | Pivot | Rotation |
|---|---|---|---|
| hips | skirt | 0.52, 0.966 (sash centre) | 90 |
| torso | torso | 0.5, 0.35 (sash centre) | -90 |
| head | head | 0.62, 0.12 (neck) | -90 |
| arm_back_upper / arm_front_upper | own bone | 0.4 / 0.45, 0.93 (shoulder cap) | 90 |
| arm_back_lower | arm_back_lower | 0.08, 0.85 (elbow end of the sleeve) | 48 |
| arm_front_lower | arm_front_lower | 0.03, 0.75 (elbow end of the sleeve) | 21 |
| leg_back_upper / leg_front_upper | own bone | 0.5, 0.95 / 0.97 (hip) | 90 |
| leg_back_lower | leg_back_lower | 0.18, 0.945 (knee; puts the sole on the floor) | 90 |
| leg_front_lower | leg_front_lower | 0.3, 0.845 (knee; the drape above hides under the robe) | 90 |
| scarf1 / scarf2 / scarf3 | own bone | 0.5, 0.97 / 0.95 / 0.96 (top edge) | 90 |

## Draw order (back to front)

`arm_back_lower, arm_back_upper, leg_back_lower, leg_back_upper, leg_front_lower, leg_front_upper,
hips, torso, scarf3, scarf2, scarf1, head, arm_front_lower, arm_front_upper`

- The back limbs go behind everything. Each upper sleeve draws over its own forearm, so the forearm
  and hand come out of the bell sleeve as in the turnaround.
- Both legs draw behind the skirt. The turnaround's robe covers them to the ankle, so drawing the
  front thigh over the skirt would break the silhouette. The front leg still draws over the back leg.
- The scarf draws over the torso's back but behind the head and the front arm, so the front arm
  swings over it.

## Scarf

`gain` is 1.0 / 0.75 / 0.5, `flutter_deg` 5, `flutter_hz` 2.0, `lag_frames` 2. Scarf angles add up
along the chain, so the tip moves 2.25× the trail. `trail_deg` per animation:

| Animation | idle | run | jump | fall | double_jump | dash | land |
|---|---|---|---|---|---|---|---|
| trail_deg | 3 | 22 | 10 | 45 | 35 | 30 | -6 |

Positive trail lifts the tail backward toward horizontal. At the plan's values (run 35, dash 70) the
tip swung past vertical and pointed forward. `fall` is positive so the tail streams upward in the
updraft. `land` is slightly negative so the tail keeps falling after the feet stop.

## Animations

Linear keys only. Every angle is a delta on the setup pose. For a limb pointing down, a positive
delta swings its far end forward; for the torso, a negative delta leans forward.

- `idle`: 1.0 s loop. The upper body sinks 4 px and leans 2° at 0.5 s while the head counters 3°,
  and the arms sway 2–3°. The skirt and feet stay planted.
- `run`: 0.6 s loop. Contacts at 0 and 0.3 s, thighs ±24°. The passing leg's knee folds to -80°.
  Arms swing ±28° opposite the legs with elbows bent about 45°. The hips bob down 12 px at mid-stance.
  The torso leans 10° forward, and the skirt trails 2–7° behind.
- `jump`: 0.5 s. A crouch at 0 (hips -60, knees bent, arms back), take-off extension at 0.12 s (arms
  up and forward), then the rising pose held from 0.3 s (front knee up, back shin folded, skirt over
  the knee).
- `fall`: 0.6 s, held. From the rising pose, the legs drop and spread and the arms go up and out.
  The head tips down.
- `double_jump`: 0.5 s. A tuck by 0.06 s (knees to chest, skirt folded forward over them, torso and
  head curled), a 360° forward flip about the hips by 0.35 s, then back out to the rising pose.
- `dash`: 0.2 s, held. The body leans hard forward (hips -12, torso -22, head up to keep the eyes
  level), the arms sweep back, the front leg reaches, the back leg trails, and the skirt and scarf
  stream back.
- `land`: 0.25 s. Impact squash at 0–0.07 s: hips down 62 px with knees bent to keep the feet
  planted, torso folded 28°, arms forward. Then the pose eases back to setup.

`idle` and `run` loop; the other five play once and hold their last frame, as character-rig.md
requires.

## Previews

`assets/bakeoff/protagonist/preview/<anim>.gif` is `spinerig render ... --scale 0.5`. The renders
use the canvas fix in PR #30: master's `spinerig render` cropped every pose outside the setup
bounding box, such as the run stride, raised arms and the flip. Lanes read `rig/violet.json`, which
`spinerig generate` writes and #30 does not touch.
