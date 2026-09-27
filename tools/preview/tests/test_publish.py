import os
import subprocess
from pathlib import Path

import pytest

from preview.publish import update_gh_pages

GIT_IDENTITY = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"}


def sh(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True, env={**os.environ, **GIT_IDENTITY}).stdout


def tree(remote: Path) -> dict[str, str]:
    """path -> blob id of every file on the remote's gh-pages branch."""
    lines = sh("git", "-C", str(remote), "ls-tree", "-r", "gh-pages").splitlines()
    return {line.split("\t")[1]: line.split()[2] for line in lines}


@pytest.fixture
def clone(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """A jj clone of a local remote whose gh-pages branch holds an unrelated site."""
    remote = tmp_path / "remote.git"
    sh("git", "init", "-q", "--bare", "-b", "master", str(remote))
    seed = tmp_path / "seed"
    sh("git", "init", "-q", "-b", "gh-pages", str(seed))
    (seed / "index.html").write_text("<p>2019 web build</p>")
    (seed / "Build").mkdir()
    (seed / "Build" / "game.data").write_bytes(b"\0" * 64)
    sh("git", "add", ".", cwd=seed)
    sh("git", "commit", "-q", "-m", "site", cwd=seed)
    sh("git", "push", "-q", str(remote), "gh-pages", cwd=seed)
    checkout = tmp_path / "clone"
    sh("jj", "git", "clone", "--colocate", str(remote), str(checkout))
    monkeypatch.chdir(checkout)
    return remote, checkout


def _build(root: Path) -> Path:
    build = root / "build"
    (build / "items").mkdir(parents=True)
    (build / "index.html").write_text("<p>gallery</p>")
    (build / "preview.json").write_text("{}")
    (build / "items" / "big.gif").write_bytes(os.urandom(3 * 1024 * 1024))  # above jj's default 1 MiB snapshot limit
    return build


def test_publishes_every_file_and_touches_nothing_else(tmp_path: Path, clone):
    remote, _ = clone
    before = tree(remote)

    commit = update_gh_pages("5", _build(tmp_path))

    after = tree(remote)
    assert commit is not None
    assert set(after) == set(before) | {"review/pr-5/index.html", "review/pr-5/preview.json", "review/pr-5/items/big.gif"}
    assert {path: blob for path, blob in after.items() if path in before} == before
    size = int(sh("git", "-C", str(remote), "cat-file", "-s", after["review/pr-5/items/big.gif"]))
    assert size == 3 * 1024 * 1024


def test_unpublish_removes_only_that_gallery(tmp_path: Path, clone):
    remote, _ = clone
    before = tree(remote)
    update_gh_pages("5", _build(tmp_path))

    update_gh_pages("5", None)

    assert tree(remote) == before
