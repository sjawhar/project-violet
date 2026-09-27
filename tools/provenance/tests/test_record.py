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


def _record_human(run, asset: str) -> None:
    code, _, err = run("record", asset, "--kind", "image", "--origin", "human", "--license", "proprietary", "--author", "Sami Jawhar")
    assert code == 0, err


def test_records_a_generated_asset_that_then_passes_check(repo: Path, run):
    asset = write_file(repo / "game/art/scarf.png", b"scarf pixels")
    write_file(repo / "docs/refs/scarf-sketch.png", b"sketch pixels")
    _record_human(run, "docs/refs/scarf-sketch.png")

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


def test_records_a_derived_asset_made_without_a_model(repo: Path, run):
    """A texture atlas, crop, or transcode names its tool and inputs and states that no model was used."""
    sprite = write_file(repo / "game/art/scarf.png", b"generated scarf")
    _record_human(run, "game/art/scarf.png")
    atlas = write_file(repo / "game/art/atlas.png", b"packed atlas")

    code, _, err = run(
        "record", "game/art/atlas.png", "--kind", "image", "--origin", "derived", "--license", "proprietary",
        "--tool", "texpack", "--tool-version", "1.0", "--no-model", "--param", "padding=2", "--input", str(sprite),
    )

    assert code == 0, err
    record = json.loads(sidecar_path(atlas).read_text())
    assert record["origin"] == "derived"
    assert record["generator"] == {
        "tool": "texpack",
        "tool_version": "1.0",
        "model": None,
        "params": {"padding": "2"},
        "inputs": [{"path": "game/art/scarf.png", "sha256": sha256(b"generated scarf")}],
    }
    assert run("check")[0] == 0


def test_refuses_a_derived_asset_that_says_nothing_about_a_model(repo: Path, run):
    source = write_file(repo / "game/art/scarf.png", b"scarf")
    _record_human(run, "game/art/scarf.png")
    asset = write_file(repo / "game/art/scarf-4x.png", b"upscaled")

    code, _, err = run(
        "record", "game/art/scarf-4x.png", "--kind", "image", "--origin", "derived", "--license", "proprietary",
        "--tool", "upscale", "--tool-version", "2", "--input", str(source),
    )

    assert code != 0
    assert "--model" in err and "--no-model" in err
    assert not sidecar_path(asset).exists()


def test_refuses_no_model_where_a_model_is_named_or_required(repo: Path, run):
    source = write_file(repo / "game/art/scarf.png", b"scarf")
    asset = write_file(repo / "game/art/out.png", b"out")
    base = ["record", "game/art/out.png", "--kind", "image", "--license", "proprietary", "--tool", "t", "--tool-version", "1", "--no-model"]

    both = run(*base, "--origin", "derived", "--provider", "p", "--model", "m", "--input", str(source))
    generated = run(*base, "--origin", "generated", "--provider", "p", "--prompt", "x")

    assert both[0] != 0 and "--no-model" in both[2]
    assert generated[0] != 0 and "--no-model" in generated[2]
    assert not sidecar_path(asset).exists()


def test_refuses_a_derived_asset_without_inputs(repo: Path, run):
    asset = write_file(repo / "game/art/atlas.png", b"packed atlas")

    code, _, err = run(
        "record", "game/art/atlas.png", "--kind", "image", "--origin", "derived", "--license", "proprietary",
        "--tool", "texpack", "--tool-version", "1.0",
    )

    assert code != 0
    assert "--input" in err
    assert not sidecar_path(asset).exists()


def test_refuses_a_model_without_its_provider(repo: Path, run):
    source = write_file(repo / "game/art/scarf.png", b"scarf")
    asset = write_file(repo / "game/art/scarf-4x.png", b"upscaled")

    code, _, err = run(
        "record", "game/art/scarf-4x.png", "--kind", "image", "--origin", "derived", "--license", "proprietary",
        "--tool", "upscale", "--tool-version", "2.1", "--model", "esrgan-4x", "--input", str(source),
    )

    assert code != 0
    assert "--provider" in err
    assert not sidecar_path(asset).exists()


def test_refuses_to_record_a_git_lfs_pointer_instead_of_the_asset(repo: Path, run):
    asset = write_file(
        repo / "game/art/hero.png",
        b"version https://git-lfs.github.com/spec/v1\noid sha256:" + b"a" * 64 + b"\nsize 12345\n",
    )

    code, _, err = run(
        "record", "game/art/hero.png", "--kind", "image", "--origin", "human", "--license", "proprietary", "--author", "Sami Jawhar",
    )

    assert code != 0
    assert "game/art/hero.png" in err
    assert not sidecar_path(asset).exists()


def test_writes_the_sidecar_beside_a_symlinked_asset(repo: Path, run):
    target = write_file(repo / "shared/hero.png", b"hero")
    link = repo / "game/art/hero.png"
    link.parent.mkdir(parents=True)
    link.symlink_to(target)

    code, _, err = run(
        "record", "game/art/hero.png", "--kind", "image", "--origin", "human", "--license", "proprietary", "--author", "Sami Jawhar",
    )

    assert code == 0, err
    assert sidecar_path(link).exists()
    assert not sidecar_path(target).exists()
    assert run("check")[0] == 0


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


def test_a_forced_record_that_fails_validation_keeps_the_existing_sidecar(repo: Path, run):
    asset = write_file(repo / "game/art/sketch.png", b"v1")
    args = ["record", "game/art/sketch.png", "--kind", "image", "--origin", "human", "--license", "proprietary"]
    assert run(*args, "--author", "Sami Jawhar")[0] == 0
    before = sidecar_path(asset).read_text()
    asset.write_bytes(b"v2")

    code, _, _ = run(*args, "--force")  # no --author

    assert code != 0
    assert sidecar_path(asset).read_text() == before


def test_refuses_an_empty_license(repo: Path, run):
    asset = write_file(repo / "game/art/sketch.png", b"hand drawn")

    code, _, err = run(
        "record", "game/art/sketch.png", "--kind", "image", "--origin", "human", "--license", "", "--author", "Sami Jawhar",
    )

    assert code != 0
    assert "license" in err
    assert not sidecar_path(asset).exists()


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
