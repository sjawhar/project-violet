"""Tests for `spinerig.generate` (structure of the Spine 4.3 JSON it emits, validated
against the actual 4.3 runtime source and example export -- see generate.py's module
docstring, not just https://esotericsoftware.com/spine-json-format, which documents the
3.8 format) and the `spinerig generate` CLI. Every rig uses real PNGs written by Pillow
in `tmp_path`, since `generate()` reads part sizes from the actual image files."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from spinerig.cli import main
from spinerig.generate import RigError, generate


def make_png(path: Path, size: tuple[int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", size, (0, 0, 0, 0)).save(path)


def base_rig(*, bones, parts, draw_order, animations=None, scarf=None, parts_dir="parts"):
    rig = {
        "parts_dir": parts_dir,
        "bones": bones,
        "parts": parts,
        "draw_order": draw_order,
        "animations": animations if animations is not None else {},
    }
    if scarf is not None:
        rig["scarf"] = scarf
    return rig


def minimal_rig(tmp_path: Path):
    make_png(tmp_path / "parts" / "part1.png", (64, 64))
    rig = base_rig(
        bones=[{"name": "root"}],
        parts=[{"slot": "part1", "bone": "root", "image": "part1.png", "pivot": [0.5, 0.5], "rotation": 0}],
        draw_order=["part1"],
        animations={"idle": {"duration": 1.0, "bones": {}}},
    )
    return rig, tmp_path


# --- pivot / rotation placement (Step 2) ---------------------------------------------


def test_pivot_places_the_attachment_with_no_rotation(tmp_path):
    make_png(tmp_path / "parts" / "part1.png", (100, 200))
    rig = base_rig(
        bones=[{"name": "root"}, {"name": "bone2", "parent": "root"}],
        parts=[{"slot": "part1", "bone": "bone2", "image": "part1.png", "pivot": [0.5, 0.0], "rotation": 0}],
        draw_order=["part1"],
    )

    spine, _, _ = generate(rig, tmp_path, tmp_path)

    attachment = spine["skins"][0]["attachments"]["part1"]["part1"]
    assert attachment["x"] == pytest.approx(0.0, abs=1e-6)
    assert attachment["y"] == pytest.approx(100.0, abs=1e-6)


def test_rotation_places_the_attachment(tmp_path):
    make_png(tmp_path / "parts" / "part1.png", (100, 200))
    rig = base_rig(
        bones=[{"name": "root"}, {"name": "bone2", "parent": "root"}],
        parts=[{"slot": "part1", "bone": "bone2", "image": "part1.png", "pivot": [0.5, 0.0], "rotation": 90}],
        draw_order=["part1"],
    )

    spine, _, _ = generate(rig, tmp_path, tmp_path)

    attachment = spine["skins"][0]["attachments"]["part1"]["part1"]
    assert attachment["x"] == pytest.approx(-100.0, abs=1e-6)
    assert attachment["y"] == pytest.approx(0.0, abs=1e-6)


# --- scarf follow-through (Step 2) ----------------------------------------------------


def test_scarf_amplitude_decreases_and_phase_increases_along_chain(tmp_path):
    make_png(tmp_path / "parts" / "head.png", (80, 80))
    for name in ("scarf1", "scarf2", "scarf3"):
        make_png(tmp_path / "parts" / f"{name}.png", (40, 20))
    bones = [
        {"name": "root"},
        {"name": "head", "parent": "root"},
        {"name": "scarf1", "parent": "head"},
        {"name": "scarf2", "parent": "scarf1", "x": 40},
        {"name": "scarf3", "parent": "scarf2", "x": 40},
    ]
    parts = [
        {"slot": "head", "bone": "head", "image": "head.png", "pivot": [0.5, 0.5], "rotation": 0},
        {"slot": "scarf1", "bone": "scarf1", "image": "scarf1.png", "pivot": [1.0, 0.5], "rotation": 0},
        {"slot": "scarf2", "bone": "scarf2", "image": "scarf2.png", "pivot": [1.0, 0.5], "rotation": 0},
        {"slot": "scarf3", "bone": "scarf3", "image": "scarf3.png", "pivot": [1.0, 0.5], "rotation": 0},
    ]
    chain = ["scarf1", "scarf2", "scarf3"]
    gain = [1.0, 0.6, 0.3]
    scarf = {
        "bones": chain,
        "trail_deg": {"idle": 0.0},  # isolate the flutter term from the (amplitude-neutral) trail offset
        "flutter_deg": 10.0,
        "flutter_hz": 1.0,
        "lag_frames": 6.0,  # 6/30s == 3 * (2/30)s: an exact multiple of the 2-frame sample step
        "gain": gain,
    }
    rig = base_rig(
        bones=bones,
        parts=parts,
        draw_order=["head", "scarf1", "scarf2", "scarf3"],
        animations={"idle": {"duration": 1.0, "loop": False, "bones": {}}},
        scarf=scarf,
    )

    spine, _, _ = generate(rig, tmp_path, tmp_path)
    keys = {name: spine["animations"]["idle"]["bones"][name]["rotate"] for name in chain}

    amplitudes = [max(abs(key["value"]) for key in keys[name]) for name in chain]
    assert amplitudes[0] > amplitudes[1] > amplitudes[2]

    # The lag is an exact multiple of the sample step, so bone i's value at sample k,
    # scaled by its own gain, equals bone 0's value 3*i samples earlier scaled by its gain
    # -- the phase delay growing with each bone in the chain.
    k = 6
    for index, name in enumerate(chain):
        expected = keys["scarf1"][k - 3 * index]["value"] / gain[0]
        actual = keys[name][k]["value"] / gain[index]
        assert actual == pytest.approx(expected, abs=1e-6)


def test_scarf_keys_loop_to_avoid_a_pop(tmp_path):
    make_png(tmp_path / "parts" / "head.png", (80, 80))
    make_png(tmp_path / "parts" / "scarf1.png", (40, 20))
    rig = base_rig(
        bones=[{"name": "root"}, {"name": "head", "parent": "root"}, {"name": "scarf1", "parent": "head"}],
        parts=[
            {"slot": "head", "bone": "head", "image": "head.png", "pivot": [0.5, 0.5], "rotation": 0},
            {"slot": "scarf1", "bone": "scarf1", "image": "scarf1.png", "pivot": [1.0, 0.5], "rotation": 0},
        ],
        draw_order=["head", "scarf1"],
        animations={"idle": {"duration": 0.77, "loop": True, "bones": {}}},
        scarf={"bones": ["scarf1"], "trail_deg": {"idle": 5.0}, "flutter_deg": 8.0, "flutter_hz": 2.5, "lag_frames": 2, "gain": [1.0]},
    )

    spine, _, _ = generate(rig, tmp_path, tmp_path)

    keys = spine["animations"]["idle"]["bones"]["scarf1"]["rotate"]
    assert keys[0]["time"] == 0
    assert keys[-1]["time"] == pytest.approx(0.77)
    assert keys[-1]["value"] == pytest.approx(keys[0]["value"])


# --- errors: no silent fallbacks -------------------------------------------------------


def test_missing_part_image_names_the_file(tmp_path):
    rig = base_rig(
        bones=[{"name": "root"}],
        parts=[{"slot": "part1", "bone": "root", "image": "missing.png", "pivot": [0.5, 0.5], "rotation": 0}],
        draw_order=["part1"],
    )

    with pytest.raises(RigError, match="missing.png"):
        generate(rig, tmp_path, tmp_path)


def test_part_referencing_an_unknown_bone_raises(tmp_path):
    make_png(tmp_path / "parts" / "part1.png", (10, 10))
    rig = base_rig(
        bones=[{"name": "root"}],
        parts=[{"slot": "part1", "bone": "nope", "image": "part1.png", "pivot": [0.5, 0.5], "rotation": 0}],
        draw_order=["part1"],
    )

    with pytest.raises(RigError, match="nope"):
        generate(rig, tmp_path, tmp_path)


def test_bone_with_an_unknown_parent_raises(tmp_path):
    make_png(tmp_path / "parts" / "part1.png", (10, 10))
    rig = base_rig(
        bones=[{"name": "root"}, {"name": "child", "parent": "ghost"}],
        parts=[{"slot": "part1", "bone": "root", "image": "part1.png", "pivot": [0.5, 0.5], "rotation": 0}],
        draw_order=["part1"],
    )

    with pytest.raises(RigError, match="ghost"):
        generate(rig, tmp_path, tmp_path)


def test_child_before_its_parent_raises(tmp_path):
    make_png(tmp_path / "parts" / "part1.png", (10, 10))
    rig = base_rig(
        bones=[{"name": "child", "parent": "root"}, {"name": "root"}],
        parts=[{"slot": "part1", "bone": "root", "image": "part1.png", "pivot": [0.5, 0.5], "rotation": 0}],
        draw_order=["part1"],
    )

    with pytest.raises(RigError, match="child before parent"):
        generate(rig, tmp_path, tmp_path)


def test_draw_order_naming_an_undefined_slot_raises(tmp_path):
    make_png(tmp_path / "parts" / "part1.png", (10, 10))
    rig = base_rig(
        bones=[{"name": "root"}],
        parts=[{"slot": "part1", "bone": "root", "image": "part1.png", "pivot": [0.5, 0.5], "rotation": 0}],
        draw_order=["part1", "ghost_slot"],
    )

    with pytest.raises(RigError, match="ghost_slot"):
        generate(rig, tmp_path, tmp_path)


def test_part_missing_from_draw_order_raises(tmp_path):
    make_png(tmp_path / "parts" / "part1.png", (10, 10))
    make_png(tmp_path / "parts" / "part2.png", (10, 10))
    rig = base_rig(
        bones=[{"name": "root"}],
        parts=[
            {"slot": "part1", "bone": "root", "image": "part1.png", "pivot": [0.5, 0.5], "rotation": 0},
            {"slot": "part2", "bone": "root", "image": "part2.png", "pivot": [0.5, 0.5], "rotation": 0},
        ],
        draw_order=["part1"],
    )

    with pytest.raises(RigError, match="part2"):
        generate(rig, tmp_path, tmp_path)


def test_scarf_chain_referencing_an_unknown_bone_raises(tmp_path):
    make_png(tmp_path / "parts" / "part1.png", (10, 10))
    rig = base_rig(
        bones=[{"name": "root"}],
        parts=[{"slot": "part1", "bone": "root", "image": "part1.png", "pivot": [0.5, 0.5], "rotation": 0}],
        draw_order=["part1"],
        animations={"idle": {"duration": 1.0, "bones": {}}},
        scarf={"bones": ["ghost"], "trail_deg": {"idle": 0.0}, "flutter_deg": 1.0, "flutter_hz": 1.0, "lag_frames": 0, "gain": [1.0]},
    )

    with pytest.raises(RigError, match="ghost"):
        generate(rig, tmp_path, tmp_path)


def test_authored_keyframe_with_a_curve_is_refused(tmp_path):
    # Bezier `curve` keyframes pack differently for a 1-value timeline (rotate) vs. a
    # 2-value one (translate) in the real 4.x runtime (readCurve's `value << 2` offset);
    # this module doesn't translate them, so it must refuse rather than emit a rig with
    # the wrong bezier shape.
    make_png(tmp_path / "parts" / "arm.png", (20, 60))
    rig = base_rig(
        bones=[{"name": "root"}, {"name": "arm", "parent": "root"}],
        parts=[{"slot": "arm", "bone": "arm", "image": "arm.png", "pivot": [0.5, 1.0], "rotation": 0}],
        draw_order=["arm"],
        animations={
            "wave": {
                "duration": 0.5,
                "bones": {"arm": {"rotate": [{"time": 0, "angle": 0, "curve": [0.25, 0, 0.75, 1]}, {"time": 0.5, "angle": 30}]}},
            }
        },
    )

    with pytest.raises(RigError, match="curve"):
        generate(rig, tmp_path, tmp_path)


def test_authored_unsupported_timeline_type_raises(tmp_path):
    make_png(tmp_path / "parts" / "arm.png", (20, 60))
    rig = base_rig(
        bones=[{"name": "root"}, {"name": "arm", "parent": "root"}],
        parts=[{"slot": "arm", "bone": "arm", "image": "arm.png", "pivot": [0.5, 1.0], "rotation": 0}],
        draw_order=["arm"],
        animations={"wave": {"duration": 0.5, "bones": {"arm": {"scale": [{"time": 0, "x": 1, "y": 1}]}}}},
    )

    with pytest.raises(RigError, match="scale"):
        generate(rig, tmp_path, tmp_path)


# --- every animation appears (Step 2) --------------------------------------------------


def test_every_animation_in_the_rig_appears_in_the_output(tmp_path):
    make_png(tmp_path / "parts" / "part1.png", (10, 10))
    rig = base_rig(
        bones=[{"name": "root"}],
        parts=[{"slot": "part1", "bone": "root", "image": "part1.png", "pivot": [0.5, 0.5], "rotation": 0}],
        draw_order=["part1"],
        animations={
            "idle": {"duration": 1.0, "bones": {}},
            "run": {"duration": 0.6, "bones": {}},
            "jump": {"duration": 0.5, "loop": False, "bones": {}},
            "fall": {"duration": 0.6, "bones": {}},
            "double_jump": {"duration": 0.5, "loop": False, "bones": {}},
            "dash": {"duration": 0.2, "loop": False, "bones": {}},
            "land": {"duration": 0.25, "loop": False, "bones": {}},
        },
    )

    spine, _, _ = generate(rig, tmp_path, tmp_path)

    assert set(spine["animations"]) == {"idle", "run", "jump", "fall", "double_jump", "dash", "land"}


# --- structure vs. the actual Spine 4.3 runtime -----------------------------------------


def test_output_has_the_documented_top_level_keys(tmp_path):
    rig, base = minimal_rig(tmp_path)

    spine, meta, _ = generate(rig, base, base)

    assert set(spine) == {"skeleton", "bones", "slots", "skins", "animations"}
    assert set(spine["skeleton"]) == {"spine", "x", "y", "width", "height", "images"}
    assert spine["skeleton"]["spine"] == "4.3.00"
    assert set(meta) == {"height_px", "feet_y_px", "facing"}
    assert meta["feet_y_px"] == 0
    assert meta["facing"] == "right"


def test_bones_are_emitted_parent_before_child(tmp_path):
    make_png(tmp_path / "parts" / "part1.png", (10, 10))
    rig = base_rig(
        bones=[{"name": "root"}, {"name": "mid", "parent": "root"}, {"name": "tip", "parent": "mid"}],
        parts=[{"slot": "part1", "bone": "tip", "image": "part1.png", "pivot": [0.5, 0.5], "rotation": 0}],
        draw_order=["part1"],
    )

    spine, _, _ = generate(rig, tmp_path, tmp_path)

    positions = {bone["name"]: index for index, bone in enumerate(spine["bones"])}
    for bone in spine["bones"]:
        if "parent" in bone:
            assert positions[bone["parent"]] < positions[bone["name"]]


def test_slot_and_attachment_references_resolve(tmp_path):
    make_png(tmp_path / "parts" / "head.png", (30, 40))
    rig = base_rig(
        bones=[{"name": "root"}],
        parts=[{"slot": "head", "bone": "root", "image": "head.png", "pivot": [0.5, 0.5], "rotation": 0}],
        draw_order=["head"],
    )

    spine, _, _ = generate(rig, tmp_path, tmp_path)

    bone_names = {bone["name"] for bone in spine["bones"]}
    for slot in spine["slots"]:
        assert slot["bone"] in bone_names
        attachments_for_slot = spine["skins"][0]["attachments"][slot["name"]]
        assert slot["attachment"] in attachments_for_slot
        # `path` names the actual part image, so a Spine import resolves it regardless of slot name.
        assert attachments_for_slot[slot["attachment"]]["path"] == "head"


def test_animation_timelines_are_shaped_as_ascending_keyframe_lists(tmp_path):
    # Input uses this schema's `angle` name for a rotate keyframe; the 4.3 runtime itself
    # reads `value` (SkeletonJson.ts's `readTimeline1`, see generate.py's module
    # docstring) -- `generate` must translate it, not pass `angle` through.
    make_png(tmp_path / "parts" / "arm.png", (20, 60))
    rig = base_rig(
        bones=[{"name": "root"}, {"name": "arm", "parent": "root"}],
        parts=[{"slot": "arm", "bone": "arm", "image": "arm.png", "pivot": [0.5, 1.0], "rotation": 0}],
        draw_order=["arm"],
        animations={
            "wave": {
                "duration": 0.5,
                "bones": {"arm": {"rotate": [{"time": 0, "angle": 0}, {"time": 0.25, "angle": 30}, {"time": 0.5, "angle": 0}]}},
            }
        },
    )

    spine, _, _ = generate(rig, tmp_path, tmp_path)

    timeline = spine["animations"]["wave"]["bones"]["arm"]["rotate"]
    times = [key["time"] for key in timeline]
    assert times == sorted(times)
    for key in timeline:
        assert set(key) == {"time", "value"}
    assert timeline[1]["value"] == 30


def test_images_path_matches_the_planned_rig_src_parts_layout(tmp_path):
    # docs/superpowers/plans/2026-09-27-phase-1-bake-off.md's Task 5 layout: rig.json and
    # the generated output live in `rig-src/`, sibling to `parts/`.
    protagonist = tmp_path / "protagonist"
    make_png(protagonist / "parts" / "part1.png", (10, 10))
    rig_dir = protagonist / "rig-src"
    rig = base_rig(
        bones=[{"name": "root"}],
        parts=[{"slot": "part1", "bone": "root", "image": "part1.png", "pivot": [0.5, 0.5], "rotation": 0}],
        draw_order=["part1"],
        parts_dir="../parts",
    )
    rig_dir.mkdir()

    spine, _, _ = generate(rig, rig_dir, rig_dir)

    assert spine["skeleton"]["images"] == "../parts/"


def test_images_path_is_computed_for_a_different_layout(tmp_path):
    # Proves the path isn't a hardcoded "../parts/": a deeper --out directory gets a
    # correspondingly deeper relative path back to the same parts_dir.
    make_png(tmp_path / "parts" / "part1.png", (10, 10))
    rig = base_rig(
        bones=[{"name": "root"}],
        parts=[{"slot": "part1", "bone": "root", "image": "part1.png", "pivot": [0.5, 0.5], "rotation": 0}],
        draw_order=["part1"],
        parts_dir="parts",
    )
    out_dir = tmp_path / "build" / "nested"

    spine, _, _ = generate(rig, tmp_path, out_dir)

    assert spine["skeleton"]["images"] == "../../parts/"


# --- CLI --------------------------------------------------------------------------------


def test_cli_generate_writes_out_and_meta(tmp_path):
    rig, base = minimal_rig(tmp_path)
    rig_path = base / "rig.json"
    rig_path.write_text(json.dumps(rig))
    out_path = base / "out" / "violet.generated.json"

    code = main(["generate", str(rig_path), "--out", str(out_path)])

    assert code == 0
    spine = json.loads(out_path.read_text())
    assert spine["skeleton"]["spine"] == "4.3.00"
    assert spine["skeleton"]["images"] == "../parts/"
    meta_path = out_path.parent / "violet.generated.meta.json"
    meta = json.loads(meta_path.read_text())
    assert meta["facing"] == "right"


def test_cli_print_parts(tmp_path, capsys):
    rig, base = minimal_rig(tmp_path)
    rig_path = base / "rig.json"
    rig_path.write_text(json.dumps(rig))
    out_path = base / "out.json"

    code = main(["generate", str(rig_path), "--out", str(out_path), "--print-parts"])

    assert code == 0
    output = capsys.readouterr().out
    assert "part1: part1.png 64x64" in output


def test_cli_reports_rig_errors_without_writing_output(tmp_path, capsys):
    rig = base_rig(
        bones=[{"name": "root"}],
        parts=[{"slot": "part1", "bone": "root", "image": "missing.png", "pivot": [0.5, 0.5], "rotation": 0}],
        draw_order=["part1"],
    )
    rig_path = tmp_path / "rig.json"
    rig_path.write_text(json.dumps(rig))
    out_path = tmp_path / "out.json"

    code = main(["generate", str(rig_path), "--out", str(out_path)])

    assert code == 1
    assert "missing.png" in capsys.readouterr().err
    assert not out_path.exists()
