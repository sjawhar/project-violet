import json
from datetime import datetime
from pathlib import Path

from conftest import sha256, sidecar_path, write_file


def _record_generated(run, asset: str) -> None:
    code, _, err = run(
        "record", asset, "--kind", "image", "--origin", "generated", "--license", "proprietary",
        "--tool", "imagegen", "--tool-version", "0.2.0", "--provider", "openai", "--model", "gpt-image-2",
        "--prompt", "a violet head scarf", "--seed", "7",
    )
    assert code == 0, err


def test_an_edit_keeps_the_record_and_appends_who_changed_what(repo: Path, run):
    asset = write_file(repo / "game/art/scarf.png", b"generated scarf")
    _record_generated(run, "game/art/scarf.png")
    original = json.loads(sidecar_path(asset).read_text())
    asset.write_bytes(b"scarf, hue shifted by hand")
    assert run("check")[0] != 0

    code, _, err = run("edit", "game/art/scarf.png", "--by", "Sami Jawhar", "--description", "shifted the hue toward violet")

    assert code == 0, err
    record = json.loads(sidecar_path(asset).read_text())
    assert record["sha256"] == sha256(b"scarf, hue shifted by hand")
    assert {k: v for k, v in record.items() if k not in ("sha256", "human_edits")} == {
        k: v for k, v in original.items() if k not in ("sha256", "human_edits")
    }
    [edit] = record["human_edits"]
    assert edit["by"] == "Sami Jawhar"
    assert edit["description"] == "shifted the hue toward violet"
    assert datetime.fromisoformat(edit["at"]).tzinfo is not None
    assert run("check")[0] == 0


def test_edits_accumulate(repo: Path, run):
    asset = write_file(repo / "game/art/scarf.png", b"v1")
    _record_generated(run, "game/art/scarf.png")

    asset.write_bytes(b"v2")
    assert run("edit", "game/art/scarf.png", "--by", "Sami Jawhar", "--description", "first pass")[0] == 0
    asset.write_bytes(b"v3")
    assert run("edit", "game/art/scarf.png", "--by", "A. Collaborator", "--description", "second pass")[0] == 0

    record = json.loads(sidecar_path(asset).read_text())
    assert [(e["by"], e["description"]) for e in record["human_edits"]] == [
        ("Sami Jawhar", "first pass"),
        ("A. Collaborator", "second pass"),
    ]
    assert record["sha256"] == sha256(b"v3")


def test_refuses_to_edit_an_asset_without_a_record(repo: Path, run):
    asset = write_file(repo / "game/art/scarf.png", b"scarf")

    code, _, err = run("edit", "game/art/scarf.png", "--by", "Sami Jawhar", "--description", "tweak")

    assert code != 0
    assert "game/art/scarf.png" in err
    assert not sidecar_path(asset).exists()
