# spinerig

Builds a Spine 4.3 JSON skeleton from a `violet-rig` v1 description: a JSON document
listing bones, painted body-part images, and animations. Reimplements the delayed,
damped follow-through `spine-animation-ai` (PolyForm Noncommercial) produces for a
trailing scarf, from scratch (`scarf.py`), so no PolyForm-licensed code or technique is
used. Also plays a generated skeleton back to PNG frames and a GIF with Pillow
(`spinerig render`, `render.py`), so a rig proves it animates without the Spine editor or
the Spine runtime — Sami ruled on 2026-09-27 that the bake-off will not buy Spine, so
every lane reads this same Spine 4.3 JSON subset with its own small reader; see
`docs/bakeoff/character-rig.md` for that contract.

This is generic rig tooling: nothing here encodes a game mechanic. The only bake-off
-specific content is the set of animation names (`idle`, `run`, `jump`, ...) an author
puts in their own `rig.json` — that's data, not code (Task 5 Step 3 in
`docs/superpowers/plans/2026-09-27-phase-1-bake-off.md`, not part of this tool).

## Spine 4.3 JSON format

The output's shape (top-level keys, bone/slot/attachment fields, parent-before-child
ordering) follows the documented Spine JSON export format:
<https://esotericsoftware.com/spine-json-format> (accessed 2026-09-27). **That page is
3.8-era** — its own example says `"spine": "3.8.24"` — and it is wrong about one field
for Spine 4.x: a bone's `rotate` timeline keyframe holds `value`, not `angle`.

Verified instead against the actual 4.3 runtime: github.com/EsotericSoftware/
spine-runtimes, branch `4.3`, `spine-ts/spine-core/src/SkeletonJson.ts`, and that
branch's own example export, `examples/spineboy/export/spineboy-pro.json` (confirms it
in practice: `"rotate": [{"value": 9.111553}]`, never `"angle"`). Checked against the
runtime source, field by field:

- `skeleton.x/y/width/height/images` and bone `name/parent/x/y/rotation/length`: read by
  `readSkeletonData`, unchanged from the page.
- Slot `name/bone/attachment` and region attachment `path/x/y/rotation/width/height`:
  read by `readAttachment`, unchanged from the page.
- Bone `rotate` timeline: read by `readTimeline1`, which reads `keyMap.value` — **not**
  the page's `angle`. `translate` timelines keep `x`/`y`, unchanged from the page.
- Bezier `curve` keyframes: `readCurve` packs a 2-value timeline's (e.g. `translate`)
  curve as two 4-number arrays back to back (`value << 2` selects which), not the single
  4-number array the page describes generically. This module doesn't need bezier easing
  and doesn't translate this, so it refuses any authored `curve` rather than risk
  emitting the wrong shape.

Spine conventions used throughout: **y is up**, **angles are in degrees**, and `bones`
lists a bone's parent before the bone itself.

**This tool's output has not been imported into the Spine 4.3 editor**, and per Sami's
2026-09-27 ruling not to buy Spine, it may never be: nothing in this repo depends on
that import succeeding. The tests below validate structure against the documented (and
runtime-verified) format — required top-level keys, bone parent order, slot/attachment
references resolving, animation timeline shapes — and `spinerig render` plays a
generated skeleton back with real FK math and real part images, which is this tool's own
substitute for an editor round trip. The same JSON remains valid Spine 4.3 export data
and would still import cleanly if Spine were ever bought later.

## Usage

```bash
uv run --project tools/spinerig spinerig generate rig-src/rig.json \
  --out rig-src/violet.generated.json [--print-parts]
```

Writes `violet.generated.json` (the Spine JSON) and, next to it,
`violet.generated.meta.json` (`--out`'s stem + `.meta.json`) — `{"height_px", "feet_y_px":
0, "facing": "right"}`, the setup-pose height every engine reads to compute its scale
factor. `--print-parts` also prints each part's image file, width and height (in pixels),
so the rig's author can pick bone lengths before wiring up animations.

On any malformed input — a part naming an image file that doesn't exist, a bone or scarf
chain naming a bone that doesn't exist, a bone whose `parent` appears later in `bones`
than the bone itself, `draw_order` and the parts not naming exactly the same set of
slots, an authored animation timeline that isn't `rotate` or `translate`, or an authored
keyframe with a `curve` — `spinerig generate` exits 1 and names the offending bone,
slot, file, timeline, or animation. It writes neither output file when it fails.

## Playback: `spinerig render`

```bash
uv run --project tools/spinerig spinerig render rig-src/violet.generated.json \
  --parts parts --anim idle --out /tmp/violet-idle [--fps 30] [--scale 1.0]
