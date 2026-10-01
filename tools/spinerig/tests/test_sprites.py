"""violet-sprites v1 (docs/bakeoff/character-rig.md, "Painted sprite sequences"): the
generated file must place every painted frame exactly where shoot_b.py's reference
compositor does, and generation must refuse inputs it cannot place honestly.

shoot_b.py is imported here only as the oracle; spinerig.sprites never imports it."""

from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

import pytest
from PIL import Image

from spinerig import render as R
from spinerig.sprites import SpritesError, build_sprites, frame_index_at, render_frame

ROOT = Path(__file__).resolve().parents[3]
PROTAGONIST = ROOT / "assets/bakeoff/protagonist"
GLOWUP = PROTAGONIST / "glow-up"
FRAMES = GLOWUP / "trial-b/frames"
SOURCE = PROTAGONIST / "sprites-src/sprites.json"
SPRITES = PROTAGONIST / "sprites/violet.sprites.json"

FRAME_COUNTS = {"idle": 8, "run": 8, "jump": 5, "fall": 5, "double_jump": 5, "dash": 6, "land": 6}
DURATIONS = {"idle": 1.0, "run": 0.6, "jump": 0.5, "fall": 0.6, "double_jump": 0.5, "dash": 0.2, "land": 0.25}


@pytest.fixture(scope="module")
def sprites() -> dict:
    return json.loads(SPRITES.read_text())


@pytest.fixture
def oracle(monkeypatch):
    monkeypatch.syspath_prepend(str(GLOWUP))
    return importlib.import_module("shoot_b")


def test_committed_file_is_what_the_source_generates(sprites):
    assert build_sprites(SOURCE, SPRITES) == sprites


def test_animations_frames_durations_and_loops(sprites):
    animations = sprites["animations"]
    assert {name: len(a["frames"]) for name, a in animations.items()} == FRAME_COUNTS
    assert {name: a["duration"] for name, a in animations.items()} == DURATIONS
    assert {name for name, a in animations.items() if a["loop"]} == {"idle", "run"}
    for name, animation in animations.items():
        for index, frame in enumerate(animation["frames"]):
            for layer in ("body", "scarf"):
                assert frame[layer]["image"] == f"../glow-up/trial-b/frames/{name}-{layer}-{index:02d}.png"


class _Cell:
    def __init__(self):
        self.pastes = []

    def paste(self, image, position, mask=None):
        self.pastes.append((image, position))


def test_every_frame_lands_where_shoot_b_pastes_it(sprites, oracle, monkeypatch):
    """At shoot_b's contact-sheet cell and scale, placing each layer's anchor on the root
    gives render_cell_b's own integer paste positions, for all 43 frames, both layers."""
    shoot = oracle.A
    scale = shoot.SCALE
    cell_w, cell_h = R.canvas_size(shoot.REFERENCE_BOX, scale, shoot.MARGIN)
    root = (oracle.HEAD_X_FRACTION * cell_w, oracle.GROUND_Y_FRACTION * cell_h)
    cell = _Cell()
    monkeypatch.setattr(oracle, "Image", type("Image", (), {"new": staticmethod(lambda *a, **k: cell)}))

    compared = 0
    for name, animation in sprites["animations"].items():
        record = oracle.load_record(name)
        assert oracle.frame_count(name) == len(animation["frames"])
        for index, frame in enumerate(animation["frames"]):
            cache = {(name, index, layer, scale): layer for layer in ("body", "scarf")}
            cell.pastes.clear()
            oracle.render_cell_b(name, index, record, scale, cell_w, cell_h, cache)
            ours = [(layer, (round(root[0] - frame[layer]["anchor"][0] * scale), round(root[1] - frame[layer]["anchor"][1] * scale))) for layer in ("body", "scarf")]
            assert cell.pastes == ours, f"{name} frame {index}"
            compared += 1
    assert compared == sum(FRAME_COUNTS.values())


def test_frame_index_matches_shoot_b_off_frame_boundaries(sprites, oracle):
    """Within a frame, `min(floor(t * n / duration), n - 1)` agrees with shoot_b's
    `int(t / (duration / n))`. Exactly on a boundary the two can differ by float
    rounding (jump at t = 0.3: 0.3 / 0.1 is 2.999...); there the format shows the frame
    that starts at t, which is what the formula says."""
    on_boundary = 0
    for name, animation in sprites["animations"].items():
        duration, count = animation["duration"], len(animation["frames"])
        gif_ticks = [i / oracle.A.GIF_FPS for i in range(max(1, round(duration * oracle.A.GIF_FPS)))]
        for t in gif_ticks + oracle.A.sample_times(name, duration):
            ours = frame_index_at(t, duration, count, animation["loop"])
            position = t * count / duration
            if abs(position - round(position)) < 1e-9:
                on_boundary += 1
                assert ours == min(round(position), count - 1), f"{name} t={t}"
            else:
                assert ours == oracle.frame_index_at(t, duration, count), f"{name} t={t}"
    assert on_boundary > 0


