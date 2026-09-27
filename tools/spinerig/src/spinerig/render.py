"""Plays a Spine 4.3 JSON subset skeleton -- the shape `spinerig generate` writes, see
`generate.py`'s module docstring -- to a directory of PNG frames and a looping GIF,
without the Spine editor or the Spine runtime. This is the proof that a `spinerig`
skeleton actually animates before any engine lane builds its own reader for the same
subset (docs/bakeoff/character-rig.md is that reader's contract).

Forward kinematics, Spine conventions throughout (y up, degrees, a bone's `bones` list
entry precedes its children): a bone's animated local transform is its setup pose
(`x`, `y`, `rotation`) plus whatever its `rotate`/`translate` timeline contributes at the
sampled time (a rotate keyframe's `value` and a translate keyframe's `x`/`y` are deltas
added to the setup pose -- not absolute values; see generate.py's module docstring for
why `value`, not the 3.8-era `angle`, is the real 4.x field name). A bone's world
transform is its parent's world transform applied to that local transform: parent
rotation rotates the local translation, then the local rotation adds to the parent's
world rotation (child = parent * translate-then-rotate). A root bone (no `parent`) is
its own local transform.

A slot's attachment (`skins[0]["attachments"][slot][attachment]`, a region attachment:
`path`, `x`, `y`, `rotation`, `width`, `height` -- see generate.py) places its image
centred at `(x, y)` in its bone's local frame (already rotated by the attachment's own
`rotation`, per `generate.py`'s `_attachment_offset`), so the image's total world
rotation is bone rotation plus attachment rotation, and its world centre is the bone's
world transform applied to `(x, y)`. Slots are drawn in `slots` list order (back to
front, the same order `spinerig generate` writes from `draw_order`) onto a transparent
canvas sized from the skeleton's setup-pose AABB (`skeleton.x/y/width/height`) plus a
fixed margin, at `--scale`. Skeleton space is y-up; the canvas is y-down (row 0 at the
top), so placement flips y (`world_to_canvas`) -- image *rotation* does not need a sign
flip: Pillow's `Image.rotate(angle)` is defined by the angle's counter-clockwise sense as
displayed, the same physical sense as a positive Spine rotation, independent of which way
a coordinate's numeric y increases. A lane whose engine is y-down in 2D (Godot) or y-up
in 3D (Godot 3D, Unity) has the same choice to make; docs/bakeoff/character-rig.md notes
it for both.

An animation's duration is the latest keyframe time across its bones' timelines (Spine
itself has no separate stored duration field; see generate.py -- the generated JSON's
`animations.<name>` holds only `bones`). Frames are sampled at `t = i / fps` for
`i in range(round(duration * fps))`, so `--fps` frames are emitted per second and the
loop does not repeat the frame at `t == duration` (an authored or scarf-generated
animation's last keyframe already matches its first when it loops).

Refuses, naming the offending bone/slot/attachment/timeline/keyframe: a bone or
translate/rotate keyframe with a bezier `curve` (this subset is linear-only, like
`generate.py`); a bone timeline type other than `rotate`/`translate`; a skin attachment
whose `type` isn't `region` (the only attachment shape this subset emits); a slot naming
an attachment the default skin does not define; a missing part image file.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

# Canvas padding (px, before --scale) around the skeleton's setup-pose AABB, so an
# animated bone can swing an attachment outside the setup silhouette without clipping.
MARGIN_PX = 40.0

_SUPPORTED_TIMELINES = ("rotate", "translate")


class RenderError(ValueError):
    """A skeleton JSON uses something outside the Spine 4.3 subset `spinerig generate`
    writes; str(error) names the offending bone/slot/attachment/timeline/keyframe/file."""


@dataclass(frozen=True)
class _BoneWorld:
    x: float
    y: float
    rotation: float  # degrees, cumulative from root


def _no_curve(keys: list[dict[str, Any]], *, context: str) -> None:
    for key in keys:
        if "curve" in key:
            raise RenderError(f"{context}: keyframe at time {key.get('time', 0)} has 'curve'; only linear keyframes are supported")


def _sample(keys: list[dict[str, Any]], t: float, field: str) -> float:
    """Linear interpolation of `field` (default 0) across ascending keyframes; clamps to
    the first/last keyframe's value outside their time range."""
    if not keys:
        return 0.0
    if t <= keys[0]["time"]:
        return keys[0].get(field, 0.0)
    if t >= keys[-1]["time"]:
        return keys[-1].get(field, 0.0)
    for a, b in zip(keys, keys[1:]):
        if a["time"] <= t <= b["time"]:
            span = b["time"] - a["time"]
            frac = 0.0 if span <= 0 else (t - a["time"]) / span
            return a.get(field, 0.0) + frac * (b.get(field, 0.0) - a.get(field, 0.0))
    return keys[-1].get(field, 0.0)