```

Reads a generated Spine 4.3 subset skeleton (`SKELETON.json`, the shape `spinerig
generate` writes above) and plays one animation back with Pillow: forward kinematics
per bone at each sampled frame (setup pose plus that frame's `rotate`/`translate`
timeline value), each slot's region attachment placed at its bone's world transform and
drawn in slot (draw) order onto a transparent canvas sized from the skeleton's AABB.
Writes `OUT_DIR/frame_0000.png`, `frame_0001.png`, ... and `OUT_DIR/<anim>.gif` (looping,
`--fps` frames per second; frame count is the animation's duration times `--fps`).
`--parts DIR` is the directory holding each part's `<path>.png` (`path` is the
attachment's own field, i.e. the image's filename stem); `--scale` resizes every part and
position uniformly (e.g. to shrink the GIF).

Refuses, naming the offender, anything `spinerig generate` itself would never emit but a
hand-edited or otherwise-sourced skeleton might: a bezier `curve` keyframe, a bone
timeline type other than `rotate`/`translate`, a skin attachment whose `type` isn't
`region`, an unresolvable slot/bone/attachment reference, or a missing part image file
(names the file). See `docs/bakeoff/character-rig.md` for the full subset contract, the
FK and placement math, and the y-flip/scale conventions each engine lane's own reader
needs.

## `violet-rig` v1

```jsonc
{
  "parts_dir": "parts",                // resolved relative to this rig.json's directory
  "bones": [
    { "name": "root" },
    { "name": "torso", "parent": "root", "x": 0, "y": 0, "rotation": 90, "length": 160 }
    // ... parent before child, Spine conventions (y up, degrees)
  ],
  "parts": [
    {
      "slot": "torso", "bone": "torso", "image": "torso.png",
      "pivot": [0.5, 0.0],   // the image point (0-1, origin bottom-left) that sits on the bone origin
      "rotation": 0          // the image's up-axis angle relative to the bone, in degrees
    }
  ],
  "draw_order": ["torso", "head"],  // every part's slot, back to front; must be a permutation of the parts' slots
  "scarf": {
    "bones": ["scarf1", "scarf2", "scarf3"],   // the chain, root end first
    "trail_deg": { "idle": 5, "run": 35 },     // one entry per animation name below
    "flutter_deg": 8, "flutter_hz": 2.5, "lag_frames": 2,
    "gain": [1.0, 0.75, 0.5]                   // one entry per scarf bone; sets decreasing amplitude along the chain
  },
  "animations": {
    "idle": {
      "duration": 1.0,
      "loop": true,   // optional, default true: forces the last keyframe to match the first so a loop doesn't pop
      "bones": {
        "torso": { "rotate": [{ "time": 0, "angle": -2 }, { "time": 0.5, "angle": 2 }] }
        // this schema's "angle" becomes Spine 4.x's own "value" on output (see above);
        // "translate": [{ "time": t, "x": ..., "y": ... }] is read through unchanged;
        // a keyframe "curve" is refused, not translated -- author linear keys only
      }
    }
  }
}
```

The generator reads each part's image size with Pillow and computes its Spine attachment
offset as the image centre relative to the pivot, rotated into bone space:
`dx = (0.5 - px) * w, dy = (0.5 - py) * h; x = dx·cos(rot) - dy·sin(rot); y = dx·sin(rot) +
dy·cos(rot)`. The skeleton's `x, y, width, height` and `violet.meta.json`'s `height_px`
are the setup-pose axis-aligned bounding box over every attachment's four corners, after
walking the bone hierarchy's forward kinematics — exactly the AABB the Spine JSON format
doc defines for the `skeleton` section. `skeleton.images` is the relative path from
`--out`'s own directory to the resolved `parts_dir` (POSIX separators, trailing slash) —
computed per run, not a fixed string, so it's correct whatever directories the rig
actually uses.

Scarf bones must **not** appear in `animations.*.bones`: `spinerig generate` computes and
injects their `rotate` timelines itself (`scarf.py`), for bone *i* of the chain (0-indexed
from the root end):

```
angle_i(t) = -gain_i * trail_deg[anim] + gain_i * flutter_deg * sin(2π · flutter_hz · (t - i * lag_frames/30))
```

sampled every 2 frames at 30 fps and emitted directly as Spine's `value` field (this
timeline is generated, not translated from authored input). Decreasing `gain` along the
chain gives decreasing amplitude; the `i * lag_frames/30` term gives increasing phase
delay.

Each attachment also sets `path` to its image's filename stem, so a slot's name doesn't
have to match its image's filename for the Spine import to resolve the texture region.

## What Task 5 Step 3 needs to know

Authoring `assets/bakeoff/protagonist/rig-src/rig.json` from the 14 body parts
(`head, torso, hips, arm_back_upper/lower, arm_front_upper/lower, leg_back_upper/lower,
leg_front_upper/lower, scarf1, scarf2, scarf3`):

- Run `spinerig generate rig.json --out /tmp/throwaway.json --print-parts` first, on a
  skeleton draft, to read each part's actual pixel width/height and pick bone `length`s
  from them — that's the whole point of `--print-parts`.
- List every scarf bone in `scarf.bones` and give `scarf.gain` the same length, root end
  first; do **not** hand-key their `rotate` timelines in `animations.*.bones`.
- `scarf.trail_deg` needs one entry per animation name used in `animations`, or
  generation fails naming the missing animation.
- `parts_dir` and every part's `image` are resolved relative to `rig.json`'s own
  directory — point `parts_dir` at wherever Task 4's part PNGs actually land.
  `skeleton.images` is then computed from `--out`'s directory to that resolved
  `parts_dir`, so `--out` should be wherever the `.spine` import in Step 4 will read
  the generated JSON from.
- `draw_order` must be an exact permutation of the parts' slot names (missing or extra
  slots both fail loudly, naming the offending slot) — this is what fixes the skeleton's
  front-to-back layering.
- Don't author a keyframe `curve`: `spinerig generate` refuses it (see above). Linear
  keyframes only.
- The generator's `--out FILE.json` is the input to `Spine.sh -i ... -r NAME` (Step 4);
  it has not been run through the real Spine 4.3 importer yet, so treat any layout choice
  as provisional until that import succeeds.