@pytest.mark.parametrize(
    ("t", "looping", "held"),
    [
        (0.0, 0, 0),  # start
        (0.35, 2, 3),  # mid-frame: 2.8 frames into idle, 3.5 into jump
        (0.25, 2, 2),  # exactly on idle's 2/8 boundary
        (0.1, 0, 1),  # exactly on jump's 1/5 boundary
        (0.5, 4, 4),  # jump's end: held on its last frame
        (1.0, 0, 4),  # idle's end wraps to its first frame
        (1.25, 2, 4),  # past the end: idle wraps, jump holds
    ],
)
def test_frame_index_at_loops_and_holds(t, looping, held):
    assert frame_index_at(t, 1.0, 8, True) == looping
    assert frame_index_at(t, 0.5, 5, False) == held


def test_height_is_idle_frame_0_sole_to_top(sprites):
    record = json.loads((FRAMES / "idle-finalize-record.json").read_text())["0"]
    with Image.open(FRAMES / "idle-body-00.png") as body:
        top = body.convert("RGBA").getchannel("A").getbbox()[1]
    assert sprites["height_px"] == record["sole_y"] - top == 1072.0


def test_scarf_is_drawn_over_the_body(sprites, tmp_path):
    """render_frame, the reference reader: at the review scale idle frame 0's scarf
    covers the body where they overlap."""
    frame = sprites["animations"]["idle"]["frames"][0]
    tint = (255, 0, 0)
    image = render_frame(sprites, SPRITES.parent, "idle", 0.0, scale=0.22, root=(135.0, 306.0), size=(290, 316), tint=tint)
    with Image.open(FRAMES / "idle-scarf-00.png") as scarf:
        scarf = scarf.convert("RGBA").resize((round(scarf.width * 0.22), round(scarf.height * 0.22)), Image.LANCZOS)
    left = round(135.0 - frame["scarf"]["anchor"][0] * 0.22)
    top = round(306.0 - frame["scarf"]["anchor"][1] * 0.22)
    x, y = next((x, y) for y in range(scarf.height) for x in range(scarf.width) if scarf.getpixel((x, y))[3] == 255 and scarf.getpixel((x, y))[0] > 60)
    r, g, b, _ = image.getpixel((left + x, top + y))
    assert r > 0 and g == 0 and b == 0, "the tinted scarf is not on top"


def _two_layer_file(tmp_path, body_rgba, scarf_rgba, *, size=(2, 2)) -> dict:
    """A one-frame violet-sprites file whose layers are flat `size` images, both
    anchored at their top-left pixel."""
    for layer, rgba in (("body", body_rgba), ("scarf", scarf_rgba)):
        Image.new("RGBA", size, rgba).save(tmp_path / f"{layer}.png")
    frame = {layer: {"image": f"{layer}.png", "anchor": [0.0, 0.0]} for layer in ("body", "scarf")}
    return {"animations": {"idle": {"duration": 1.0, "loop": True, "frames": [frame]}}}


def _over(src, dst):
    """Exact source-over, straight (non-premultiplied) alpha, 0-255 channels."""
    sa, da = src[3] / 255, dst[3] / 255
    out_a = sa + da * (1 - sa)
    rgb = [(s * sa + d * da * (1 - sa)) / out_a for s, d in zip(src[:3], dst[:3])]
    return (*rgb, out_a * 255)


def _close(actual, expected):
    return all(abs(a - e) <= 1 for a, e in zip(actual, expected))


def test_translucent_layers_keep_their_alpha_on_a_transparent_canvas(tmp_path):
    """Lanes draw source-over onto whatever is behind the character, so the reference
    reader's transparent output must carry each translucent pixel's own RGBA."""
    body = (200, 100, 50, 128)
    alone = render_frame(_two_layer_file(tmp_path, body, (0, 0, 0, 0)), tmp_path, "idle", 0.0, scale=1.0, root=(1.0, 1.0), size=(4, 4))
    assert alone.getpixel((1, 1)) == body

    scarf = (60, 60, 60, 128)
    stacked = render_frame(_two_layer_file(tmp_path, body, scarf), tmp_path, "idle", 0.0, scale=1.0, root=(1.0, 1.0), size=(4, 4))
    assert _close(stacked.getpixel((1, 1)), _over(scarf, body)), stacked.getpixel((1, 1))


