# Character rig: the Spine 4.3 JSON subset every lane reads (THROWAWAY)

Part of the Phase 1 bake-off shared inputs; see [README.md](README.md). This is the
contract every lane's own reader implements to animate the protagonist rig
(`assets/bakeoff/protagonist/spine/violet.json` and its part images) — the character's
final design, rig, and rendering approach are undecided
([decision 0009](../decisions/0009-mechanics-undecided.md)); nothing here is canon.

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

- `skeleton`: `x`, `y`, `width`, `height` (the setup-pose AABB, in the rig's own units —
  see Scale below), `images` (the path from the JSON's own directory to the part-images
  directory, POSIX separators, trailing slash).
- `bones`: a list, each `{name, parent?, x?, y?, rotation?, length?}` (all four numeric
  fields default to `0` when absent). **A bone's entry always precedes its children's.**
  `x`/`y` are the bone's local translation from its parent's origin (root bones: from the
  skeleton origin); `rotation` is local, in degrees; Spine convention: **y is up**,
  rotation is counter-clockwise as viewed, and all of this is the bone's *setup* pose.
- `slots`: a list, each `{name, bone, attachment}`, **in draw order** (index 0 drawn
  first, i.e. furthest back; the list order *is* the layering — there is no separate
  z-index).
- `skins`: exactly one skin, `{"name": "default", "attachments": {slot: {attachment:
  {...}}}}`. Every attachment is a **region attachment** (Spine's default when `type` is
  absent): `path` (the image file's name, without directory or extension — see Images
  below), `x`, `y` (the image's centre, in the bone's local frame, already rotated by the
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
  keyframe time across all of its bones' timelines. **Loop**: every animation in this
  subset loops; play frame `t = 0` immediately after frame `t = duration` without
  repeating it (a looping animation's last keyframe already matches its first).

Refuse and name the offender for anything outside this subset: a `curve` keyframe, a
timeline type other than `rotate`/`translate`, an attachment `type` other than region (or
absent), an unresolvable slot/bone/attachment reference. `tools/spinerig/src/spinerig/
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

`assets/bakeoff/protagonist/spine/violet.meta.json` is `{"height_px", "feet_y_px": 0,
"facing": "right"}` — `height_px` is the setup-pose skeleton height, in the rig's own
(pixel-ish, Pillow-native) units. Every lane scales the rig so its height is **1.6
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
packing). A lane's reader loads each part image directly by that resolved path; nothing
here assumes a texture atlas or a `.atlas` file.

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