def _bone_local_at(bone: dict[str, Any], timeline: dict[str, Any] | None, t: float, *, context: str) -> tuple[float, float, float]:
    x, y, rotation = bone.get("x", 0.0), bone.get("y", 0.0), bone.get("rotation", 0.0)
    if not timeline:
        return x, y, rotation
    for name in timeline:
        if name not in _SUPPORTED_TIMELINES:
            raise RenderError(f"{context}: unsupported timeline {name!r} (only {_SUPPORTED_TIMELINES} are)")
    if "rotate" in timeline:
        _no_curve(timeline["rotate"], context=f"{context} rotate")
        rotation += _sample(timeline["rotate"], t, "value")
    if "translate" in timeline:
        _no_curve(timeline["translate"], context=f"{context} translate")
        x += _sample(timeline["translate"], t, "x")
        y += _sample(timeline["translate"], t, "y")
    return x, y, rotation


def animation_duration(animation: dict[str, Any]) -> float:
    """The latest keyframe time across every bone timeline in `animation` -- Spine's own
    generated JSON stores no separate duration field (see this module's docstring)."""
    duration = 0.0
    for timelines in animation.get("bones", {}).values():
        for keys in timelines.values():
            for key in keys:
                duration = max(duration, key.get("time", 0.0))
    return duration


def bone_world_transforms(bones: list[dict[str, Any]], animation: dict[str, Any], t: float) -> dict[str, _BoneWorld]:
    """Forward kinematics at time `t`: each bone's setup pose plus its `rotate`/
    `translate` timeline (a delta on the setup values), composed parent-to-child. `bones`
    must list a bone's parent before the bone itself, as every Spine export does."""
    anim_bones = animation.get("bones", {})
    world: dict[str, _BoneWorld] = {}
    for bone in bones:
        name = bone["name"]
        parent_name = bone.get("parent")
        local_x, local_y, local_rotation = _bone_local_at(bone, anim_bones.get(name), t, context=f"bone {name!r}")
        if parent_name is None:
            world[name] = _BoneWorld(local_x, local_y, local_rotation)
            continue
        if parent_name not in world:
            raise RenderError(f"bone {name!r} lists parent {parent_name!r}, which is unknown or appears later in bones")
        parent = world[parent_name]
        rad = math.radians(parent.rotation)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        world[name] = _BoneWorld(
            x=parent.x + local_x * cos_r - local_y * sin_r,
            y=parent.y + local_x * sin_r + local_y * cos_r,
            rotation=parent.rotation + local_rotation,
        )
    return world


def _default_skin(spine: dict[str, Any]) -> dict[str, Any]:
    for skin in spine.get("skins", []):
        if skin.get("name") == "default":
            return skin
    raise RenderError("skeleton has no 'default' skin")


def _resolve_attachment(skin: dict[str, Any], slot: dict[str, Any]) -> dict[str, Any]:
    slot_name, attachment_name = slot["name"], slot.get("attachment")
    attachment = skin.get("attachments", {}).get(slot_name, {}).get(attachment_name)
    if attachment is None:
        raise RenderError(f"slot {slot_name!r} names attachment {attachment_name!r}, which the default skin does not define")
    attachment_type = attachment.get("type", "region")
    if attachment_type != "region":
        raise RenderError(f"slot {slot_name!r} attachment {attachment_name!r} has type {attachment_type!r}; only region attachments are supported")
    return attachment


