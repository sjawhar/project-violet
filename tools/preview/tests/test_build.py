import json
import os
import shutil
from pathlib import Path

import pytest

from conftest import generated_record, probe, probe_audio, sh, sha256, write_record
from preview.cli import frames_in
from preview.media import PreviewError, run as run_tool
from preview.publish import pages_problem, snippet

FAST = ["--turntable-size", "64", "--turntable-samples", "1", "--turntable-fps", "8", "--render-device", "cpu"]


def _manifest(workdir: Path, pr: str) -> dict:
    return json.loads((workdir / f"out/review/pr-{pr}/preview.json").read_text())


def _item(manifest: dict, name: str) -> dict:
    [item] = [item for item in manifest["items"] if item["name"] == name]
    return item


def test_builds_a_gallery_with_every_kind_of_asset(workdir: Path, run, assets: dict[str, Path]):
    code, _, err = run("build", "7", *FAST, *(str(p) for p in assets.values()))

    assert code == 0, err
    out = workdir / "out/review/pr-7"
    manifest = _manifest(workdir, "7")
    assert {item["name"]: item["kind"] for item in manifest["items"]} == {
        "scarf.png": "image", "sky.jpg": "image", "walk": "animation", "intro.mp4": "animation",
        "chime.wav": "audio", "lantern.glb": "model",
    }
    assert _item(manifest, "scarf.png")["sha256"] == sha256(assets["scarf"])

    sheet = probe(out / manifest["contact_sheet"])
    assert (sheet["frames"], sheet["width"]) == (1, 2 * (320 + 2 * 8))  # both images, one 336px tile each

    scarf = probe(out / _item(manifest, "scarf.png")["media"]["image"])
    assert (scarf["width"], scarf["height"]) == (800, 600)
    sky = probe(out / _item(manifest, "sky.jpg")["media"]["image"])
    assert (sky["width"], sky["height"]) == (1600, 800)

    walk = _item(manifest, "walk")["media"]
    assert probe(out / walk["gif"])["frames"] == 6
    assert probe(out / walk["video"])["frames"] == 6
    for name in ("walk", "intro.mp4", "lantern.glb"):
        poster = probe(out / _item(manifest, name)["media"]["poster"])
        assert poster["frames"] == 1 and poster["codec"] == "webp"
    intro = probe(out / _item(manifest, "intro.mp4")["media"]["video"])
    assert (intro["codec"], intro["pix_fmt"], intro["frames"]) == ("h264", "yuv420p", 12)
    assert probe(out / _item(manifest, "intro.mp4")["media"]["gif"])["frames"] == 10  # 1 s at the 10 fps GIF rate

    codec, duration = probe_audio(out / _item(manifest, "chime.wav")["media"]["audio"])
    assert codec == "aac" and duration == pytest.approx(1.0, abs=0.1)
    assert probe(out / _item(manifest, "chime.wav")["media"]["waveform"])["frames"] == 1

    lantern = _item(manifest, "lantern.glb")["media"]
    turntable = probe(out / lantern["video"])
    assert turntable["duration"] == pytest.approx(6.0, abs=0.2)
    assert (turntable["frames"], turntable["width"], turntable["height"]) == (48, 64, 64)
    assert probe(out / lantern["gif"])["frames"] == 48  # 8 fps is under the GIF cap, so every frame stays

    html = (out / "index.html").read_text()
    for text in ("openai", "gpt-image-2", "a violet &lt;scarf&gt; &amp; a lantern", "Sami Jawhar", "proprietary"):
        assert text in html
    assert "<scarf>" not in html
    for item in manifest["items"]:
        for path in item["media"].values():
            assert path in html
    assert manifest["contact_sheet"] in html
    assert "No provenance record." in html  # the frame sequence has none


