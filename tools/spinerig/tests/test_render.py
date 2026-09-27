"""Tests for `spinerig.render` (FK playback of a Spine 4.3 JSON subset skeleton to PNG
frames and a GIF, no Spine editor or runtime -- see render.py's module docstring). Every
part image is a real PNG written by Pillow, and every placement assertion inspects the
actual rendered frame's pixels, not just the internal FK numbers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from spinerig.cli import main
from spinerig.render import MARGIN_PX, RenderError, animation_duration, render_animation, render_frame, world_to_canvas


def make_png(path: Path, size: tuple[int, int], color: tuple[int, int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", size, color).save(path)


RED = (220, 30, 30, 255)


def opaque_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    """The pixel bounding box of every non-transparent pixel: (left, top, right, bottom)
    with right/bottom exclusive, the same convention `Image.getbbox()` uses."""
    bbox = image.getchannel("A").getbbox()
    assert bbox is not None, "expected some non-transparent pixels"
    return bbox


def generic_skeleton(*, animations: dict) -> dict:
    """A single root bone with one 20x20 region attachment centred on it (pivot [0.5,
    0.5]) inside a generous AABB -- for tests that check errors or frame counts, not
    exact pixel placement."""
    return {
        "skeleton": {"spine": "4.3.00", "x": -100.0, "y": -100.0, "width": 200.0, "height": 200.0, "images": "parts/"},
        "bones": [{"name": "root"}],
        "slots": [{"name": "part", "bone": "root", "attachment": "part"}],
        "skins": [{"name": "default", "attachments": {"part": {"part": {"path": "part", "x": 0.0, "y": 0.0, "rotation": 0, "width": 20, "height": 20}}}}],
        "animations": animations,
    }


# --- red-rectangle placement (Step 2) --------------------------------------------------


def test_single_bone_part_renders_in_the_expected_rectangle(tmp_path):
    # pivot [0.5, 0] (bottom-centre) on an unrotated root bone: generate.py's own
    # `_attachment_offset` puts the 100x200 part's image centre at world (0, 100), so its
    # world rectangle is x in [-50, 50], y in [0, 200].
    make_png(tmp_path / "parts" / "part.png", (100, 200), RED)
    skeleton = {"spine": "4.3.00", "x": -50.0, "y": 0.0, "width": 100.0, "height": 200.0, "images": "parts/"}
    spine = {
        "skeleton": skeleton,
        "bones": [{"name": "root"}],
        "slots": [{"name": "part", "bone": "root", "attachment": "part"}],
        "skins": [{"name": "default", "attachments": {"part": {"part": {"path": "part", "x": 0.0, "y": 100.0, "rotation": 0, "width": 100, "height": 200}}}}],
        "animations": {"idle": {"bones": {}}},
    }

    frame = render_frame(spine, tmp_path / "parts", "idle", 0.0, scale=1.0)

    expected_left, expected_top = world_to_canvas(-50.0, 200.0, skeleton, 1.0, MARGIN_PX)
    expected_right, expected_bottom = world_to_canvas(50.0, 0.0, skeleton, 1.0, MARGIN_PX)
    left, top, right, bottom = opaque_bbox(frame)
    assert (left, top, right, bottom) == (round(expected_left), round(expected_top), round(expected_right), round(expected_bottom))
    # every pixel inside the rectangle is the part's own red, at full alpha
    assert frame.getpixel((left + 1, top + 1)) == RED
    assert frame.getpixel((right - 2, bottom - 2)) == RED
    # outside the rectangle stays transparent
    assert frame.getpixel((0, 0))[3] == 0


# --- FK at an animated frame (Step 2) ---------------------------------------------------


def test_child_bone_rotation_lands_where_fk_predicts(tmp_path):
    # root -> child (child at local (0, 100), unrotated setup); child's rotate timeline
    # holds 90 degrees at t=0.5, its last keyframe, so t=0.5 samples exactly 90 with no
    # interpolation needed to state the expectation. A 40x80 part sits on `child` at
    # pivot [0.5, 0] (attachment y = 40), rotation 0.
    make_png(tmp_path / "parts" / "part.png", (40, 80), RED)
    skeleton = {"spine": "4.3.00", "x": -150.0, "y": 0.0, "width": 300.0, "height": 250.0, "images": "parts/"}
    spine = {
        "skeleton": skeleton,
        "bones": [
            {"name": "root"},
            {"name": "child", "parent": "root", "x": 0.0, "y": 100.0, "rotation": 0.0},
        ],
        "slots": [{"name": "part", "bone": "child", "attachment": "part"}],
        "skins": [{"name": "default", "attachments": {"part": {"part": {"path": "part", "x": 0.0, "y": 40.0, "rotation": 0, "width": 40, "height": 80}}}}],
        "animations": {"idle": {"bones": {"child": {"rotate": [{"time": 0.0, "value": 0.0}, {"time": 0.5, "value": 90.0}]}}}},
    }

    frame = render_frame(spine, tmp_path / "parts", "idle", 0.5, scale=1.0)

    # FK by hand: child's own position is unaffected by its own rotation (only its
    # parent's rotation moves a bone, and root is unrotated), so child stays at world
    # (0, 100), rotation 90. The attachment centre (bone-local (0, 40)) rotates with the
    # bone: centre = (0 + 0*cos90 - 40*sin90, 100 + 0*sin90 + 40*cos90) = (-40, 100). The
    # 40x80 rectangle rotated 90 degrees about that centre swaps its half-extents: world
    # x in [-80, 0], y in [80, 120].
    expected_left, expected_top = world_to_canvas(-80.0, 120.0, skeleton, 1.0, MARGIN_PX)
    expected_right, expected_bottom = world_to_canvas(0.0, 80.0, skeleton, 1.0, MARGIN_PX)

    left, top, right, bottom = opaque_bbox(frame)
    assert (left, top, right, bottom) == pytest.approx((expected_left, expected_top, expected_right, expected_bottom), abs=1)
    assert frame.getpixel(((left + right) // 2, (top + bottom) // 2)) == RED


# --- GIF frame count (Step 2) ------------------------------------------------------------


def test_gif_has_the_expected_frame_count(tmp_path):
    make_png(tmp_path / "parts" / "part.png", (20, 20), RED)
    # Translate, not rotate: a few pixels of movement per frame guarantees every sampled
    # frame's raster differs from its neighbour, so Pillow's GIF writer (which merges
    # byte-identical consecutive frames rather than encoding a genuine duplicate) can't
    # collapse any of them -- unlike a small-angle rotation of a plain square, which can
    # resample to the same pixels for several consecutive frames.
    spine = generic_skeleton(animations={"run": {"bones": {"root": {"translate": [{"time": 0.0, "x": 0.0}, {"time": 0.6, "x": 90.0}]}}}})
    assert animation_duration(spine["animations"]["run"]) == pytest.approx(0.6)

    frames = render_animation(spine, tmp_path / "parts", "run", fps=30.0)
    assert len(frames) == round(0.6 * 30)

    out_dir = tmp_path / "out"
    skeleton_path = tmp_path / "skeleton.json"
    skeleton_path.write_text(json.dumps(spine))
    rc = main(["render", str(skeleton_path), "--parts", str(tmp_path / "parts"), "--anim", "run", "--out", str(out_dir), "--fps", "30"])

    assert rc == 0
    assert sorted(out_dir.glob("frame_*.png")) == [out_dir / f"frame_{i:04d}.png" for i in range(len(frames))]
    with Image.open(out_dir / "run.gif") as gif:
        frame_count = 0
        try:
            while True:
                gif.seek(frame_count)
                frame_count += 1
        except EOFError:
            pass
    assert frame_count == len(frames)


# --- errors: no silent fallbacks ---------------------------------------------------------


def test_curve_keyframe_raises(tmp_path):
    make_png(tmp_path / "parts" / "part.png", (20, 20), RED)
    spine = generic_skeleton(animations={"idle": {"bones": {"root": {"rotate": [{"time": 0.0, "value": 0.0, "curve": "stepped"}]}}}})

    with pytest.raises(RenderError, match="curve"):
        render_frame(spine, tmp_path / "parts", "idle", 0.0)


def test_missing_part_image_names_the_file(tmp_path):
    spine = generic_skeleton(animations={"idle": {"bones": {}}})

    with pytest.raises(RenderError, match="part.png"):
        render_frame(spine, tmp_path / "parts", "idle", 0.0)


def test_unsupported_timeline_type_raises(tmp_path):
    make_png(tmp_path / "parts" / "part.png", (20, 20), RED)
    spine = generic_skeleton(animations={"idle": {"bones": {"root": {"scale": [{"time": 0.0, "x": 1.0}]}}}})

    with pytest.raises(RenderError, match="scale"):
        render_frame(spine, tmp_path / "parts", "idle", 0.0)


def test_non_region_attachment_raises(tmp_path):
    make_png(tmp_path / "parts" / "part.png", (20, 20), RED)
    spine = generic_skeleton(animations={"idle": {"bones": {}}})
    spine["skins"][0]["attachments"]["part"]["part"]["type"] = "mesh"

    with pytest.raises(RenderError, match="mesh"):
        render_frame(spine, tmp_path / "parts", "idle", 0.0)


# --- the rest of the contract (docs/bakeoff/character-rig.md) ---------------------------


def test_attachment_without_path_raises(tmp_path):
    make_png(tmp_path / "parts" / "part.png", (20, 20), RED)
    spine = generic_skeleton(animations={"idle": {"bones": {}}})
    del spine["skins"][0]["attachments"]["part"]["part"]["path"]
    with pytest.raises(RenderError, match="no 'path'"):
        render_frame(spine, tmp_path / "parts", "idle", 0.0)


def test_slot_without_attachment_raises(tmp_path):
    make_png(tmp_path / "parts" / "part.png", (20, 20), RED)
    spine = generic_skeleton(animations={"idle": {"bones": {}}})
    del spine["slots"][0]["attachment"]
    with pytest.raises(RenderError, match="has no attachment"):
        render_frame(spine, tmp_path / "parts", "idle", 0.0)


def test_non_4_3_skeleton_raises(tmp_path):
    make_png(tmp_path / "parts" / "part.png", (20, 20), RED)
    spine = generic_skeleton(animations={"idle": {"bones": {}}})
    spine["skeleton"]["spine"] = "3.8.99"
    with pytest.raises(RenderError, match="4.3"):
        render_frame(spine, tmp_path / "parts", "idle", 0.0)