def test_translucent_layers_blend_opaque_over_an_opaque_background_even_off_canvas(tmp_path):
    """Over an opaque background the result is opaque and source-over blended, including
    for a layer that starts left of and above the canvas."""
    body, scarf, gray = (200, 100, 50, 128), (60, 60, 60, 128), (128, 128, 128, 255)
    sprites = _two_layer_file(tmp_path, body, scarf, size=(3, 3))
    image = render_frame(sprites, tmp_path, "idle", 0.0, scale=1.0, root=(-1.0, -1.0), size=(4, 4), background=gray)
    expected = _over(scarf, _over(body, gray))
    for xy in ((0, 0), (1, 1)):
        assert image.getpixel(xy)[3] == 255 and _close(image.getpixel(xy), expected), image.getpixel(xy)
    assert image.getpixel((2, 2)) == gray


# --- refusals: each runs the real inputs through a copy of the frames directory -------


@pytest.fixture
def inputs(tmp_path):
    """A source file whose frames directory is a tmp copy (symlinks) of the live frames,
    so a test can change one input without touching the repo."""
    frames = tmp_path / "frames"
    frames.mkdir()
    for path in FRAMES.iterdir():
        (frames / path.name).symlink_to(path)
    pins = tmp_path / "scarf_attachments.json"
    pins.write_text((GLOWUP / "scarf_attachments.json").read_text())
    source = json.loads(SOURCE.read_text())
    source["rig"] = str(SOURCE.parent / source["rig"])
    source["frames_dir"] = str(frames)
    source["scarf_attachments"] = str(pins)
    source_path = tmp_path / "sprites.json"

    def write(edit=None):
        if edit:
            edit(source)
        source_path.write_text(json.dumps(source))
        return source_path

    return frames, pins, write


def _replace(frames: Path, name: str, edit) -> Path:
    path = frames / name
    with Image.open(path.resolve()) as image:
        changed = edit(image.convert("RGBA"))
    path.unlink()
    changed.save(path)
    return path


def test_untouched_copy_builds(inputs, tmp_path):
    _, _, write = inputs
    assert len(build_sprites(write(), tmp_path / "out.json")["animations"]) == 7


def test_refuses_a_stale_scarf_binding(inputs, tmp_path):
    frames, _, write = inputs

    def nudge(image):
        image.putpixel((0, 0), (1, 2, 3, 255))
        return image

    _replace(frames, "idle-body-03.png", nudge)
    with pytest.raises(SpritesError, match=r"idle-body-03\.png: pixels changed"):
        build_sprites(write(), tmp_path / "out.json")


def test_refuses_a_colored_scarf(inputs, tmp_path):
    frames, pins, write = inputs

    def redden(image):
        red = Image.new("RGBA", image.size, (200, 40, 40, 255))
        red.putalpha(image.getchannel("A"))
        return red

    path = _replace(frames, "run-scarf-02.png", redden)
    # Rebind the new bytes so the color check, not the hash check, is what refuses it.
    data = json.loads(pins.read_text())
    pin = next(p for p in data["frames"] if (p["animation"], p["index"]) == ("run", 2))
    pin["scarf_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    pins.write_text(json.dumps(data))
    with pytest.raises(SpritesError, match=r"run-scarf-02\.png: scarf layer is colored"):
        build_sprites(write(), tmp_path / "out.json")


def test_refuses_a_missing_frame(inputs, tmp_path):
    frames, _, write = inputs
    (frames / "jump-scarf-04.png").unlink()
    with pytest.raises(SpritesError, match=r"jump-scarf-04\.png: missing"):
        build_sprites(write(), tmp_path / "out.json")


def test_refuses_an_unknown_animation(inputs, tmp_path):
    _, _, write = inputs

    def add_wave(source):
        source["animations"]["wave"] = {"record": "wave-finalize-record.json", "loop": False}

    with pytest.raises(SpritesError, match=r"violet\.json: no animation 'wave'"):
        build_sprites(write(add_wave), tmp_path / "out.json")


def test_render_refuses_an_unknown_animation(sprites):
    with pytest.raises(SpritesError, match=r"sprites: violet-sprites file has no animation 'wave'"):
        render_frame(sprites, SPRITES.parent, "wave", 0.0, scale=1.0, root=(0.0, 0.0), size=(1, 1))