def world_to_canvas(x: float, y: float, skeleton: dict[str, Any], scale: float, margin: float) -> tuple[float, float]:
    """Skeleton space (y up) to canvas pixel space (row 0 at the top): flips y about the
    AABB's top edge (`skeleton.y + skeleton.height`) and offsets by `margin`."""
    cx = margin + (x - skeleton["x"]) * scale
    cy = margin + (skeleton["y"] + skeleton["height"] - y) * scale
    return cx, cy


def canvas_size(skeleton: dict[str, Any], scale: float, margin: float) -> tuple[int, int]:
    return (
        round(skeleton["width"] * scale) + 2 * round(margin),
        round(skeleton["height"] * scale) + 2 * round(margin),
    )


def _load_part(parts_dir: Path, path_stem: str, scale: float, cache: dict[tuple[str, float], Image.Image], *, slot_name: str) -> Image.Image:
    key = (path_stem, scale)
    if key not in cache:
        image_path = parts_dir / f"{path_stem}.png"
        if not image_path.is_file():
            raise RenderError(f"slot {slot_name!r} needs part image {image_path.name}, but {image_path} does not exist")
        image = Image.open(image_path).convert("RGBA")
        if scale != 1.0:
            image = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.LANCZOS)
        cache[key] = image
    return cache[key]


def render_frame(
    spine: dict[str, Any],
    parts_dir: Path,
    anim_name: str,
    t: float,
    *,
    scale: float = 1.0,
    margin: float = MARGIN_PX,
    image_cache: dict[tuple[str, float], Image.Image] | None = None,
) -> Image.Image:
    """One frame of `anim_name` at time `t`, as an RGBA `Image` sized by `canvas_size`."""
    animations = spine.get("animations", {})
    if anim_name not in animations:
        raise RenderError(f"animation {anim_name!r} is not in this skeleton (has {sorted(animations)})")
    animation = animations[anim_name]
    skeleton = spine["skeleton"]
    world = bone_world_transforms(spine["bones"], animation, t)
    skin = _default_skin(spine)
    cache = image_cache if image_cache is not None else {}

    width, height = canvas_size(skeleton, scale, margin)
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    for slot in spine["slots"]:
        slot_name, bone_name = slot["name"], slot["bone"]
        if bone_name not in world:
            raise RenderError(f"slot {slot_name!r} references unknown bone {bone_name!r}")
        attachment = _resolve_attachment(skin, slot)
        bone = world[bone_name]
        ax, ay, arot = attachment.get("x", 0.0), attachment.get("y", 0.0), attachment.get("rotation", 0.0)
        rad = math.radians(bone.rotation)
        cos_b, sin_b = math.cos(rad), math.sin(rad)
        center_x = bone.x + ax * cos_b - ay * sin_b
        center_y = bone.y + ax * sin_b + ay * cos_b
        total_rotation = bone.rotation + arot

        path_stem = attachment.get("path", slot_name)
        image = _load_part(parts_dir, path_stem, scale, cache, slot_name=slot_name)
        rotated = image.rotate(total_rotation, expand=True, resample=Image.BICUBIC)
        cx, cy = world_to_canvas(center_x, center_y, skeleton, scale, margin)
        paste_x = round(cx - rotated.width / 2)
        paste_y = round(cy - rotated.height / 2)
        canvas.paste(rotated, (paste_x, paste_y), rotated)

    return canvas


def render_animation(
    spine: dict[str, Any],
    parts_dir: Path,
    anim_name: str,
    *,
    fps: float,
    scale: float = 1.0,
    margin: float = MARGIN_PX,
) -> list[Image.Image]:
    """Every frame of `anim_name`, sampled at `fps` frames per second over its duration
    (see `animation_duration`); `len(result) == round(duration * fps)`."""
    animations = spine.get("animations", {})
    if anim_name not in animations:
        raise RenderError(f"animation {anim_name!r} is not in this skeleton (has {sorted(animations)})")
    duration = animation_duration(animations[anim_name])
    frame_count = max(1, round(duration * fps))
    cache: dict[tuple[str, float], Image.Image] = {}
    return [render_frame(spine, parts_dir, anim_name, i / fps, scale=scale, margin=margin, image_cache=cache) for i in range(frame_count)]
