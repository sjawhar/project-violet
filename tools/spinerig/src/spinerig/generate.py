"""Builds a Spine 4.3 JSON skeleton from a `violet-rig` v1 description.

Structure (top-level keys, bone/slot/attachment fields, parent-before-child ordering)
follows https://esotericsoftware.com/spine-json-format (accessed 2026-09-27) -- but that
page documents the 3.8 export format (its own example says `"spine": "3.8.24"`) and is
wrong about one field for 4.x: a bone's `rotate` timeline keyframe holds `value`, not
`angle`. Verified against the actual 4.3 runtime source, github.com/EsotericSoftware/
spine-runtimes, branch `4.3`, `spine-ts/spine-core/src/SkeletonJson.ts`: `readTimeline1`
(used for `rotate`, at the `case "rotate":` in the bone-timelines loop) reads
`keyMap.value`, and the branch's own example export, `examples/spineboy/export/
spineboy-pro.json`, confirms it (`"rotate": [{"value": ...}]`). Every other field this
module emits was checked the same way and is unchanged from the page: the skeleton
section's `x/y/width/height/images`, bone `name/parent/x/y/rotation/length`, slot
`name/bone/attachment`, and region attachment `path/x/y/rotation/width/height` all read
by the same (or directly corresponding) `getValue(map, "field", default)` calls in
`SkeletonJson.ts`. Bezier `curve` keyframes are a real 4.x behavior difference (a
1-value timeline like `rotate` reads a 4-number array; a 2-value timeline like
`translate` reads two 4-number curves packed into 8 numbers, per `readCurve`'s `value <<
2` offset) that this module does not need to reproduce, so it refuses `curve` on any
authored keyframe rather than emit a rig with the wrong bezier shape.

A `violet-rig` v1 document (the input this module reads):

    {
      "parts_dir": "path relative to the rig.json, containing the part images",
      "bones": [{"name", "parent"?, "x"?, "y"?, "rotation"?, "length"?}, ...],
      "parts": [{"slot", "bone", "image", "pivot": [px, py], "rotation"?}, ...],
      "draw_order": ["slot", ...],
      "scarf": {"bones": ["bone", ...], "trail_deg": {"anim": deg, ...},
                "flutter_deg": deg, "flutter_hz": hz, "lag_frames": n, "gain": [f, ...]},
      "animations": {"name": {"duration": s, "loop"?: bool,
                               "bones": {"bone": {"rotate": [{"time", "angle"}, ...],
                                                   "translate": [{"time", "x"?, "y"?}, ...]}}}}
    }

`rotate`/`translate` are the only supported timeline types; `angle` (not Spine's own
`value`) is this schema's input name for a rotate keyframe's angle in degrees -- this
module translates it to `value` on output, the field the 4.3 runtime actually reads.

Spine conventions apply throughout: y is up, angles are in degrees, and `bones` lists a
bone's parent before the bone itself. `pivot` is the point of the part's image (0-1,
origin bottom-left) that sits on its bone's origin; `rotation` on a part is the image's
up-axis angle relative to the bone. `scarf.bones` names a chain (root end first); this
module adds a `rotate` timeline to each of those bones in every animation (`scarf.py`)
rather than requiring the rig author to hand-key them. `skeleton.images` is computed as
the relative path from the generated file's own directory to the resolved `parts_dir`
(POSIX separators, trailing slash), the way the 4.3 example export writes `"./images/"`

No silent fallbacks: an unknown bone reference, a bone whose parent appears later in
`bones`, a missing part image, a `draw_order`/part slot mismatch, an unsupported
animation timeline type, or a keyframe `curve` all raise `RigError` naming the offending
bone, slot, file, timeline, or animation.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from spinerig import scarf as scarf_module

SPINE_VERSION = "4.3.00"


class RigError(ValueError):
    """A violet-rig v1 document is malformed; str(error) names the offending bone/slot/file."""


@dataclass(frozen=True)
class PartInfo:
    """One part's resolved image, for `--print-parts`."""

    slot: str
    image: str
    width: int
    height: int


@dataclass(frozen=True)
class _BoneWorld:
    x: float
    y: float
    rotation: float  # degrees, cumulative from root


def _bone_world_transforms(bones: list[dict[str, Any]]) -> dict[str, _BoneWorld]:
    by_name = {bone["name"]: bone for bone in bones}
    world: dict[str, _BoneWorld] = {}
    for bone in bones:
        name = bone["name"]
        parent_name = bone.get("parent")
        local_x, local_y = bone.get("x", 0.0), bone.get("y", 0.0)
        local_rotation = bone.get("rotation", 0.0)
        if parent_name is None:
            world[name] = _BoneWorld(local_x, local_y, local_rotation)
            continue
        if parent_name not in by_name:
            raise RigError(f"bone {name!r} has unknown parent {parent_name!r}")
        if parent_name not in world:
            raise RigError(f"bone {name!r} lists parent {parent_name!r}, which appears later in bones (child before parent)")
        parent = world[parent_name]
        rad = math.radians(parent.rotation)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        world[name] = _BoneWorld(
            x=parent.x + local_x * cos_r - local_y * sin_r,
            y=parent.y + local_x * sin_r + local_y * cos_r,
            rotation=parent.rotation + local_rotation,
        )
    return world


