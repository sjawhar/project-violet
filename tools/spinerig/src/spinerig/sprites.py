"""violet-sprites v1: the painted, frame-by-frame protagonist as data every lane reads
(docs/bakeoff/character-rig.md, "Painted sprite sequences").

`build_sprites` turns an authored violet-sprites-src v1 file into the violet-sprites v1
file. It reads the live painted frames (`<anim>-{body,scarf}-NN.png`), each animation's
finalize record (placement fields and `scarf_offset_final`), the hash-bound scarf
attachments and the rig's per-animation durations, and folds every placement scheme
`shoot_b.py`'s `render_cell_b` uses into one anchor per layer per frame:

- grounded (no target fields): body anchor = (`torso_x` or else `head_x`,
  `sole_y` + `place_dy_offset`). The record's own ground point lands on the root.
- airborne, absolute rig units (`target_head_x`/`target_head_y`): `render_cell_b` puts
  the head on the target in cell space at the review scale, so the anchor is the
  root's cell position in source pixels minus that offset:
  `root / scale + head - target_head`.
- airborne, cell fraction (`target_head_x_fraction`/`target_head_y_fraction`, `dash`):
  `head + (root - fraction * cell) / scale`.

`root` is (`head_x_fraction` * cell width, `ground_y_fraction` * cell height) of the
source file's review cell, and `scale` is that cell's scale. The scarf anchor is the
body anchor minus the frame's `scarf_offset_final`.

`render_frame` is the reference reader: it composites one frame from the violet-sprites
file alone, at any scale and root position, body first and then scarf.

This module never imports or runs the asset scripts (shoot.py, shoot_b.py, build.py):
every constant it needs comes from the source file, which quotes where each came from.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFont

from spinerig.render import animation_duration

FORMAT = "violet-sprites"
VERSION = 1
SOURCE_FORMAT = "violet-sprites-src"
SOURCE_VERSION = 1
LAYERS = ("body", "scarf")
# Mean |R-G| + |G-B| over a scarf layer's non-transparent pixels. Above this the scarf
# carries its own hue and multiplying it by the active tag color would muddy it.
MAX_SCARF_CHROMA = 4.0
# apply_scarf_attachments.py's tolerances: a landmark must sit on a pixel whose alpha is
# above this, and the record's offset must be within this many source px of the pins.
LANDMARK_MIN_ALPHA = 8
MAX_BINDING_ERROR_PX = 1.0


class SpritesError(Exception):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _scarf_chroma(image: Image.Image) -> float:
    rgba = image.convert("RGBA")
    total = 0
    count = 0
    for r, g, b, a in rgba.get_flattened_data():
        if a > 0:
            total += abs(r - g) + abs(g - b)
            count += 1
    return total / count if count else 0.0


def _top_opaque_y(image: Image.Image) -> int:
    bbox = image.convert("RGBA").getchannel("A").getbbox()
    if bbox is None:
        raise SpritesError("image has no opaque pixels")
    return bbox[1]


def _live_frames(frames_dir: Path, anim: str) -> dict[str, set[int]]:
    pattern = re.compile(rf"^{re.escape(anim)}-(body|scarf)-(\d+)\.png$")
    found: dict[str, set[int]] = {layer: set() for layer in LAYERS}
    for path in frames_dir.iterdir():
        match = pattern.match(path.name)
        if match:
            found[match.group(1)].add(int(match.group(2)))
    return found


def _frame_path(frames_dir: Path, anim: str, layer: str, index: int) -> Path:
    return frames_dir / f"{anim}-{layer}-{index:02d}.png"


def _require(record_path: Path, index: int, frame: dict[str, Any], *fields: str) -> list[float]:
    values = []
    for field in fields:
        value = frame.get(field)
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise SpritesError(f"{record_path} frame {index}: needs a finite {field!r}")
        values.append(float(value))
    return values


def body_anchor(frame: dict[str, Any], *, record_path: Path, index: int, root: tuple[float, float], cell: tuple[int, int], scale: float) -> tuple[float, float]:
    """The body image pixel (y down) that sits on the root, per the frame's own scheme."""
    if "target_head_x_fraction" in frame:
        head_x, head_y, fx, fy = _require(record_path, index, frame, "head_x", "head_y", "target_head_x_fraction", "target_head_y_fraction")
        return head_x + (root[0] - fx * cell[0]) / scale, head_y + (root[1] - fy * cell[1]) / scale
    if "target_head_x" in frame:
        head_x, head_y, tx, ty = _require(record_path, index, frame, "head_x", "head_y", "target_head_x", "target_head_y")
        return root[0] / scale + head_x - tx, root[1] / scale + head_y - ty
    x_field = "torso_x" if "torso_x" in frame else "head_x"
    (x,) = _require(record_path, index, frame, x_field)
    (sole_y,) = _require(record_path, index, frame, "sole_y")
    lift = 0.0
    if "place_dy_offset" in frame:
        (lift,) = _require(record_path, index, frame, "place_dy_offset")
    return x, sole_y + lift


