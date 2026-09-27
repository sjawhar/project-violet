import hashlib
import subprocess
from pathlib import Path

import pytest

LFS_RULE = b"*.png filter=lfs diff=lfs merge=lfs -text\n"


def git(repo: Path, *args: str, stdin: bytes | None = None) -> str:
    return subprocess.run(["git", *args], cwd=repo, input=stdin, capture_output=True, check=True).stdout.decode()


@pytest.fixture
def git_repo(repo: Path) -> Path:
    git(repo, "init", "-q")
    return repo


def stage(repo: Path, path: str, content: bytes) -> None:
    """Stage content verbatim, bypassing clean filters, the way a commit made without git-lfs lands."""
    blob = git(repo, "hash-object", "-w", "--stdin", stdin=content).strip()
    git(repo, "update-index", "--add", "--cacheinfo", f"100644,{blob},{path}")


def pointer(content: bytes) -> bytes:
    return (
        "version https://git-lfs.github.com/spec/v1\n"
        f"oid sha256:{hashlib.sha256(content).hexdigest()}\n"
        f"size {len(content)}\n"
    ).encode()


BINARY = b"\x89PNG\r\n\x1a\n" + bytes(range(256)) * 16


def test_passes_without_any_lfs_rules_even_for_binaries(git_repo: Path, run):
    stage(git_repo, "game/art/hero.png", BINARY)

    code, _, err = run("lfs-check")

    assert code == 0, err


def test_fails_naming_a_file_that_matches_an_lfs_rule_but_is_a_regular_blob(git_repo: Path, run):
    stage(git_repo, ".gitattributes", LFS_RULE)
    stage(git_repo, "game/art/hero.png", BINARY)
    stage(git_repo, "game/art/scarf.png", pointer(b"scarf"))

    code, _, err = run("lfs-check")

    assert code != 0
    assert "game/art/hero.png" in err
    assert "game/art/scarf.png" not in err


def test_passes_when_every_matching_file_is_an_lfs_pointer(git_repo: Path, run):
    stage(git_repo, ".gitattributes", LFS_RULE)
    stage(git_repo, "game/art/hero.png", pointer(BINARY))
    stage(git_repo, "README.md", b"# not an LFS file\n")

    code, _, err = run("lfs-check")

    assert code == 0, err


@pytest.mark.parametrize(
    "content",
    [
        b"version https://git-lfs.github.com/spec/v1\noid sha256:" + b"a" * 64 + b"\n",  # no size
        b"version https://git-lfs.github.com/spec/v1\nsize 5\noid sha256:" + b"a" * 64 + b"\n",  # keys out of order
        b"version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 5\n",  # short oid
        b"oid sha256:" + b"a" * 64 + b"\nsize 5\n",  # no version line
    ],
)
def test_fails_on_a_malformed_pointer(git_repo: Path, run, content: bytes):
    stage(git_repo, ".gitattributes", LFS_RULE)
    stage(git_repo, "game/art/hero.png", content)

    code, _, err = run("lfs-check")

    assert code != 0
    assert "game/art/hero.png" in err


def test_fails_outside_a_git_repository(repo: Path, run):
    code, _, err = run("lfs-check")

    assert code != 0
    assert "git" in err