def test_writes_to_the_repository_root_from_a_subdirectory(workdir: Path, run, assets: dict[str, Path], monkeypatch):
    (workdir / "tools").mkdir()
    monkeypatch.chdir(workdir / "tools")

    assert run("build", "7", str(assets["scarf"]))[0] == 0

    assert (workdir / "out/review/pr-7/index.html").exists()
    assert not (workdir / "tools/out").exists()


def test_a_frame_sequence_keeps_every_frame_whatever_each_file_s_pixel_format(workdir: Path, run):
    frames = workdir / "mixed"
    frames.mkdir()
    sh("magick", "-size", "64x64", "xc:black", "-type", "bilevel", str(frames / "f1.png"))
    sh("magick", "-size", "64x64", "xc:red", str(frames / "f2.png"))
    sh("magick", "-size", "64x64", "xc:red", "-fill", "blue", "-draw", "circle 32,32 40,32", "-depth", "16", str(frames / "f3.png"))
    sh("magick", "-size", "64x64", "xc:#00ff0080", str(frames / "f4.png"))

    code, _, err = run("build", "3", str(frames))

    assert code == 0, err
    walk = _item(_manifest(workdir, "3"), "mixed")["media"]
    assert probe(workdir / "out/review/pr-3" / walk["gif"])["frames"] == 4
    assert probe(workdir / "out/review/pr-3" / walk["video"])["frames"] == 4


def test_refuses_a_frame_sequence_whose_frames_differ_in_size(workdir: Path, run):
    frames = workdir / "ragged"
    frames.mkdir()
    sh("magick", "-size", "64x64", "xc:red", str(frames / "f1.png"))
    sh("magick", "-size", "128x96", "xc:red", str(frames / "f2.png"))

    code, _, err = run("build", "3", str(frames))

    assert code != 0
    assert "ragged" in err and "128x96" in err


def test_orders_frames_by_their_numbers(tmp_path: Path):
    for name in ("walk10.png", "walk2.png", "walk1.png", "notes.txt"):
        (tmp_path / name).write_bytes(b"")

    assert [p.name for p in frames_in(tmp_path)] == ["walk1.png", "walk2.png", "walk10.png"]


def test_converts_odd_sized_video_and_gif_to_playable_mp4(workdir: Path, run):
    clip = workdir / "odd.webm"
    sh("ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=641x481:rate=10:duration=1", "-c:v", "libvpx-vp9", str(clip))
    gif = workdir / "odd.gif"
    sh("ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=99x75:rate=10:duration=1", str(gif))

    code, _, err = run("build", "4", str(clip), str(gif))

    assert code == 0, err
    manifest = _manifest(workdir, "4")
    for name, size in (("odd.webm", (640, 480)), ("odd.gif", (98, 74))):
        video = probe(workdir / "out/review/pr-4" / _item(manifest, name)["media"]["video"])
        assert (video["codec"], video["pix_fmt"], video["frames"], (video["width"], video["height"])) == ("h264", "yuv420p", 10, size)
    assert probe(workdir / "out/review/pr-4" / _item(manifest, "odd.webm")["media"]["gif"])["width"] == 360
    assert probe(workdir / "out/review/pr-4" / _item(manifest, "odd.gif")["media"]["gif"])["frames"] == 10


def test_shows_stale_and_missing_records_without_failing(workdir: Path, run, assets: dict[str, Path]):
    stale = workdir / "stale.png"
    shutil.copyfile(assets["scarf"], stale)
    write_record(stale, generated_record(stale, provider="openai", model="gpt-image-2", prompt="old prompt"))
    sh("magick", str(stale), "-negate", str(stale))
    bare = workdir / "bare.png"
    shutil.copyfile(assets["scarf"], bare)

    code, _, err = run("build", "5", str(stale), str(bare))

    assert code == 0, err
    manifest = _manifest(workdir, "5")
    assert _item(manifest, "stale.png")["provenance"]["status"] == "stale"
    assert _item(manifest, "bare.png")["provenance"]["status"] == "missing"
    assert _item(manifest, "bare.png")["provenance"]["problems"] == []  # "No provenance record." says it once
    html = (workdir / "out/review/pr-5/index.html").read_text()
    assert "sha256 mismatch" in html
    assert "No provenance record" in html


