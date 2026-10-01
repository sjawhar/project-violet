# Character rig: the Spine 4.3 JSON subset every lane reads (THROWAWAY)

Part of the Phase 1 bake-off shared inputs; see [README.md](README.md). This is the
contract every lane's own reader implements to animate the protagonist rig
(`assets/bakeoff/protagonist/rig/violet.json`, `violet.meta.json` beside it, and the part images) — the character's
final design, rig, and rendering approach are undecided
([decision 0009](../decisions/0009-mechanics-undecided.md)); nothing here is canon.

The painted, frame-by-frame character has its own format,
[violet-sprites v1](#painted-sprite-sequences-violet-sprites-v1), at the end of this doc.

## Why no Spine editor, no Spine runtime

Sami ruled on 2026-09-27 that the bake-off will not buy Spine: "You haven't actually
proven that you can develop anything yet, why should I purchase some professional tool."
So the rig is built and consumed as data, not as a licensed pipeline: `tools/spinerig`
(`spinerig generate`) writes a Spine 4.3 *JSON* skeleton by hand, matching the shape the
real Spine editor's own JSON export uses (verified against the runtime source, not just
the 3.8-era format page — see `tools/spinerig/README.md`), and each lane reads that exact
subset with its own small reader. No lane depends on the Spine editor, the Spine
runtime, or any Spine license. `spinerig render` (this doc's other half) proves a rig
plays back correctly, in Pillow, before any engine touches it.

If Spine is ever bought later, nothing here has to change: the same JSON is valid Spine
4.3 export data and imports into the Spine editor unmodified — buying Spine only adds a
GUI and a runtime on top of a format lanes can already read.

## The subset

A skeleton file has exactly these top-level keys and fields; a lane's reader does not
need to handle anything else (curves, meshes, IK, physics, other timeline types, other
attachment types), and `spinerig render` refuses to emit or play back a file that uses
one:

- `skeleton`: `spine` (the format version: always `4.3.` something; refuse anything else), `x`, `y`, `width`, `height` (the setup-pose AABB, in the rig's own units —
  see Scale below), `images` (the path from the JSON's own directory to the part-images
  directory, POSIX separators, trailing slash).
- `bones`: a list, each `{name, parent?, x?, y?, rotation?, length?}` (all four numeric
  fields default to `0` when absent). **A bone's entry always precedes its children's.**
  `x`/`y` are the bone's local translation from its parent's origin (root bones: from the
  skeleton origin); `rotation` is local, in degrees; Spine convention: **y is up**,
  rotation is counter-clockwise as viewed, and all of this is the bone's *setup* pose.
- `slots`: a list, each `{name, bone, attachment}` (every slot names an attachment; refuse one that doesn't), **in draw order** (index 0 drawn
  first, i.e. furthest back; the list order *is* the layering — there is no separate
  z-index).
- `skins`: exactly one skin, `{"name": "default", "attachments": {slot: {attachment:
  {...}}}}`. Every attachment is a **region attachment** (Spine's default when `type` is
  absent): `path` (required: the image file's name, without directory or extension — see Images
  below; refuse an attachment without one rather than fall back to a name), `x`, `y` (the image's centre, in the bone's local frame, already rotated by the
  attachment's own `rotation` — see the placement math), `rotation` (the image's own
  extra rotation on top of the bone, degrees), `width`, `height` (the source image's pixel
  size). No other attachment `type` (mesh, path, clipping, boundingbox, point) appears.
- `animations`: `{name: {"bones": {bone: {"rotate"?: [...], "translate"?: [...]}}}}`. A
  bone only appears here if something animates it. The only two timeline types are:
  - `rotate`: keyframes `{"time": t, "value": deg}` — `value` is a **delta added to the
    bone's setup `rotation`**, not an absolute angle (Spine 4.x's real field name; the
    3.8-era format page calls it `angle` — see `tools/spinerig/README.md`).
  - `translate`: keyframes `{"time": t, "x"?": dx, "y"?: dy}` (each defaults to `0` when
    absent) — deltas added to the bone's setup `x`/`y`.

  Every keyframe list is **linear** and **ascending by time**; there is no `curve` field
  anywhere in this subset (Bezier easing is a real 4.x behavior difference from the
  documented 3.8 format that this subset does not reproduce — refuse a `curve` rather
  than guess its shape). An animation has no separate stored duration: it is the latest
  keyframe time across all of its bones' timelines. **Looping** is not stored in the
  JSON; the lane decides it by animation name. `idle` and `run` loop: play `t = 0`
  immediately after `t = duration` without repeating it (their last keyframe already
  matches their first). `jump`, `fall`, `double_jump`, `dash` and `land` play once and
  hold their last frame; the lane's own state machine chooses what plays next (for
  example `land`, then `idle`).

