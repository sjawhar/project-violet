import os
import subprocess
import threading
from pathlib import Path

import pytest

from preview.media import PreviewError
from preview.publish import update_gh_pages

IDENTITY = ("Preview Test", "preview@example.com")
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"}


def git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True, env={**os.environ, **GIT_ENV}).stdout


def tree(remote: Path) -> dict[str, str]:
    """path -> blob id of every file on the remote's gh-pages branch."""
    return {line.split("\t")[1]: line.split()[2] for line in git("-C", str(remote), "ls-tree", "-r", "gh-pages").splitlines()}


def head(remote: Path) -> str:
    return git("-C", str(remote), "rev-parse", "gh-pages").strip()


@pytest.fixture
def remote(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A bare remote whose gh-pages branch holds an unrelated site and an LFS rule that must not apply to galleries."""
    bare = tmp_path / "remote.git"
    git("init", "-q", "--bare", "-b", "master", str(bare))
    seed = tmp_path / "seed"
    git("init", "-q", "-b", "gh-pages", str(seed))
    (seed / "index.html").write_text("<p>2019 web build</p>")
    (seed / "Build").mkdir()
    (seed / "Build" / "game.data").write_bytes(b"\0" * 64)
    (seed / ".gitattributes").write_text("*.gif filter=lfs diff=lfs merge=lfs -text\n")
    (seed / "review" / "pr-3").mkdir(parents=True)  # another PR's gallery, which publishing pr-5 must not touch
    (seed / "review" / "pr-3" / "index.html").write_text("<p>pr 3</p>")
    git("-c", "filter.lfs.clean=cat", "-c", "filter.lfs.process=", "add", ".", cwd=seed)
    git("commit", "-q", "-m", "site", cwd=seed)
    git("push", "-q", str(bare), "gh-pages", cwd=seed)
    monkeypatch.setenv("PREVIEW_CACHE_DIR", str(tmp_path / "cache"))
    return bare


def _build(root: Path, name: str = "build", *, big: bytes | None = None) -> Path:
    build = root / name
    (build / "items").mkdir(parents=True)
    (build / "index.html").write_text(f"<p>{name}</p>")
    (build / "preview.json").write_text("{}")
    (build / "items" / "big.gif").write_bytes(big if big is not None else os.urandom(3 * 1024 * 1024))
    return build


def test_publishes_every_file_as_plain_blobs_and_touches_nothing_else(tmp_path: Path, remote: Path):
    before = tree(remote)
    big = os.urandom(3 * 1024 * 1024)

    commit = update_gh_pages("5", _build(tmp_path, big=big), remote=str(remote), identity=IDENTITY)

    after = tree(remote)
    assert commit == head(remote)
    assert set(after) == set(before) | {"review/pr-5/index.html", "review/pr-5/preview.json", "review/pr-5/items/big.gif"}
    assert {path: blob for path, blob in after.items() if path in before} == before
    blob = subprocess.run(["git", "-C", str(remote), "cat-file", "blob", after["review/pr-5/items/big.gif"]], capture_output=True, check=True).stdout
    assert blob == big  # the real bytes, not an LFS pointer, despite the branch's *.gif filter=lfs rule
    assert git("-C", str(remote), "log", "-1", "--format=%an <%ae>", "gh-pages").strip() == "Preview Test <preview@example.com>"


def test_republishing_an_unchanged_gallery_makes_no_commit(tmp_path: Path, remote: Path):
    build = _build(tmp_path)
    first = update_gh_pages("5", build, remote=str(remote), identity=IDENTITY)

    assert update_gh_pages("5", build, remote=str(remote), identity=IDENTITY) is None
    assert head(remote) == first


def test_unpublish_removes_only_that_gallery(tmp_path: Path, remote: Path):
    before = tree(remote)
    update_gh_pages("5", _build(tmp_path), remote=str(remote), identity=IDENTITY)

    update_gh_pages("5", None, remote=str(remote), identity=IDENTITY)

    assert tree(remote) == before


def test_a_rejected_push_does_not_block_the_next_publish(tmp_path: Path, remote: Path):
    hook = remote / "hooks" / "pre-receive"
    hook.write_text("#!/bin/sh\necho rejected by test >&2\nexit 1\n")
    hook.chmod(0o755)
    build = _build(tmp_path)

    with pytest.raises(PreviewError, match="rejected by test"):
        update_gh_pages("5", build, remote=str(remote), identity=IDENTITY)
    hook.unlink()

    commit = update_gh_pages("5", build, remote=str(remote), identity=IDENTITY)
    assert commit == head(remote)
    assert "review/pr-5/index.html" in tree(remote)


def test_concurrent_publishes_of_different_prs_all_arrive(tmp_path: Path, remote: Path):
    builds = {pr: _build(tmp_path, f"build-{pr}", big=os.urandom(1024)) for pr in ("21", "22", "23")}
    errors: list[BaseException] = []

    def publish(pr: str) -> None:
        try:
            update_gh_pages(pr, builds[pr], remote=str(remote), identity=IDENTITY)
        except BaseException as error:  # noqa: BLE001 - surfaced by the assertion below
            errors.append(error)

    threads = [threading.Thread(target=publish, args=(pr,)) for pr in builds]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert {f"review/pr-{pr}/index.html" for pr in builds} <= set(tree(remote))


def test_retries_when_gh_pages_moves_between_fetch_and_push(tmp_path: Path, remote: Path, monkeypatch: pytest.MonkeyPatch):
    import preview.publish as publish

    other = tmp_path / "other"
    git("clone", "-q", "-b", "gh-pages", str(remote), str(other))
    real_push = publish._push
    moved = []

    def push_after_someone_else(repo: Path, url: str, commit: str) -> bool:
        if not moved:
            (other / "unrelated.txt").write_text("someone else's change")
            git("add", "unrelated.txt", cwd=other)
            git("commit", "-q", "-m", "concurrent", cwd=other)
            git("push", "-q", "origin", "gh-pages", cwd=other)
            moved.append(True)
        return real_push(repo, url, commit)

    monkeypatch.setattr(publish, "_push", push_after_someone_else)

    update_gh_pages("5", _build(tmp_path, big=b"x"), remote=str(remote), identity=IDENTITY)

    assert {"unrelated.txt", "review/pr-5/index.html"} <= set(tree(remote))


def test_republishing_replaces_the_gallery_exactly(tmp_path: Path, remote: Path):
    build = _build(tmp_path, big=b"first")
    (build / "items" / "dropped.gif").write_bytes(b"only in the first build")
    update_gh_pages("5", build, remote=str(remote), identity=IDENTITY)
    (build / "items" / "dropped.gif").unlink()
    (build / "items" / "big.gif").write_bytes(b"second")

    update_gh_pages("5", build, remote=str(remote), identity=IDENTITY)

    published = {path for path in tree(remote) if path.startswith("review/pr-5/")}
    assert published == {"review/pr-5/index.html", "review/pr-5/preview.json", "review/pr-5/items/big.gif"}
    blob = subprocess.run(["git", "-C", str(remote), "cat-file", "blob", "gh-pages:review/pr-5/items/big.gif"], capture_output=True, check=True).stdout
    assert blob == b"second"
    assert "review/pr-3/index.html" in tree(remote)
