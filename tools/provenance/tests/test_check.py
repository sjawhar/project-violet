import copy
import hashlib
from pathlib import Path

import pytest

from conftest import generated_record, human_record, sidecar_path, write_file, write_sidecar


def test_passes_when_every_asset_has_a_valid_sidecar(repo: Path, run):
    hero = write_file(repo / "game/art/hero.png", b"\x89PNG hero")
    write_sidecar(hero, human_record(hero))
    rig = write_file(repo / "game/characters/spine/violet.json", b'{"skeleton": {}}')
    write_sidecar(rig, generated_record(rig, kind="animation"))
    # Not assets: extension not configured, and .json outside a spine/ directory.
    write_file(repo / "game/notes.md", b"# notes")
    write_file(repo / "game/levels/room1.json", b"{}")
    # The "assets" root does not exist, which is fine.

    code, _, err = run("check")

    assert code == 0, err


def test_fails_naming_each_asset_without_a_sidecar(repo: Path, run):
    write_file(repo / "game/art/hero.png", b"hero")
    write_file(repo / "assets/sfx/jump.wav", b"RIFF jump")
    write_file(repo / "game/characters/spine/violet.json", b"{}")

    code, _, err = run("check")

    assert code != 0
    assert "game/art/hero.png" in err
    assert "assets/sfx/jump.wav" in err
    assert "game/characters/spine/violet.json" in err


def _drop_generator_field(field: str):
    def mutate(record: dict) -> None:
        del record["generator"][field]

    return mutate


def _set_generator_field(field: str, value):
    def mutate(record: dict) -> None:
        record["generator"][field] = value

    return mutate


@pytest.mark.parametrize(
    ("mutate", "field"),
    [
        (lambda r: r.update(kind="sprite"), "kind"),
        (lambda r: r.update(origin="ai"), "origin"),
        (lambda r: r.pop("generator"), "generator"),
        (_drop_generator_field("model"), "model"),
        (_drop_generator_field("prompt"), "prompt"),
        (_drop_generator_field("provider"), "provider"),
        (_set_generator_field("model", "gpt-image-2\n### Injected heading"), "model"),
        (lambda r: r.update(origin="derived"), "inputs"),
        (lambda r: r.update(created_at="last tuesday"), "created_at"),
        (lambda r: r.update(created_at="2026-09-27"), "created_at"),
        (lambda r: r.update(origin="human", authors=["Sami Jawhar"]), "generator"),
        (lambda r: r.pop("license"), "license"),
        (lambda r: r.update(sha256="ABC"), "sha256"),
        (lambda r: r.update(unexpected=True), "unexpected"),
    ],
)
def test_fails_naming_the_file_and_field_when_the_sidecar_violates_the_schema(repo: Path, run, mutate, field):
    asset = write_file(repo / "game/art/scarf.png", b"scarf")
    record = copy.deepcopy(generated_record(asset))
    mutate(record)
    write_sidecar(asset, record)

    code, _, err = run("check")

    assert code != 0
    assert "game/art/scarf.png.provenance.json" in err
    assert field in err


def test_fails_when_a_human_asset_has_no_authors(repo: Path, run):
    asset = write_file(repo / "game/art/sketch.png", b"sketch")
    record = human_record(asset)
    del record["authors"]
    write_sidecar(asset, record)

    code, _, err = run("check")

    assert code != 0
    assert "game/art/sketch.png.provenance.json" in err
    assert "authors" in err


def test_fails_when_the_sidecar_is_not_json(repo: Path, run):
    asset = write_file(repo / "game/art/hero.png", b"hero")
    sidecar_path(asset).write_text("{not json")

    code, _, err = run("check")

    assert code != 0
    assert "game/art/hero.png.provenance.json" in err


def test_fails_when_the_recorded_hash_is_stale(repo: Path, run):
    asset = write_file(repo / "game/art/hero.png", b"hero v1")
    write_sidecar(asset, human_record(asset))
    asset.write_bytes(b"hero v2, edited after recording")

    code, _, err = run("check")

    assert code != 0
    assert "game/art/hero.png" in err
    assert "sha256" in err


def test_fails_when_the_sidecar_names_a_different_asset(repo: Path, run):
    asset = write_file(repo / "game/art/hero.png", b"hero")
    write_sidecar(asset, human_record(asset, asset="villain.png"))

    code, _, err = run("check")

    assert code != 0
    assert "game/art/hero.png.provenance.json" in err
    assert "villain.png" in err


