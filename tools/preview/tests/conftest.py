"""Fixtures are generated here with the pinned tools (ImageMagick, ffmpeg, Blender); none are third-party files."""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from preview.cli import main

PROVENANCE_TOML = 'roots = ["game"]\nextensions = ["png", "jpg", "wav", "mp4", "glb"]\n'


def sh(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True).stdout


def probe(path: Path) -> dict:
    """Decode the first video stream fully and report its frame count, size, pixel format, and the file's duration."""
    out = sh(
        "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=nb_read_frames,width,height,pix_fmt,codec_name:format=duration", "-of", "json", str(path),
    )
    data = json.loads(out)
    stream = data["streams"][0]
    duration = data["format"].get("duration")
    return {
        "frames": int(stream["nb_read_frames"]),
        "width": stream["width"],
        "height": stream["height"],
        "pix_fmt": stream.get("pix_fmt"),
        "codec": stream["codec_name"],
        "duration": float(duration) if duration not in (None, "N/A") else None,
    }


def probe_audio(path: Path) -> tuple[str, float]:
    out = sh("ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name:format=duration", "-of", "json", str(path))
    data = json.loads(out)
    return data["streams"][0]["codec_name"], float(data["format"]["duration"])


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generated_record(asset: Path, **generator) -> dict:
    return {
        "schema_version": 1, "asset": asset.name, "sha256": sha256(asset), "kind": "image", "origin": "generated",
        "created_at": "2026-09-27T05:00:00+00:00", "human_edits": [], "license": "proprietary",
        "generator": {"tool": "gen", "tool_version": "0.1.0", "params": {}, "inputs": [], **generator},
    }


def write_record(asset: Path, record: dict) -> None:
    asset.with_name(asset.name + ".provenance.json").write_text(json.dumps(record))


def glb(path: Path) -> Path:
    sh("blender", "-b", "--factory-startup", "--python-exit-code", "1", "--python-expr",
       "import bpy; bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.mesh.primitive_monkey_add(); "
       f"bpy.ops.export_scene.gltf(filepath={str(path)!r})")
    return path


@pytest.fixture(scope="session")
def assets(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    root = tmp_path_factory.mktemp("assets")
    scarf = root / "scarf.png"
    sh("magick", "-size", "800x600", "gradient:#7c3aed-#f472b6", str(scarf))
    wide = root / "sky.jpg"
    sh("magick", "-size", "2400x1200", "plasma:fractal", "-seed", "7", str(wide))
    frames = root / "walk"
    frames.mkdir()
    for i in range(6):
        sh("magick", "-size", "96x96", "xc:#101018", "-fill", "#a78bfa", "-draw", f"circle {16 + 12 * i},48 {24 + 12 * i},48", str(frames / f"walk_{i:02d}.png"))
    clip = root / "intro.mp4"  # yuv444p High 4:4:4, which phone browsers don't play
    sh("ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=160x120:rate=12:duration=1", "-pix_fmt", "yuv444p", str(clip))
    tone = root / "chime.wav"
    sh("ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=660:duration=1", str(tone))
    model = glb(root / "lantern.glb")
    write_record(scarf, generated_record(scarf, provider="openai", model="gpt-image-2", prompt="a violet <scarf> & a lantern"))
    tone_record = generated_record(tone, provider="x", model="y", prompt="z") | {"origin": "human", "authors": ["Sami Jawhar"], "kind": "audio"}
    del tone_record["generator"]
    write_record(tone, tone_record)
    return {"scarf": scarf, "wide": wide, "frames": frames, "clip": clip, "tone": tone, "model": model}


@pytest.fixture
def workdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A repository root: preview resolves out/ from the provenance.toml it finds."""
    (tmp_path / "provenance.toml").write_text(PROVENANCE_TOML)
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def run(capsys: pytest.CaptureFixture[str]):
    def _run(*argv: str) -> tuple[int, str, str]:
        code = main(list(argv))
        captured = capsys.readouterr()
        return code, captured.out, captured.err

    return _run