Refuse and name the offender for anything outside this subset: a `curve` keyframe, a
timeline type other than `rotate`/`translate`, an attachment `type` other than region (or
absent), an unresolvable slot/bone/attachment reference, a slot with no attachment, an attachment without a
`path`, a `skeleton.spine` that isn't 4.3.x. `tools/spinerig/src/spinerig/
render.py` is the reference implementation of all of the above, including these refusals.

## Forward kinematics and placement

For a bone at animation time `t`: local `x`/`y`/`rotation` = its setup values plus its
`translate`/`rotate` timeline's value at `t` (linearly interpolated between the
keyframes surrounding `t`, clamped to the first/last keyframe's value outside their time
range). Its world transform is its parent's world transform applied to that local one —
**child = parent × (translate then rotate)**:

```
world.x        = parent.world.x + local.x·cos(parent.world.rotation) − local.y·sin(parent.world.rotation)
world.y        = parent.world.y + local.x·sin(parent.world.rotation) + local.y·cos(parent.world.rotation)
world.rotation = parent.world.rotation + local.rotation
```

A root bone (no `parent`) has world transform equal to its own local transform.

An attachment's world centre is its bone's world transform applied to the attachment's
own `(x, y)` (which is *already* rotated into bone-local space by the attachment's own
`rotation` — this subset's generator computes it that way, so a reader does not re-apply
attachment rotation to `x`/`y` a second time):

```
centre.x  = bone.world.x + x·cos(bone.world.rotation) − y·sin(bone.world.rotation)
centre.y  = bone.world.y + x·sin(bone.world.rotation) + y·cos(bone.world.rotation)
image_rotation = bone.world.rotation + attachment.rotation
```

Draw the image (its own pixel `width`×`height`, scaled per below) centred at `centre`,
rotated by `image_rotation` (counter-clockwise, the same physical sense as the Spine
rotations above — this is a statement about how the rotation *looks*, not about which way
a coordinate's y increases, so it needs no sign flip per engine), in `slots` order.

**y-flip.** Skeleton space is y-up throughout the math above. Convert to each engine's
own space when placing the result, not by changing the FK or rotation math itself:

- **Godot 2D (y down):** flip skeleton y before use — a bone/attachment world `y` in
  skeleton space becomes `-y` in Godot 2D local space (then offset by wherever the
  rig's root node sits). `spinerig render`'s own canvas placement does the same flip to
  turn y-up skeleton space into a y-down raster (`world_to_canvas` in `render.py`).
- **Godot 3D and Unity (y up):** no flip — skeleton y already points the way these
  engines' y does. Treat skeleton x/y as a plane (commonly x/y → world x/y with z=0, or
  x/z if the character faces along a different axis than the plan's greybox convention
  assumes; either way, no sign change on y).

## Scale

The meta file sits beside the skeleton and is named `<stem>.meta.json`, which is what
`spinerig generate` writes: `violet.json` pairs with `violet.meta.json`. It is
`{"height_px", "feet_y_px", "facing"}`:

- `height_px` is the setup-pose skeleton height, in the rig's own (pixel-ish,
  Pillow-native) units.
- `feet_y_px` is the skeleton-space y where the feet touch the ground. It is 0 for this
  rig, whose root is at the feet. A reader subtracts it so the feet sit on the character
  body's floor.
- `facing` is always `"right"`; refuse anything else. A lane shows the character facing
  left by mirroring it (negative x scale on the rig's root node), not with a second rig. Every lane scales the rig so its height is **1.6
tiles** (the plan's protagonist scale target), where a tile is the project's own unit
(`docs/superpowers/plans/2026-09-27-phase-1-bake-off.md`'s Global Constraints: 1 tile =
64 px in Godot 2D, 1 m in Godot 3D and Unity):

```
scale = (1.6 · tile_unit) / height_px
```

Apply `scale` uniformly to every bone's translation and every attachment's position and
size — the same single factor throughout, not a per-part fudge.

## Images

One PNG per body part, no shared atlas: `skeleton.images` (resolved against the JSON
file's own directory) names the directory, and an attachment's `path` names the file
inside it (`path.png`, no other extension — this subset never uses Spine's atlas/region
packing). Nothing here assumes a texture atlas or a `.atlas` file.

In Godot, copy the skeleton, meta file and part PNGs into the lane's project, and load
each part as an imported texture (`load("res://.../<path>.png")`). An exported build
packs imported resources, not raw PNG files, so reading PNGs from disk at runtime would
work in the editor and fail in the export.

## What this doc does not cover

`draw_order`/bones/parts authoring is `assets/bakeoff/protagonist/rig-src/rig.json`'s
job (Task 5), not this contract. Two things are deliberately left to each lane, not
baked into the rig JSON, because they are mechanic/rendering choices, not rig data:

- **The scarf chain's color.** The rig has `scarf1`/`scarf2`/`scarf3` slots and bones
  like any other part, animated the same FK way — but their *tint* (gray when no color
  is active, the active color otherwise) is the lane's own rendering, driven by the
  bake-off's active-color state (`docs/bakeoff/mechanic.md`), not a color baked into the
  scarf's PNGs or the skeleton JSON.
- **Anything else mechanic-specific.** This rig is generic playback data; a lane wires
  it to its own gameplay state.

## Reference implementation

`uv run --project tools/spinerig spinerig render SKELETON.json --parts DIR --anim NAME
--out DIR [--fps 30] [--scale S]` (`tools/spinerig/src/spinerig/render.py`) plays this
exact subset back with Pillow — the FK and placement math above, the y-flip for its own
(y-down) raster output, the same refusals — to `OUT_DIR/frame_%04d.png` and
`OUT_DIR/<anim>.gif`. It is not a lane reader (no lane renders with Pillow), but it is the
proof, before any engine-side reader exists, that a `spinerig generate` skeleton actually
animates.

## Painted sprite sequences (violet-sprites v1)

The painted, frame-by-frame Violet (`assets/bakeoff/protagonist/glow-up/`, merged in
PR #36) has no skeleton. Each animation is a short sequence of painted frames, and each
frame has two layers: a body and a separate scarf. The rig above stays valid; this is a
second, independent format a lane can read instead.

`assets/bakeoff/protagonist/sprites/violet.sprites.json` is generated by `spinerig
sprites` from `assets/bakeoff/protagonist/sprites-src/sprites.json` (see
`tools/spinerig/README.md`). Its shape:

```
{"format": "violet-sprites", "version": 1, "facing": "right",
 "height_px": <float>, "units": "px",
 "animations": {"<name>": {"duration": <s>, "loop": <bool>, "frames": [
    {"body":  {"image": "<path relative to this JSON>", "anchor": [ax, ay]},
     "scarf": {"image": "...", "anchor": [ax, ay]}} ... ]}}}