def _load_pins(path: Path, frames_dir: Path, wanted: set[tuple[str, int]]) -> dict[tuple[str, int], tuple[float, float]]:
    """apply_scarf_attachments.py's check mode, reimplemented: every emitted frame has
    exactly one pin, bound to its body and scarf PNGs' exact bytes, with both landmarks
    on opaque pixels. Returns each frame's wanted scarf offset (body_neck - scarf_knot)."""
    pins = json.loads(path.read_text())["frames"]
    offsets: dict[tuple[str, int], tuple[float, float]] = {}
    for pin in pins:
        key = (pin["animation"], pin["index"])
        if key in offsets:
            raise SpritesError(f"{path}: duplicate attachment for {key[0]} frame {key[1]}")
        if key not in wanted:
            raise SpritesError(f"{path}: attachment for {key[0]} frame {key[1]}, which is not a live frame of any listed animation")
        for layer, field in (("body", "body_neck"), ("scarf", "scarf_knot")):
            png = _frame_path(frames_dir, key[0], layer, key[1])
            if _sha256(png) != pin[f"{layer}_sha256"]:
                raise SpritesError(f"{png}: pixels changed since {path} bound its {field}; re-author the attachment landmark")
            point = pin[field]
            if len(point) != 2 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in point):
                raise SpritesError(f"{path}: {png.name} has an invalid {field}")
            with Image.open(png) as image:
                x, y = map(round, point)
                if not (0 <= x < image.width and 0 <= y < image.height):
                    raise SpritesError(f"{path}: {png.name}'s {field} is outside the image")
                if image.convert("RGBA").getpixel((x, y))[3] <= LANDMARK_MIN_ALPHA:
                    raise SpritesError(f"{path}: {png.name}'s {field} is on transparent pixels")
        offsets[key] = (pin["body_neck"][0] - pin["scarf_knot"][0], pin["body_neck"][1] - pin["scarf_knot"][1])
    missing = sorted(wanted - offsets.keys())
    if missing:
        anim, index = missing[0]
        raise SpritesError(f"{path}: no attachment for {anim} frame {index} ({len(missing)} frames unbound)")
    return offsets