def _attachment_offset(pivot: tuple[float, float], rotation_deg: float, width: float, height: float) -> tuple[float, float]:
    """The image centre relative to the pivot, rotated into bone space."""
    px, py = pivot
    dx = (0.5 - px) * width
    dy = (0.5 - py) * height
    rad = math.radians(rotation_deg)
    cos_r, sin_r = math.cos(rad), math.sin(rad)
    return dx * cos_r - dy * sin_r, dx * sin_r + dy * cos_r


def _world_corners(bone: _BoneWorld, ax: float, ay: float, arot: float, width: float, height: float) -> list[tuple[float, float]]:
    """The four corners of an attachment's rectangle in skeleton (root) space, setup pose."""
    rad_bone = math.radians(bone.rotation)
    cos_b, sin_b = math.cos(rad_bone), math.sin(rad_bone)
    center_x = bone.x + ax * cos_b - ay * sin_b
    center_y = bone.y + ax * sin_b + ay * cos_b
    rad_attach = math.radians(bone.rotation + arot)
    cos_a, sin_a = math.cos(rad_attach), math.sin(rad_attach)
    half_w, half_h = width / 2, height / 2
    corners = []
    for hx, hy in ((-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)):
        corners.append((center_x + hx * cos_a - hy * sin_a, center_y + hx * sin_a + hy * cos_a))
    return corners


def _images_path(parts_dir: Path, out_dir: Path) -> str:
    """The `skeleton.images` value: `out_dir` (where the generated JSON will live) to
    `parts_dir`, as a POSIX-style relative path with a trailing slash -- e.g. `"../parts/"`
    for the plan's `rig-src/` (out) beside `parts/` layout, but computed for whatever
    layout the caller actually uses, not assumed."""
    relative = os.path.relpath(parts_dir.resolve(), out_dir.resolve())
    return relative.replace(os.sep, "/") + "/"


def _resolve_parts(rig: dict[str, Any], parts_dir: Path, bone_names: set[str], world: dict[str, _BoneWorld]):
    """`parts_dir` is already resolved (base_dir / rig["parts_dir"])."""
    part_by_slot: dict[str, dict[str, Any]] = {}
    part_infos: list[PartInfo] = []
    corners: list[tuple[float, float]] = []
    for part in rig["parts"]:
        slot = part["slot"]
        bone_name = part["bone"]
        if bone_name not in bone_names:
            raise RigError(f"part {slot!r} references unknown bone {bone_name!r}")
        image_path = parts_dir / part["image"]
        if not image_path.is_file():
            raise RigError(f"part {slot!r} references missing image file {image_path}")
        with Image.open(image_path) as img:
            width, height = img.size
        rotation = part.get("rotation", 0.0)
        x, y = _attachment_offset(tuple(part["pivot"]), rotation, width, height)
        part_by_slot[slot] = {
            "bone": bone_name,
            "image": part["image"],
            "x": x,
            "y": y,
            "rotation": rotation,
            "width": width,
            "height": height,
        }
        part_infos.append(PartInfo(slot=slot, image=part["image"], width=width, height=height))
        corners.extend(_world_corners(world[bone_name], x, y, rotation, width, height))
    return part_by_slot, part_infos, corners


def _slots_and_skin(rig: dict[str, Any], part_by_slot: dict[str, dict[str, Any]]) -> tuple[list[dict], dict[str, Any]]:
    draw_order: list[str] = rig["draw_order"]
    defined_slots = set(part_by_slot)
    draw_order_slots = set(draw_order)
    for slot in draw_order:
        if slot not in defined_slots:
            raise RigError(f"draw_order names slot {slot!r}, which no part defines")
    for slot in defined_slots:
        if slot not in draw_order_slots:
            raise RigError(f"part slot {slot!r} does not appear in draw_order")

    slots_json = []
    attachments_json = {}
    for slot in draw_order:
        part = part_by_slot[slot]
        slots_json.append({"name": slot, "bone": part["bone"], "attachment": slot})
        attachments_json[slot] = {
            slot: {
                "path": Path(part["image"]).stem,
                "x": part["x"],
                "y": part["y"],
                "rotation": part["rotation"],
                "width": part["width"],
                "height": part["height"],
            }
        }
    return slots_json, attachments_json


