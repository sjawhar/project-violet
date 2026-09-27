import copy
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


@pytest.mark.parametrize(
    ("mutate", "field"),
    [
        (lambda r: r.update(kind="sprite"), "kind"),
        (lambda r: r.update(origin="ai"), "origin"),
        (lambda r: r.pop("generator"), "generator"),
        (_drop_generator_field("model"), "model"),
        (_drop_generator_field("prompt"), "prompt"),
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
