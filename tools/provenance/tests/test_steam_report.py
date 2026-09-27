import re
from pathlib import Path

from conftest import generated_record, human_record, sha256, write_file, write_sidecar


def _generator(tool: str, tool_version: str, provider: str | None = None, model: str | None = None, inputs=(), **extra) -> dict:
    generator = {"tool": tool, "tool_version": tool_version, "params": {}, "inputs": list(inputs), **extra}
    if model is not None:
        generator |= {"provider": provider, "model": model, "prompt": "prompt text"}
    return generator


def _input(repo: Path, relative: str) -> dict:
    return {"path": relative, "sha256": sha256((repo / relative).read_bytes())}


def _record(repo: Path, relative: str, record_for, **fields) -> None:
    asset = write_file(repo / relative, relative.encode())
    write_sidecar(asset, record_for(asset, **fields))


def _sections(markdown: str) -> dict[str, tuple[int, str]]:
    """Map each '### <Title> (<n> assets)' heading's title to (n, the text under it)."""
    sections: dict[str, tuple[int, str]] = {}
    current = None
    for line in markdown.splitlines():
        heading = re.fullmatch(r"### (\w+) \((\d+) assets?\)", line)
        if heading:
            current = heading.group(1)
            sections[current] = (int(heading.group(2)), "")
        elif current is not None:
            count, body = sections[current]
            sections[current] = (count, body + line + "\n")
    return sections


def test_groups_ai_assets_by_kind_naming_tools_and_models_and_excludes_human_assets(repo: Path, run):
    _record(repo, "game/art/sketch.png", human_record, kind="image")
    _record(repo, "game/art/scarf.png", generated_record, kind="image",
            generator=_generator("imagegen", "0.2.0", "openai", "gpt-image-2", model_version="2026-08-01"))
    _record(repo, "game/props/lantern.glb", generated_record, kind="model3d",
            generator=_generator("meshgen", "0.1.0", "tripo", "tripo-v3"))
    _record(repo, "game/audio/theme.wav", generated_record, kind="audio",
            generator=_generator("musicgen", "0.3.0", "elevenlabs", "eleven-music-v1"))
    _record(repo, "game/anim/spine/violet.json", generated_record, kind="animation", origin="derived",
            generator=_generator("rigtool", "1.0.0", "local", "auto-rig-2", inputs=[_input(repo, "game/art/sketch.png")]))
    _record(repo, "game/text/barks.txt", generated_record, kind="text",
            generator=_generator("writer", "0.1.0", "anthropic", "claude-opus-5"))

    code, out, err = run("steam-report")

    assert code == 0, err
    assert "(5 assets)" in out.splitlines()[0]
    sections = _sections(out)
    assert {title: count for title, (count, _) in sections.items()} == {"Art": 2, "Audio": 1, "Animation": 1, "Text": 1}
    art = sections["Art"][1]
    for name in ("imagegen 0.2.0", "gpt-image-2 2026-08-01 (openai)", "meshgen 0.1.0", "tripo-v3 (tripo)"):
        assert name in art
    for other in ("musicgen", "rigtool", "writer"):
        assert other not in art
    assert "musicgen 0.3.0" in sections["Audio"][1] and "eleven-music-v1 (elevenlabs)" in sections["Audio"][1]
    assert "rigtool 1.0.0" in sections["Animation"][1] and "auto-rig-2 (local)" in sections["Animation"][1]
    assert "writer 0.1.0" in sections["Text"][1] and "claude-opus-5 (anthropic)" in sections["Text"][1]


def test_follows_derived_assets_back_through_their_inputs(repo: Path, run):
    _record(repo, "game/art/sprite.png", generated_record,
            generator=_generator("imagegen", "0.2.0", "openai", "gpt-image-2"))
    _record(repo, "game/art/atlas.png", generated_record, origin="derived",
            generator=_generator("texpack", "1.0", inputs=[_input(repo, "game/art/sprite.png")]))
    # A human sketch outside the asset roots, cropped by a tool: no AI anywhere in its lineage.
    _record(repo, "docs/refs/sketch.png", human_record)
    _record(repo, "game/art/sketch-crop.png", generated_record, origin="derived",
            generator=_generator("imagecrop", "3.0", inputs=[_input(repo, "docs/refs/sketch.png")]))

    code, out, err = run("steam-report")

    assert code == 0, err
    sections = _sections(out)
    assert list(sections) == ["Art"]
    count, art = sections["Art"]
    assert count == 2
    assert "texpack 1.0" in art and "imagegen 0.2.0" in art and "gpt-image-2 (openai)" in art
    assert "imagecrop" not in art


def test_refuses_when_a_derived_asset_has_an_input_without_a_record(repo: Path, run):
    write_file(repo / "docs/refs/sheet.png", b"unrecorded sheet")
    _record(repo, "game/art/atlas.png", generated_record, origin="derived",
            generator=_generator("texpack", "1.0", inputs=[_input(repo, "docs/refs/sheet.png")]))
    assert run("check")[0] == 0

    code, out, err = run("steam-report")

    assert code != 0
    assert "docs/refs/sheet.png" in err
    assert out == ""


def test_prints_nothing_when_no_recorded_asset_involves_ai(repo: Path, run):
    _record(repo, "game/art/sketch.png", human_record)

    code, out, err = run("steam-report")

    assert code == 0, err
    assert out == ""


def test_refuses_to_report_while_an_asset_lacks_a_valid_record(repo: Path, run):
    _record(repo, "game/art/scarf.png", generated_record)
    write_file(repo / "game/audio/unrecorded.wav", b"RIFF")

    code, out, err = run("steam-report")

    assert code != 0
    assert "game/audio/unrecorded.wav" in err
    assert out == ""
