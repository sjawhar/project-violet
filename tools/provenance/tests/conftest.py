import hashlib
import json
from pathlib import Path

import pytest

from provenance.cli import main

CONFIG = """\
roots = ["game", "assets"]
extensions = ["png", "wav", "glb", "txt"]

[directory_extensions]
spine = ["json"]
"""


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "provenance.toml").write_text(CONFIG)
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def run(capsys: pytest.CaptureFixture[str]):
    """Run the CLI in-process; return (exit code, stdout, stderr)."""

    def _run(*argv: str) -> tuple[int, str, str]:
        code = main(list(argv))
        captured = capsys.readouterr()
        return code, captured.out, captured.err

    return _run


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_file(path: Path, data: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def sidecar_path(asset: Path) -> Path:
    return asset.with_name(asset.name + ".provenance.json")


def write_sidecar(asset: Path, record: dict) -> Path:
    sidecar = sidecar_path(asset)
    sidecar.write_text(json.dumps(record, indent=2))
    return sidecar


def human_record(path: Path, **overrides) -> dict:
    record = {
        "schema_version": 1,
        "asset": path.name,
        "sha256": sha256(path.read_bytes()),
        "kind": "image",
        "origin": "human",
        "created_at": "2026-09-27T04:30:00Z",
        "authors": ["Sami Jawhar"],
        "human_edits": [],
        "license": "proprietary",
    }
    record.update(overrides)
    return record


def generated_record(path: Path, **overrides) -> dict:
    record = {
        "schema_version": 1,
        "asset": path.name,
        "sha256": sha256(path.read_bytes()),
        "kind": "image",
        "origin": "generated",
        "created_at": "2026-09-27T04:30:00+00:00",
        "generator": {
            "tool": "imagegen",
            "tool_version": "0.1.0",
            "provider": "openai",
            "model": "gpt-image-2",
            "prompt": "a violet head scarf, painted",
            "params": {"size": "1024x1024"},
            "inputs": [],
        },
        "human_edits": [],
        "license": "proprietary",
    }
    record.update(overrides)
    return record