def test_explicit_paths_limit_the_check_to_those_paths(repo: Path, run):
    good = write_file(repo / "game/art/hero.png", b"hero")
    write_sidecar(good, human_record(good))
    write_file(repo / "game/audio/unrecorded.wav", b"RIFF")

    assert run("check", "game/art")[0] == 0
    assert run("check", "game/art/hero.png")[0] == 0
    code, _, err = run("check", "game/audio/unrecorded.wav")
    assert code != 0
    assert "game/audio/unrecorded.wav" in err


def test_fails_on_an_explicit_path_that_does_not_exist(repo: Path, run):
    code, _, err = run("check", "game/missing.png")

    assert code != 0
    assert "game/missing.png" in err


def test_fails_outside_a_tree_with_provenance_toml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, run):
    monkeypatch.chdir(tmp_path)

    code, _, err = run("check")

    assert code != 0
    assert "provenance.toml" in err


def test_checks_extensions_case_insensitively(repo: Path, run):
    write_file(repo / "game/art/HERO.PNG", b"hero")

    code, _, err = run("check")

    assert code != 0
    assert "game/art/HERO.PNG" in err


def _lfs_pointer(content: bytes) -> bytes:
    return (
        "version https://git-lfs.github.com/spec/v1\n"
        f"oid sha256:{hashlib.sha256(content).hexdigest()}\n"
        f"size {len(content)}\n"
    ).encode()


def test_accepts_an_lfs_pointer_on_disk_whose_oid_matches_the_record(repo: Path, run):
    """CI checks out with lfs: false, so assets on disk are pointers to the recorded content."""
    asset = write_file(repo / "game/art/hero.png", b"real hero pixels")
    write_sidecar(asset, human_record(asset))
    asset.write_bytes(_lfs_pointer(b"real hero pixels"))

    code, _, err = run("check")

    assert code == 0, err


def test_fails_when_an_lfs_pointer_on_disk_points_at_other_content(repo: Path, run):
    asset = write_file(repo / "game/art/hero.png", b"real hero pixels")
    write_sidecar(asset, human_record(asset))
    asset.write_bytes(_lfs_pointer(b"hero pixels, edited later"))

    code, _, err = run("check")

    assert code != 0
    assert "game/art/hero.png" in err
    assert "sha256" in err


def test_a_sidecar_named_on_the_command_line_checks_its_asset(repo: Path, run):
    good = write_file(repo / "game/art/hero.png", b"hero")
    write_sidecar(good, human_record(good))
    stale = write_file(repo / "game/art/scarf.png", b"scarf")
    write_sidecar(stale, human_record(stale))
    stale.write_bytes(b"scarf, edited")

    assert run("check", "game/art/hero.png.provenance.json", "game/art/hero.png")[0] == 0
    code, _, err = run("check", "game/art/scarf.png.provenance.json")
    assert code != 0
    assert "game/art/scarf.png" in err


def test_reports_each_problem_once_when_paths_overlap(repo: Path, run):
    write_file(repo / "game/art/hero.png", b"hero")

    code, _, err = run("check", "game", "game/art", "game/art/hero.png")

    assert code != 0
    assert err.count("game/art/hero.png:") == 1


def test_checks_a_symlinked_asset_against_the_sidecar_beside_the_link(repo: Path, run):
    target = write_file(repo / "shared/hero.png", b"hero")
    link = repo / "game/art/hero.png"
    link.parent.mkdir(parents=True)
    link.symlink_to(target)
    write_sidecar(link, human_record(link))

    assert run("check")[0] == 0
    assert run("check", "game/art/hero.png")[0] == 0


@pytest.mark.parametrize(
    "config",
    [
        'roots = ["game"]\nextensions = [".png"]\n',
        'roots = ["game"]\nextensions = ["png"]\n[directory_extensions]\n"characters/spine" = ["json"]\n',
        'roots = ["game"]\nextensions = ["png"]\ndirectory_extension = {spine = ["json"]}\n',
        'extensions = ["png"]\n',
        'roots = "game"\nextensions = ["png"]\n',
    ],
)
def test_refuses_a_config_that_could_silently_match_nothing(repo: Path, run, config: str):
    (repo / "provenance.toml").write_text(config)
    write_file(repo / "game/art/hero.png", b"hero")

    code, _, err = run("check")

    assert code != 0
    assert "provenance.toml" in err