def test_fails_naming_an_invalid_provenance_record(workdir: Path, run, assets: dict[str, Path]):
    image = workdir / "odd.png"
    shutil.copyfile(assets["scarf"], image)
    record = generated_record(image, provider="openai", model="gpt-image-2", prompt="p")
    del record["license"]
    write_record(image, record)

    code, _, err = run("build", "8", str(image))

    assert code != 0
    assert "odd.png.provenance.json" in err and "license" in err
    assert not (workdir / "out/review/pr-8").exists()


def test_refuses_a_git_lfs_pointer_in_place_of_the_asset(workdir: Path, run):
    pointer = workdir / "hero.png"
    pointer.write_bytes(b"version https://git-lfs.github.com/spec/v1\noid sha256:" + b"a" * 64 + b"\nsize 1234\n")

    code, _, err = run("build", "8", str(pointer))

    assert code != 0
    assert "hero.png" in err and "git lfs pull" in err


def test_fails_naming_an_unsupported_file_and_writes_nothing(workdir: Path, run, assets: dict[str, Path]):
    notes = workdir / "notes.txt"
    notes.write_text("not an asset")

    code, _, err = run("build", "8", str(assets["scarf"]), str(notes))

    assert code != 0
    assert "notes.txt" in err
    assert not (workdir / "out/review/pr-8").exists()


def test_fails_naming_a_corrupt_asset_and_writes_nothing(workdir: Path, run):
    broken = workdir / "broken.png"
    broken.write_bytes(os.urandom(512))

    code, _, err = run("build", "8", str(broken))

    assert code != 0
    assert "broken.png" in err
    assert not (workdir / "out/review/pr-8").exists()


def test_a_failed_rebuild_keeps_the_previous_gallery_and_clears_old_scratch(workdir: Path, run, assets: dict[str, Path]):
    assert run("build", "9", str(assets["scarf"]))[0] == 0
    before = (workdir / "out/review/pr-9/preview.json").read_text()
    (workdir / "out/review/.pr-9-left-by-a-killed-build").mkdir()
    broken = workdir / "broken.png"
    broken.write_bytes(os.urandom(512))

    assert run("build", "9", str(assets["scarf"]), str(broken))[0] != 0

    assert (workdir / "out/review/pr-9/preview.json").read_text() == before
    assert [p.name for p in (workdir / "out/review").iterdir()] == ["pr-9"]


def test_renders_a_blend_file_regardless_of_its_saved_settings(workdir: Path, run):
    blend = workdir / "prop.blend"
    sh("blender", "-b", "--factory-startup", "--python-exit-code", "1", "--python-expr",
       "import bpy; bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.mesh.primitive_cube_add(); "
       "s = bpy.context.scene; s.frame_step = 2; s.render.resolution_percentage = 25; "
       "big = bpy.data.collections.new('excluded'); s.collection.children.link(big); "
       "bpy.ops.mesh.primitive_cube_add(size=200); o = bpy.context.object; s.collection.objects.unlink(o); big.objects.link(o); "
       "bpy.context.view_layer.layer_collection.children['excluded'].exclude = True; "
       f"bpy.ops.wm.save_as_mainfile(filepath={str(blend)!r})")

    code, _, err = run("build", "6", *FAST, str(blend))

    assert code == 0, err
    video = probe(workdir / "out/review/pr-6" / _item(_manifest(workdir, "6"), "prop.blend")["media"]["video"])
    assert (video["frames"], video["width"], video["height"]) == (48, 64, 64)


def test_a_tool_that_hangs_is_stopped_with_an_error_naming_the_asset(tmp_path: Path):
    with pytest.raises(PreviewError, match=r"slow\.png.*did not finish within 1s"):
        run_tool(tmp_path / "slow.png", "sleep", "30", timeout=1)