def _bones_json(bones: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for bone in bones:
        entry: dict[str, Any] = {"name": bone["name"]}
        if bone.get("parent") is not None:
            entry["parent"] = bone["parent"]
        for key in ("x", "y", "rotation", "length"):
            if key in bone:
                entry[key] = bone[key]
        out.append(entry)
    return out


def _add_scarf_keys(
    anim_name: str,
    anim: dict[str, Any],
    scarf: dict[str, Any],
    anim_bones: dict[str, Any],
    bone_names: set[str],
) -> None:
    chain: list[str] = scarf["bones"]
    for bone_name in chain:
        if bone_name not in bone_names:
            raise RigError(f"scarf.bones references unknown bone {bone_name!r}")
    if anim_name not in scarf["trail_deg"]:
        raise RigError(f"scarf.trail_deg has no entry for animation {anim_name!r}")
    gains: list[float] = scarf["gain"]
    if len(gains) != len(chain):
        raise RigError(f"scarf.gain has {len(gains)} entries but scarf.bones has {len(chain)}")

    duration = anim["duration"]
    loop = anim.get("loop", True)
    trail_deg = scarf["trail_deg"][anim_name]
    for index, bone_name in enumerate(chain):
        keys = scarf_module.rotate_keys(
            duration=duration,
            loop=loop,
            gain=gains[index],
            trail_deg=trail_deg,
            flutter_deg=scarf["flutter_deg"],
            flutter_hz=scarf["flutter_hz"],
            lag_frames=scarf["lag_frames"],
            chain_index=index,
        )
        anim_bones[bone_name] = {"rotate": keys}


_SUPPORTED_TIMELINES = ("rotate", "translate")


def _authored_bone_timeline(anim_name: str, bone_name: str, timeline: dict[str, Any]) -> dict[str, Any]:
    """Translates an authored `{"rotate": [{time, angle}], "translate": [{time, x, y}]}`
    timeline into what the Spine 4.x runtime actually reads: a rotate keyframe's angle is
    `value`, not the 3.8-era `angle` this schema uses for its input. `curve` keyframes are
    refused (see the module docstring) rather than passed through with the wrong shape.
    """
    context = f"animation {anim_name!r} bone {bone_name!r}"
    out: dict[str, Any] = {}
    for timeline_name, entries in timeline.items():
        if timeline_name not in _SUPPORTED_TIMELINES:
            raise RigError(f"{context}: unsupported timeline {timeline_name!r} (only {_SUPPORTED_TIMELINES} are)")
        keys = []
        for entry in entries:
            if "curve" in entry:
                raise RigError(f"{context}: a {timeline_name!r} keyframe has 'curve'; only linear keyframes are supported")
            key: dict[str, Any] = {"time": entry.get("time", 0)}
            if timeline_name == "rotate":
                key["value"] = entry.get("angle", 0)
            else:
                if "x" in entry:
                    key["x"] = entry["x"]
                if "y" in entry:
                    key["y"] = entry["y"]
            keys.append(key)
        out[timeline_name] = keys
    return out


def _animations_json(rig: dict[str, Any], bone_names: set[str]) -> dict[str, Any]:
    scarf = rig.get("scarf")
    animations_json = {}
    for anim_name, anim in rig["animations"].items():
        anim_bones = {
            name: _authored_bone_timeline(anim_name, name, timeline)
            for name, timeline in anim.get("bones", {}).items()
        }
        if scarf is not None:
            _add_scarf_keys(anim_name, anim, scarf, anim_bones, bone_names)
        animations_json[anim_name] = {"bones": anim_bones}
    return animations_json


def generate(rig: dict[str, Any], base_dir: Path, out_dir: Path) -> tuple[dict[str, Any], dict[str, Any], list[PartInfo]]:
    """Returns `(spine_json, meta_json, parts)` for a violet-rig v1 document.

    `base_dir` is the rig.json's own directory; `parts_dir` and every part's `image` are
    resolved relative to it. `out_dir` is the directory the generated Spine JSON will be
    written to (the CLI's `--out`'s parent) -- used only to compute `skeleton.images`.
    """
    bones: list[dict[str, Any]] = rig["bones"]
    bone_names = {bone["name"] for bone in bones}
    world = _bone_world_transforms(bones)
    parts_dir = base_dir / rig["parts_dir"]

    part_by_slot, part_infos, corners = _resolve_parts(rig, parts_dir, bone_names, world)
    slots_json, attachments_json = _slots_and_skin(rig, part_by_slot)
    animations_json = _animations_json(rig, bone_names)

    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    height = max_y - min_y

    spine_json = {
        "skeleton": {
            "spine": SPINE_VERSION,
            "x": min_x,
            "y": min_y,
            "width": max_x - min_x,
            "height": height,
            "images": _images_path(parts_dir, out_dir),
        },
        "bones": _bones_json(bones),
        "slots": slots_json,
        "skins": [{"name": "default", "attachments": attachments_json}],
        "animations": animations_json,
    }
    meta_json = {"height_px": height, "feet_y_px": 0, "facing": "right"}
    return spine_json, meta_json, part_infos
