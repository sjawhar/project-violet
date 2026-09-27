import json
import os
from pathlib import Path

import pytest

from conftest import probe, probe_audio
from preview.publish import pages_problem, snippet

FAST_TURNTABLE = ["--turntable-size", "64", "--turntable-samples", "1", "--turntable-fps", "8"]


def _manifest(workdir: Path, pr: str) -> dict:
    return json.loads((workdir / f"out/review/pr-{pr}/preview.json").read_text())


def _item(manifest: dict, name: str) -> dict:
    [item] = [item for item in manifest["items"] if item["name"] == name]
    return item


def test_builds_a_gallery_with_every_kind_of_asset(workdir: Path, run, assets: dict[str, Path]):
    code, _, err = run("build", "7", *FAST_TURNTABLE, *(str(p) for p in assets.values()))

    assert code == 0, err
    out = workdir / "out/review/pr-7"
    manifest = _manifest(workdir, "7")
    assert {item["name"]: item["kind"] for item in manifest["items"]} == {
        "scarf.png": "image", "sky.jpg": "image", "walk": "animation", "intro.mp4": "animation",
        "chime.wav": "audio", "lantern.glb": "model",
    }

    sheet = probe(out / manifest["contact_sheet"])
    assert sheet["frames"] == 1 and sheet["width"] > 0

    scarf = probe(out / _item(manifest, "scarf.png")["media"]["image"])
    assert (scarf["width"], scarf["height"]) == (800, 600)
    sky = probe(out / _item(manifest, "sky.jpg")["media"]["image"])
    assert (sky["width"], sky["height"]) == (1600, 800)

    walk = _item(manifest, "walk")["media"]
    assert probe(out / walk["gif"])["frames"] == 6
    assert probe(out / walk["video"])["frames"] == 6
    intro = _item(manifest, "intro.mp4")["media"]
    assert probe(out / intro["gif"])["frames"] > 1
    assert probe(out / intro["video"])["frames"] == 12

    chime = _item(manifest, "chime.wav")["media"]
    assert probe_audio(out / chime["audio"]) == pytest.approx(1.0, abs=0.05)
    assert probe(out / chime["waveform"])["frames"] == 1

    lantern = _item(manifest, "lantern.glb")["media"]
    turntable = probe(out / lantern["video"])
    assert turntable["duration"] == pytest.approx(6.0, abs=0.2)
    assert turntable["frames"] == 48
    assert probe(out / lantern["gif"])["frames"] > 1

    html = (out / "index.html").read_text()
    for text in ("openai", "gpt-image-2", "a violet &lt;scarf&gt; &amp; a lantern", "Sami Jawhar"):
        assert text in html
    assert "<scarf>" not in html
    for item in manifest["items"]:
        for path in item["media"].values():
            assert path in html


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


def test_a_failed_rebuild_keeps_the_previous_gallery(workdir: Path, run, assets: dict[str, Path]):
    assert run("build", "9", str(assets["scarf"]))[0] == 0
    before = (workdir / "out/review/pr-9/preview.json").read_text()
    broken = workdir / "broken.png"
    broken.write_bytes(os.urandom(512))

    assert run("build", "9", str(assets["scarf"]), str(broken))[0] != 0

    assert (workdir / "out/review/pr-9/preview.json").read_text() == before


def test_fails_naming_a_malformed_provenance_record(workdir: Path, run, assets: dict[str, Path]):
    image = workdir / "odd.png"
    image.write_bytes(assets["scarf"].read_bytes())
    (workdir / "odd.png.provenance.json").write_text("{not json")

    code, _, err = run("build", "8", str(image))

    assert code != 0
    assert "odd.png.provenance.json" in err


def test_publish_refuses_a_pr_without_a_complete_build(workdir: Path, run):
    code, _, err = run("publish", "10")

    assert code != 0
    assert "preview build 10" in err


@pytest.mark.parametrize(
    ("pages", "ok"),
    [
        ({"build_type": "legacy", "source": {"branch": "gh-pages", "path": "/"}}, True),
        ({"build_type": "legacy", "source": {"branch": "master", "path": "/"}}, False),
        ({"build_type": "legacy", "source": {"branch": "gh-pages", "path": "/docs"}}, False),
        ({"build_type": "workflow", "source": {"branch": "gh-pages", "path": "/"}}, False),
        (None, False),
    ],
)
def test_pages_must_serve_the_gh_pages_root(pages, ok: bool):
    problem = pages_problem(pages)

    assert (problem is None) == ok
    if not ok:
        assert "gh-pages" in problem


def test_snippet_links_the_gallery_and_inlines_the_thumbnails():
    manifest = {
        "pr": "7",
        "contact_sheet": "contact-sheet.png",
        "items": [
            {"name": "walk", "kind": "animation", "media": {"gif": "items/02-walk.gif", "video": "items/02-walk.mp4"}},
            {"name": "chime.wav", "kind": "audio", "media": {"audio": "items/03-chime.wav", "waveform": "items/03-chime.waveform.png"}},
            {"name": "lantern.glb", "kind": "model", "media": {"gif": "items/04-lantern.gif", "video": "items/04-lantern.mp4"}},
        ],
    }

    text = snippet(manifest, "sjawhar/project-violet")

    raw = "https://raw.githubusercontent.com/sjawhar/project-violet/gh-pages/review/pr-7/"
    assert "https://sjawhar.github.io/project-violet/review/pr-7/" in text
    for path in ("contact-sheet.png", "items/02-walk.gif", "items/03-chime.waveform.png", "items/04-lantern.gif"):
        assert f"({raw}{path})" in text
    assert ".mp4)" not in text and ".wav)" not in text