def build_sprites(source_path: Path, out_path: Path) -> dict[str, Any]:
    """The violet-sprites v1 document for `source_path`, with image paths relative to
    `out_path`'s directory. Raises SpritesError naming the offending file or frame."""
    source = json.loads(source_path.read_text())
    if source.get("format") != SOURCE_FORMAT or source.get("version") != SOURCE_VERSION:
        raise SpritesError(f"{source_path}: expected format {SOURCE_FORMAT!r} version {SOURCE_VERSION}")
    base = source_path.parent
    rig_path = base / source["rig"]
    frames_dir = base / source["frames_dir"]
    pins_path = base / source["scarf_attachments"]
    cell = (int(source["cell"]["width"]), int(source["cell"]["height"]))
    scale = float(source["cell"]["scale"])
    gx, gy = source["ground_y_fraction"]
    hx, hy = source["head_x_fraction"]
    root = (hx / hy * cell[0], gx / gy * cell[1])

    rig_animations = json.loads(rig_path.read_text())["animations"]
    plans = []
    wanted: set[tuple[str, int]] = set()
    for anim, spec in source["animations"].items():
        if anim not in rig_animations:
            raise SpritesError(f"{rig_path}: no animation {anim!r} (listed in {source_path})")
        duration = animation_duration(rig_animations[anim])
        if duration <= 0:
            raise SpritesError(f"{rig_path}: animation {anim!r} has no duration")
        record_path = frames_dir / spec["record"]
        if not record_path.is_file():
            raise SpritesError(f"{record_path}: finalize record for {anim!r} does not exist")
        record = {int(k): v for k, v in json.loads(record_path.read_text()).items()}
        count = len(record)
        if sorted(record) != list(range(count)):
            raise SpritesError(f"{record_path}: frame indices must be 0..{count - 1}, got {sorted(record)}")
        live = _live_frames(frames_dir, anim)
        for layer in LAYERS:
            for index in range(count):
                if index not in live[layer]:
                    raise SpritesError(f"{_frame_path(frames_dir, anim, layer, index)}: missing ({record_path.name} has frame {index})")
            extra = sorted(live[layer] - set(range(count)))
            if extra:
                raise SpritesError(f"{_frame_path(frames_dir, anim, layer, extra[0])}: live frame with no entry in {record_path.name}")
        wanted.update((anim, index) for index in range(count))
        plans.append((anim, spec, duration, record_path, record))

    pin_offsets = _load_pins(pins_path, frames_dir, wanted)

    out_dir = out_path.parent
    animations: dict[str, Any] = {}
    height_px = None
    for anim, spec, duration, record_path, record in plans:
        frames = []
        for index in range(len(record)):
            frame = record[index]
            if "scarf_offset_final" not in frame:
                raise SpritesError(f"{record_path} frame {index}: no scarf_offset_final; run apply_scarf_attachments.py apply")
            offset = [float(v) for v in frame["scarf_offset_final"]]
            if not math.dist(offset, pin_offsets[(anim, index)]) <= MAX_BINDING_ERROR_PX:
                raise SpritesError(f"{record_path} frame {index}: scarf_offset_final misses the bound neck; run apply_scarf_attachments.py apply")
            scarf_png = _frame_path(frames_dir, anim, "scarf", index)
            with Image.open(scarf_png) as scarf_image:
                chroma = _scarf_chroma(scarf_image)
            if chroma > MAX_SCARF_CHROMA:
                raise SpritesError(f"{scarf_png}: scarf layer is colored (mean |R-G|+|G-B| {chroma:.2f} > {MAX_SCARF_CHROMA}); lanes tint it, so it must be neutral gray")
            bx, by = body_anchor(frame, record_path=record_path, index=index, root=root, cell=cell, scale=scale)
            if anim == "idle" and index == 0:
                body_png = _frame_path(frames_dir, anim, "body", index)
                with Image.open(body_png) as body_image:
                    height_px = float(frame["sole_y"]) - _top_opaque_y(body_image)
            frames.append({
                "body": {"image": _rel(_frame_path(frames_dir, anim, "body", index), out_dir), "anchor": [bx, by]},
                "scarf": {"image": _rel(scarf_png, out_dir), "anchor": [bx - offset[0], by - offset[1]]},
            })
        animations[anim] = {"duration": duration, "loop": bool(spec["loop"]), "frames": frames}

    if height_px is None:
        raise SpritesError(f"{source_path}: height_px is idle frame 0's height, but 'idle' is not listed")
    return {
        "format": FORMAT,
        "version": VERSION,
        "facing": "right",
        "height_px": height_px,
        "units": "px",
        "animations": animations,
    }


def _rel(path: Path, start: Path) -> str:
    return Path(os.path.relpath(path.resolve(), start.resolve())).as_posix()


def frame_index_at(t: float, duration: float, count: int, loop: bool) -> int:
    """The painted frame showing at time t: evenly spaced, held, never interpolated."""
    if t < 0:
        raise SpritesError(f"time {t} is negative")
    if loop:
        t = math.fmod(t, duration)
    return min(math.floor(t * count / duration), count - 1)


def load_sprites(path: Path) -> dict[str, Any]:
    sprites = json.loads(path.read_text())
    if sprites.get("format") != FORMAT or sprites.get("version") != VERSION:
        raise SpritesError(f"{path}: expected format {FORMAT!r} version {VERSION}")
    if sprites.get("facing") != "right" or sprites.get("units") != "px":
        raise SpritesError(f"{path}: expected facing 'right' and units 'px'")
    return sprites