def test_fails_when_a_derived_record_says_nothing_about_a_model(repo: Path, run):
    """A derived record must name its model or state "model": null; silence could hide AI use."""
    source = write_file(repo / "game/art/scarf.png", b"scarf")
    write_sidecar(source, human_record(source))
    asset = write_file(repo / "game/art/scarf-4x.png", b"upscaled")
    record = generated_record(asset, origin="derived")
    record["generator"] = {
        "tool": "upscale",
        "tool_version": "2",
        "params": {},
        "inputs": [{"path": "game/art/scarf.png", "sha256": hashlib.sha256(b"scarf").hexdigest()}],
    }
    write_sidecar(asset, record)

    code, _, err = run("check")

    assert code != 0
    assert "game/art/scarf-4x.png.provenance.json" in err
    assert "model" in err


def _input(repo: Path, relative: str) -> dict:
    return {"path": relative, "sha256": hashlib.sha256((repo / relative).read_bytes()).hexdigest()}


def _generated_from(repo: Path, relative: str, *inputs: str) -> Path:
    asset = write_file(repo / relative, relative.encode())
    record = generated_record(asset)
    record["generator"]["inputs"] = [_input(repo, path) for path in inputs]
    write_sidecar(asset, record)
    return asset


def test_passes_when_every_input_is_recorded_and_current(repo: Path, run):
    sketch = write_file(repo / "docs/refs/sketch.png", b"sketch")
    write_sidecar(sketch, human_record(sketch))
    _generated_from(repo, "game/art/scarf.png", "docs/refs/sketch.png")

    code, _, err = run("check")

    assert code == 0, err


def test_fails_when_an_input_has_no_record(repo: Path, run):
    write_file(repo / "docs/refs/sketch.png", b"sketch")
    _generated_from(repo, "game/art/scarf.png", "docs/refs/sketch.png")

    code, _, err = run("check")

    assert code != 0
    assert "game/art/scarf.png.provenance.json" in err
    assert "$.generator.inputs[0]" in err
    assert "docs/refs/sketch.png" in err


def test_fails_when_an_input_record_is_stale(repo: Path, run):
    sketch = write_file(repo / "docs/refs/sketch.png", b"sketch")
    write_sidecar(sketch, human_record(sketch))
    _generated_from(repo, "game/art/scarf.png", "docs/refs/sketch.png")
    sketch.write_bytes(b"sketch, replaced later")

    code, _, err = run("check")

    assert code != 0
    assert "docs/refs/sketch.png" in err
    assert "sha256" in err


def test_fails_when_an_input_changed_after_the_asset_was_made_from_it(repo: Path, run):
    sketch = write_file(repo / "docs/refs/sketch.png", b"sketch v1")
    write_sidecar(sketch, human_record(sketch))
    _generated_from(repo, "game/art/scarf.png", "docs/refs/sketch.png")
    sketch.write_bytes(b"sketch v2")
    write_sidecar(sketch, human_record(sketch))  # the input's own record is current again

    code, _, err = run("check")

    assert code != 0
    assert "game/art/scarf.png.provenance.json" in err
    assert "$.generator.inputs[0]" in err


def test_fails_on_a_sidecar_whose_asset_is_gone(repo: Path, run):
    kept = write_file(repo / "game/art/hero.png", b"hero")
    write_sidecar(kept, human_record(kept))
    renamed = write_file(repo / "game/art/old-name.png", b"villain")
    write_sidecar(renamed, human_record(renamed))
    renamed.rename(repo / "game/art/villain.png")

    code, _, err = run("check", "game/art/hero.png")  # an explicit asset path does not scan for orphans
    assert code == 0, err

    code, _, err = run("check")
    assert code != 0
    assert "game/art/old-name.png.provenance.json" in err


def test_fails_on_a_symlinked_directory_under_a_root(repo: Path, run):
    shared = write_file(repo / "shared/art/hero.png", b"hero").parent
    (repo / "game").mkdir()
    (repo / "game/art").symlink_to(shared, target_is_directory=True)

    code, _, err = run("check")

    assert code != 0
    assert "game/art" in err


def test_fails_on_a_dangling_symlink_under_a_root(repo: Path, run):
    (repo / "game/art").mkdir(parents=True)
    (repo / "game/art/hero.png").symlink_to(repo / "missing/hero.png")

    code, _, err = run("check")

    assert code != 0
    assert "game/art/hero.png" in err