def test_publish_refuses_a_pr_without_a_complete_build(workdir: Path, run):
    (workdir / "out/review/pr-10/items").mkdir(parents=True)  # a build that never wrote preview.json

    code, _, err = run("publish", "10")

    assert code != 0
    assert "pr-10" in err


@pytest.mark.parametrize(
    ("pages", "wrong"),
    [
        ({"build_type": "legacy", "source": {"branch": "gh-pages", "path": "/"}}, None),
        ({"build_type": "legacy", "source": {"branch": "master", "path": "/"}}, "master:/"),
        ({"build_type": "legacy", "source": {"branch": "gh-pages", "path": "/docs"}}, "gh-pages:/docs"),
        ({"build_type": "workflow", "source": {"branch": "gh-pages", "path": "/"}}, "'workflow'"),
        (None, "not enabled"),
    ],
)
def test_pages_must_serve_the_gh_pages_root(pages, wrong: str | None):
    problem = pages_problem(pages)

    if wrong is None:
        assert problem is None
    else:
        assert wrong in problem  # names the setting that is wrong, not just that something is


def test_snippet_links_the_gallery_and_pins_thumbnails_to_the_published_commit():
    manifest = {
        "pr": "7",
        "contact_sheet": "contact-sheet.png",
        "items": [
            {"name": "walk](http://evil.example) x", "kind": "animation", "media": {"gif": "items/02-walk.gif", "video": "items/02-walk.mp4"}},
            {"name": "chime.wav", "kind": "audio", "media": {"audio": "items/03-chime.m4a", "waveform": "items/03-chime.waveform.png"}},
            {"name": "lantern.glb", "kind": "model", "media": {"gif": "items/04-lantern.gif", "video": "items/04-lantern.mp4"}},
        ],
    }

    text = snippet(manifest, "sjawhar/project-violet", "0123456789abcdef0123456789abcdef01234567")

    raw = "https://raw.githubusercontent.com/sjawhar/project-violet/0123456789abcdef0123456789abcdef01234567/review/pr-7/"
    assert "https://sjawhar.github.io/project-violet/review/pr-7/" in text
    for path in ("contact-sheet.png", "items/02-walk.gif", "items/03-chime.waveform.png", "items/04-lantern.gif"):
        assert f"({raw}{path})" in text
    assert ".mp4)" not in text and ".m4a)" not in text
    assert "(http://evil.example)" not in text


def test_publish_checks_pages_before_pushing_anything(workdir: Path, run, assets: dict[str, Path], tmp_path_factory, monkeypatch):
    fake = tmp_path_factory.mktemp("fake-gh")
    (fake / "gh").write_text(
        "#!/bin/sh\n"
        'case "$1" in\n'
        '  repo) echo sjawhar/project-violet ;;\n'
        '  api) echo \'{"build_type": "legacy", "source": {"branch": "master", "path": "/"}}\' ;;\n'
        "esac\n"
    )
    (fake / "gh").chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake}:{os.environ['PATH']}")
    assert run("build", "11", str(assets["scarf"]))[0] == 0

    code, out, err = run("publish", "11")

    assert code != 0
    assert "master:/" in err
    assert out == ""  # no snippet, so nothing was published


def test_refuses_a_frame_sequence_that_mixes_file_types(workdir: Path, run):
    frames = workdir / "mixed-types"
    frames.mkdir()
    sh("magick", "-size", "32x32", "xc:red", str(frames / "f1.png"))
    sh("magick", "-size", "32x32", "xc:red", str(frames / "f2.jpg"))

    code, _, err = run("build", "3", str(frames))

    assert code != 0
    assert "mixed-types" in err and ".jpg" in err


@pytest.mark.parametrize("pr", ["../escape", "7/..", "PR7", ""])
def test_rejects_a_pr_name_that_could_leave_the_gallery_directory(workdir: Path, run, assets: dict[str, Path], pr: str):
    with pytest.raises(SystemExit):
        run("build", pr, str(assets["scarf"]))
