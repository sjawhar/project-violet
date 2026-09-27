"""Fixtures are generated here with the pinned tools (ImageMagick, ffmpeg, Blender); none are third-party files."""

import json
import subprocess
from pathlib import Path

import pytest

from preview.cli import main


def sh(*args: str) -> str:
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


def probe(path: Path) -> dict:
    """Decode the first video stream fully and report its frame count, size, and the file's duration."""
    out = sh(
        "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=nb_read_frames,width,height:format=duration", "-of", "json", str(path),
    )
    data = json.loads(out)
    stream = data["streams"][0]
    duration = data["format"].get("duration")
    return {
        "frames": int(stream["nb_read_frames"]),
        "width": stream["width"],
        "height": stream["height"],
        "duration": float(duration) if duration not in (None, "N/A") else None,
    }


def probe_audio(path: Path) -> float:
    out = sh("ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "format=duration", "-of", "json", str(path))
    return float(json.loads(out)["format"]["duration"])


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
    clip = root / "intro.mp4"
    sh("ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=160x120:rate=12:duration=1", "-pix_fmt", "yuv420p", str(clip))
    tone = root / "chime.wav"
    sh("ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=660:duration=1", str(tone))
    model = root / "lantern.glb"
    sh(
        "blender", "-b", "--factory-startup", "--python-exit-code", "1", "--python-expr",
        "import bpy; bpy.ops.wm.read_factory_settings(use_empty=True); "
        "bpy.ops.mesh.primitive_monkey_add(); "
        f"bpy.ops.export_scene.gltf(filepath={str(model)!r})",
    )
    (root / "scarf.png.provenance.json").write_text(json.dumps({
        "origin": "generated",
        "generator": {"provider": "openai", "model": "gpt-image-2", "prompt": "a violet <scarf> & a lantern"},
    }))
    (root / "chime.wav.provenance.json").write_text(json.dumps({"origin": "human", "authors": ["Sami Jawhar"]}))
    return {"scarf": scarf, "wide": wide, "frames": frames, "clip": clip, "tone": tone, "model": model}


@pytest.fixture
def workdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def run(capsys: pytest.CaptureFixture[str]):
    def _run(*argv: str) -> tuple[int, str, str]:
        code = main(list(argv))
        captured = capsys.readouterr()
        return code, captured.out, captured.err

    return _run