```

Refuse a file whose `format` is not `violet-sprites`, whose `version` is not `1`, whose
`facing` is not `right` or whose `units` are not `px`. Mirror the character for facing
left, as with the rig.

- **Animations.** `idle` (8 frames, 1.0 s), `run` (8, 0.6 s), `jump` (5, 0.5 s), `fall`
  (5, 0.6 s), `double_jump` (5, 0.5 s), `dash` (6, 0.2 s), `land` (6, 0.25 s). The
  durations are the rig's, so both formats play in step. `idle` and `run` have `loop:
  true`. The other five play once and hold their last frame; the lane's state machine
  picks what plays next, as with the rig.
- **Units.** Everything is in the frame PNGs' own pixels. Every frame was painted to
  one shared scale (`RIG_PER_RAW`, `glow-up/technique-trial.md`), so no frame needs its
  own factor.
- **Images.** `image` is resolved against the JSON file's own directory. In Godot,
  import each PNG as a texture, as with the rig's parts.

### Root and anchor

The **root** is the player's position: the ground contact point under the character's
horizontal anchor. An **anchor** is the pixel of its image, measured from the image's
top-left corner with y down, that sits exactly on the root. Anchors are floats, and they
can lie outside the image: an airborne frame's anchor is below its feet.

To draw a layer, put the image's anchor pixel on the root, scaled uniformly by `scale`:
the image's top-left corner goes to `root - anchor * scale`. In Godot 2D that is a
`Sprite2D` with `centered = false` and `offset = -anchor`, child of a node at the root
with `scale = Vector2(scale, scale)`. In a y-up engine, flip the y offset: the image's
top edge is `anchor.y * scale` above the root.

The generator folds every placement scheme `glow-up/shoot_b.py`'s `render_cell_b`
uses into these anchors, so a reader needs no per-animation cases:

- grounded (`idle`, `run`, `land`): the record's sole (plus `place_dy_offset`) sits on
  the ground line, and its `torso_x`, or `head_x` where there is no `torso_x`, sits on
  the horizontal anchor;
- airborne in rig units (`jump`, `fall`, `double_jump`): the head sits on the
  record's `target_head_x/y` in shoot_b's review cell;
- airborne by cell fraction (`dash`): the head sits on `target_head_x/y_fraction` of
  that cell.

The review cell is shoot_b's contact-sheet cell, 290 × 316 px at scale 0.22, with the
root at (`HEAD_X_FRACTION` · 290, `GROUND_Y_FRACTION` · 316) = (135, 306). At that cell
and scale, every frame's two layers land on shoot_b's own integer paste positions
(`tools/spinerig/tests/test_sprites.py` checks all 43 frames).
At any other scale the anchors scale exactly. shoot_b does not: it places its airborne
frames against its own rounded cell size, so at the in-game scale its `jump`, `fall`,
`double_jump` and `dash` cells sit up to 0.25 px from the anchors' placement (1.3 px at
scale 1.0). The anchors are the contract; that drift is shoot_b's rounding.

The scarf binds to the body through the frame's `scarf_offset_final`, which
`glow-up/apply_scarf_attachments.py` derives from the hash-bound neck and knot landmarks
in `glow-up/scarf_attachments.json`: scarf anchor = body anchor − `scarf_offset_final`.
Draw both layers on the same root and the knot lands on the neck.

### Timing

Frames are evenly spaced across the duration and held, never interpolated. The frame
showing at time `t` (seconds since the animation started) is

```
index = min(floor(t * n / duration), n - 1)
```

where `n` is the number of frames, and `t` is first wrapped to `t mod duration` for a
looping animation. Exactly on a boundary this shows the frame that starts there. shoot_b
computes `int(t / (duration / n))`, which agrees everywhere else but can fall one frame
short on a boundary by float rounding (jump at t = 0.3 s: shoot_b shows frame 2, the
formula frame 3). Follow the formula.

### Draw order and scarf tint

Draw the body first, then the scarf over it, so the scarf's painted neck wrap stays
visible over the clothing.

Every scarf layer is neutral gray: its mean |R−G| + |G−B| over non-transparent pixels is
at most 4 (today's largest is 2.1). A lane multiplies the scarf by the active tag color
(`docs/bakeoff/mechanic.md`), or leaves it gray when no color is active. The body is
never tinted.

### Scale

`height_px` is idle frame 0's standing height, from the sole to the top non-transparent
pixel of the body layer. Lanes keep the rig's scale rule:

```
scale = (1.6 · tile_unit) / height_px
```

and apply it to every image and anchor, the same single factor throughout.

### Refusals

`spinerig sprites` refuses, naming the file or frame:

- a stale scarf binding: a body or scarf PNG whose sha256 differs from
  `scarf_attachments.json`, a landmark that is outside its image or on transparent
  pixels, a frame with no binding or two, or a record whose `scarf_offset_final` misses
  the bound neck by more than 1 px (`apply_scarf_attachments.py check`'s rules);
- a colored scarf layer (above the gray limit);
- a missing frame PNG, or a live frame PNG with no record entry;
- an animation the rig does not have, so it has no duration;
- a record frame missing the fields its placement scheme needs.

`render_frame` and `spinerig sprites-render` refuse an animation the file does not
have.

### Worked example

From the real file: idle frame 0's body is `../glow-up/trial-b/frames/idle-body-00.png`,
379 × 1095 px, anchor (204.678, 1094.0): the root is the sole line, 204.7 px from the
image's left edge. `height_px` is 1072.0 (sole 1094, top non-transparent row 22). Its
scarf, `idle-scarf-00.png`, has `scarf_offset_final` (107.543, 191.562), so its anchor is
(204.678 − 107.543, 1094.0 − 191.562) = (97.135, 902.438).

In Godot 2D, 1 tile = 64 px, so scale = 1.6 · 64 / 1072 = 0.09552. With the player at
(400, 300) the body's top-left corner is (400 − 204.678 · 0.09552, 300 − 1094.0 ·
0.09552) = (380.45, 195.50) and the scarf's is (390.72, 213.80). At t = 0.35 s idle shows
frame min(floor(0.35 · 8 / 1.0), 7) = 2; at t = 1.35 s it wraps to the same frame. Jump
at t = 0.8 s holds frame 4. Jump frame 0's body anchor is (651.066, 921.412) in an
839 px tall image, so the root is 82 source px below the image's bottom row: that frame
is drawn clear of the ground, where shoot_b drew it.

### Reference implementation

`tools/spinerig/src/spinerig/sprites.py`: `build_sprites` (with the refusals above),
`frame_index_at` and `render_frame`, which composites one frame from the file alone at
any scale and root. `uv run --project tools/spinerig spinerig sprites-render
assets/bakeoff/protagonist/sprites/violet.sprites.json --out sheet.png --scale 0.22
--cell 290x316 --root 135,306` renders all seven animations in shoot_b's contact-sheet
layout; check a lane's reader against it.
