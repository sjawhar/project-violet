from pathlib import Path

from conftest import generated_record, human_record, write_file, write_sidecar


def _generator(tool: str, tool_version: str, provider: str, model: str, **extra) -> dict:
    return {
        "tool": tool,
        "tool_version": tool_version,
        "provider": provider,
        "model": model,
        "prompt": "prompt text",
        "params": {},
        "inputs": [],
        **extra,
    }


def _sections(markdown: str) -> dict[str, str]:
    """Map each '### ' heading's first word to the text under it."""
    sections: dict[str, str] = {}
    current = None
    for line in markdown.splitlines():
        if line.startswith("### "):
            current = line.removeprefix("### ").split()[0]
            sections[current] = ""
        elif current is not None:
            sections[current] += line + "\n"
    return sections


def _record(repo: Path, relative: str, record_for, **fields) -> None:
    asset = write_file(repo / relative, relative.encode())
    write_sidecar(asset, record_for(asset, **fields))


def test_groups_ai_assets_by_kind_naming_tools_and_models_and_excludes_human_assets(repo: Path, run):
    _record(repo, "game/art/scarf.png", generated_record, kind="image",
            generator=_generator("imagegen", "0.2.0", "openai", "gpt-image-2", model_version="2026-08-01"))
    _record(repo, "game/props/lantern.glb", generated_record, kind="model3d",
            generator=_generator("meshgen", "0.1.0", "tripo", "tripo-v3"))
    _record(repo, "game/audio/theme.wav", generated_record, kind="audio",
            generator=_generator("musicgen", "0.3.0", "elevenlabs", "eleven-music-v1"))
    _record(repo, "game/anim/spine/violet.json", generated_record, kind="animation", origin="derived",
            generator=_generator("rigtool", "1.0.0", "local", "auto-rig-2"))
    _record(repo, "game/text/credits.txt", human_record, kind="text", authors=["Hand Written Author"])

    code, out, err = run("steam-report")

    assert code == 0, err
    sections = _sections(out)
    assert set(sections) == {"Art", "Audio", "Animation"}
    for name in ("imagegen", "0.2.0", "gpt-image-2", "2026-08-01", "openai", "meshgen", "tripo-v3"):
        assert name in sections["Art"]
    assert "musicgen" not in sections["Art"] and "rigtool" not in sections["Art"]
    for name in ("musicgen", "eleven-music-v1", "elevenlabs"):
        assert name in sections["Audio"]
    assert "imagegen" not in sections["Audio"]
    for name in ("rigtool", "auto-rig-2"):
        assert name in sections["Animation"]
    assert "credits.txt" not in out
    assert "Hand Written Author" not in out


def test_states_there_is_no_ai_content_when_every_asset_is_human_made(repo: Path, run):
    _record(repo, "game/art/sketch.png", human_record)

    code, out, err = run("steam-report")

    assert code == 0, err
    assert _sections(out) == {}
    assert "no" in out.lower()


def test_refuses_to_report_while_an_asset_lacks_a_valid_record(repo: Path, run):
    _record(repo, "game/art/scarf.png", generated_record)
    write_file(repo / "game/audio/unrecorded.wav", b"RIFF")

    code, out, err = run("steam-report")

    assert code != 0
    assert "game/audio/unrecorded.wav" in err
    assert out == ""
