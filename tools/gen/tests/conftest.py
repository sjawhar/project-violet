from pathlib import Path

import pytest

from gen.cli import main

CONFIG = """\
roots = ["game", "assets"]
extensions = ["png"]
"""


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A tmp directory with its own provenance.toml, chdir'd into: `find_config(Path.cwd())` finds it."""
    (tmp_path / "provenance.toml").write_text(CONFIG)
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def run(capsys: pytest.CaptureFixture[str]):
    """Run the gen CLI in-process; return (exit code, stdout, stderr)."""

    def _run(*argv: str) -> tuple[int, str, str]:
        code = main(list(argv))
        captured = capsys.readouterr()
        return code, captured.out, captured.err

    return _run


def sidecar_path(asset: Path) -> Path:
    return asset.with_name(asset.name + ".provenance.json")
