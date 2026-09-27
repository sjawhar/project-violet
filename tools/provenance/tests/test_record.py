import json
from datetime import datetime
from pathlib import Path

from conftest import sha256, sidecar_path, write_file

GENERATOR_FLAGS = [
    "--tool", "imagegen",
    "--tool-version", "0.2.0",
    "--provider", "openai",
    "--model", "gpt-image-2",
    "--prompt", "a violet head scarf, painted",
]


def test_records_a_generated_asset_that_then_passes_check(repo: Path, run):
    asset = write_file(repo / "game/art/scarf.png", b"scarf pixels")
    reference = write_file(repo / "docs/refs/scarf-sketch.png", b"sketch pixels")

    code, _, err = run(
        "record", "game/art/scarf.png", "--kind", "image", "--origin", "generated", "--license", "proprietary",
        *GENERATOR_FLAGS,
        "--model-version", "2026-08-01",
        "--negative-prompt", "text, watermark",
        "--seed", "42",
        "--param", "size=1024x1024",
        "--param", "quality=high",
        "--input", "docs/refs/scarf-sketch.png",
    )

    assert code == 0, err
    record = json.loads(sidecar_path(asset).read_text())
    assert record["asset"] == "scarf.png"
    assert record["sha256"] == sha256(b"scarf pixels")
    assert record["kind"] == "image"
    assert record["origin"] == "generated"
    assert record["license"] == "proprietary"
    assert record["human_edits"] == []
    assert "authors" not in record
    assert datetime.fromisoformat(record["created_at"]).tzinfo is not None
    assert record["generator"] == {
        "tool": "imagegen",
        "tool_version": "0.2.0",
        "provider": "openai",
        "model": "gpt-image-2",
        "model_version": "2026-08-01",
        "prompt": "a violet head scarf, painted",
        "negative_prompt": "text, watermark",
        "seed": 42,
        "params": {"size": "1024x1024", "quality": "high"},
        "inputs": [{"path": "docs/refs/scarf-sketch.png", "sha256": sha256(b"sketch pixels")}],
    }
    assert reference.exists()
    assert run("check")[0] == 0


def test_records_a_human_asset_that_then_passes_check(repo: Path, run):
    asset = write_file(repo / "game/art/sketch.png", b"hand drawn")

    code, _, err = run(
        "record", "game/art/sketch.png", "--kind", "image", "--origin", "human", "--license", "proprietary",
        "--author", "Sami Jawhar", "--author", "A. Collaborator",
    )

    assert code == 0, err
    record = json.loads(sidecar_path(asset).read_text())
    assert record["origin"] == "human"
    assert record["authors"] == ["Sami Jawhar", "A. Collaborator"]
    assert "generator" not in record
    assert run("check")[0] == 0


def test_records_a_derived_asset_with_its_inputs_and_human_edits(repo: Path, run):
    source = write_file(repo / "game/art/scarf.png", b"generated scarf")
    derived = write_file(repo / "game/art/scarf-recolored.png", b"recolored scarf")

    code, _, err = run(
        "record", "game/art/scarf-recolored.png", "--kind", "image", "--origin", "derived", "--license", "proprietary",
        *GENERATOR_FLAGS,
        "--input", str(source),
        "--human-edit", "Sami Jawhar: shifted the scarf hue toward violet",
    )

    assert code == 0, err
    record = json.loads(sidecar_path(derived).read_text())
    assert record["origin"] == "derived"
    assert record["generator"]["inputs"] == [{"path": "game/art/scarf.png", "sha256": sha256(b"generated scarf")}]
    assert record["human_edits"] == [
        {"by": "Sami Jawhar", "description": "shifted the scarf hue toward violet", "at": record["created_at"]}
    ]
    # check also covers scarf.png, which has no record yet; restrict it to the derived asset.
    assert run("check", "game/art/scarf-recolored.png")[0] == 0


def test_refuses_a_generated_asset_without_provider_model_and_prompt(repo: Path, run):
    asset = write_file(repo / "game/art/scarf.png", b"scarf")

    code, _, err = run(
        "record", "game/art/scarf.png", "--kind", "image", "--origin", "generated", "--license", "proprietary",
        "--tool", "imagegen", "--tool-version", "0.2.0",
    )

    assert code != 0
    for flag in ("--provider", "--model", "--prompt"):
        assert flag in err
    assert not sidecar_path(asset).exists()


def test_refuses_generator_flags_on_a_human_asset(repo: Path, run):
    asset = write_file(repo / "game/art/sketch.png", b"hand drawn")

    code, _, err = run(
        "record", "game/art/sketch.png", "--kind", "image", "--origin", "human", "--license", "proprietary",
        "--author", "Sami Jawhar", "--model", "gpt-image-2",
    )

    assert code != 0
    assert "--model" in err
    assert not sidecar_path(asset).exists()


def test_refuses_a_human_asset_without_an_author(repo: Path, run):
    asset = write_file(repo / "game/art/sketch.png", b"hand drawn")

    code, _, err = run("record", "game/art/sketch.png", "--kind", "image", "--origin", "human", "--license", "proprietary")

    assert code != 0
    assert "--author" in err
    assert not sidecar_path(asset).exists()


def test_refuses_to_overwrite_an_existing_record_unless_forced(repo: Path, run):
    asset = write_file(repo / "game/art/sketch.png", b"v1")
    args = ["record", "game/art/sketch.png", "--kind", "image", "--origin", "human", "--license", "proprietary", "--author", "Sami Jawhar"]
    assert run(*args)[0] == 0
    asset.write_bytes(b"v2")

    code, _, err = run(*args)
    assert code != 0
    assert "--force" in err
    assert json.loads(sidecar_path(asset).read_text())["sha256"] == sha256(b"v1")

    assert run(*args, "--force")[0] == 0
    assert json.loads(sidecar_path(asset).read_text())["sha256"] == sha256(b"v2")


def test_refuses_an_input_outside_the_repository(repo: Path, tmp_path_factory, run):
    write_file(repo / "game/art/scarf.png", b"scarf")
    outside = write_file(tmp_path_factory.mktemp("elsewhere") / "ref.png", b"ref")

    code, _, err = run(
        "record", "game/art/scarf.png", "--kind", "image", "--origin", "generated", "--license", "proprietary",
        *GENERATOR_FLAGS, "--input", str(outside),
    )

    assert code != 0
    assert "ref.png" in err
    assert not sidecar_path(repo / "game/art/scarf.png").exists()