def _layer_image(sprites_dir: Path, image: str, scale: float, cache: dict) -> Image.Image:
    key = (image, scale)
    if key not in cache:
        loaded = Image.open(sprites_dir / image).convert("RGBA")
        if scale != 1.0:
            loaded = loaded.resize((max(1, round(loaded.width * scale)), max(1, round(loaded.height * scale))), Image.LANCZOS)
        cache[key] = loaded
    return cache[key]


def render_frame(
    sprites: dict[str, Any],
    sprites_dir: Path,
    anim: str,
    t: float,
    *,
    scale: float,
    root: tuple[float, float],
    size: tuple[int, int],
    background: tuple[int, int, int, int] = (0, 0, 0, 0),
    tint: tuple[int, int, int] | None = None,
    cache: dict | None = None,
) -> Image.Image:
    """Composite `anim` at time `t` onto a `size` canvas: each layer drawn at `scale` with
    its anchor pixel on `root` (canvas px, y down), body first, then the scarf multiplied
    by `tint` (no tint leaves it gray)."""
    if anim not in sprites["animations"]:
        raise SpritesError(f"{sprites_dir}: violet-sprites file has no animation {anim!r}")
    cache = {} if cache is None else cache
    animation = sprites["animations"][anim]
    frame = animation["frames"][frame_index_at(t, animation["duration"], len(animation["frames"]), animation["loop"])]
    canvas = Image.new("RGBA", size, background)
    for layer in LAYERS:
        image = _layer_image(sprites_dir, frame[layer]["image"], scale, cache)
        if layer == "scarf" and tint is not None:
            image = ImageChops.multiply(image, Image.new("RGBA", image.size, (*tint, 255)))
        ax, ay = frame[layer]["anchor"]
        _draw_over(canvas, image, (round(root[0] - ax * scale), round(root[1] - ay * scale)))
    return canvas


def _draw_over(canvas: Image.Image, image: Image.Image, position: tuple[int, int]) -> None:
    """Source-over `image` onto `canvas` with its top-left at `position`, which may lie
    off the canvas: only the visible part of `image` is composited."""
    x, y = position
    left, top = max(0, -x), max(0, -y)
    right, bottom = min(image.width, canvas.width - x), min(image.height, canvas.height - y)
    if right > left and bottom > top:
        canvas.alpha_composite(image, dest=(x + left, y + top), source=(left, top, right, bottom))


def sample_times(duration: float, loop: bool, columns: int) -> list[float]:
    """Evenly spaced times: a loop's period without its repeated end, a held
    animation's both endpoints (shoot.py's contact-sheet rule)."""
    if loop:
        return [i * duration / columns for i in range(columns)]
    return [i * duration / (columns - 1) for i in range(columns)]


SHEET_LABEL_W = 90
SHEET_GUTTER = 2
SHEET_BACKGROUND = (128, 128, 128, 255)


def render_sheet(
    sprites: dict[str, Any],
    sprites_dir: Path,
    *,
    scale: float,
    root: tuple[float, float],
    cell: tuple[int, int],
    columns: int = 6,
    tint: tuple[int, int, int] | None = None,
) -> Image.Image:
    """One row per animation in file order, `columns` sample times each, a label column
    on the left: shoot.py's contact-sheet layout, rendered from the violet-sprites file."""
    names = list(sprites["animations"])
    width = SHEET_LABEL_W + columns * cell[0] + (columns - 1) * SHEET_GUTTER
    height = len(names) * cell[1] + (len(names) - 1) * SHEET_GUTTER
    sheet = Image.new("RGBA", (width, height), SHEET_BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    cache: dict = {}
    for row, anim in enumerate(names):
        animation = sprites["animations"][anim]
        y0 = row * (cell[1] + SHEET_GUTTER)
        draw.text((6, y0 + cell[1] // 2 - 6), anim, fill=(20, 20, 20, 255), font=font)
        for col, t in enumerate(sample_times(animation["duration"], animation["loop"], columns)):
            frame = render_frame(sprites, sprites_dir, anim, t, scale=scale, root=root, size=cell, background=SHEET_BACKGROUND, tint=tint, cache=cache)
            sheet.paste(frame, (SHEET_LABEL_W + col * (cell[0] + SHEET_GUTTER), y0))
    return sheet
