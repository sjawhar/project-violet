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


def stage(repo: Path, path: str, content: bytes, mode: str = "100644") -> None:
    """Stage content verbatim, bypassing clean filters, the way a commit made without git-lfs lands."""
    blob = git(repo, "hash-object", "-w", "--stdin", stdin=content).strip()
    git(repo, "update-index", "--add", "--cacheinfo", f"{mode},{blob},{path}")


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


def test_fails_naming_only_the_matching_files_committed_as_regular_blobs(git_repo: Path, run):
    stage(git_repo, ".gitattributes", LFS_RULE)
    stage(git_repo, "game/art/hero.png", BINARY)
    stage(git_repo, "game/art/scarf.png", pointer(b"scarf"))
    stage(git_repo, "game/art/cloak.png", pointer(b"cloak"))
    stage(git_repo, "game/art/tiny.png", b"not a pointer, just small")
    stage(git_repo, "game/art/boots.png", pointer(b"boots"))

    code, _, err = run("lfs-check")

    assert code != 0
    assert "game/art/hero.png" in err
    assert "game/art/tiny.png" in err
    for fine in ("scarf.png", "cloak.png", "boots.png"):
        assert fine not in err


def test_passes_when_every_matching_file_is_an_lfs_pointer(git_repo: Path, run):
    stage(git_repo, ".gitattributes", LFS_RULE)
    stage(git_repo, "game/art/hero.png", pointer(BINARY))
    stage(git_repo, "game/art/scarf.png", pointer(b"scarf"))
    stage(git_repo, "README.md", b"# not an LFS file\n")

    code, _, err = run("lfs-check")

    assert code == 0, err


def test_skips_what_git_lfs_itself_never_converts(git_repo: Path, run):
    """Empty files, symlinks, and submodules match the rule but are never stored as pointers."""
    stage(git_repo, ".gitattributes", b"*.png filter=lfs\nvendor filter=lfs\n")
    stage(git_repo, "game/art/empty.png", b"")
    stage(git_repo, "game/art/link.png", b"empty.png", mode="120000")
    git(git_repo, "update-index", "--add", "--cacheinfo", f"160000,{'a' * 40},vendor")

    code, _, err = run("lfs-check")

    assert code == 0, err


def test_treats_file_names_literally(git_repo: Path, run):
    stage(git_repo, ".gitattributes", LFS_RULE)
    stage(git_repo, ":magic.png", BINARY)
    stage(git_repo, "a[1].png", pointer(b"bracket"))
    stage(git_repo, "a1.png", b"-filter excludes this one\n")
    stage(git_repo, ".gitattributes", LFS_RULE + b"a1.png -filter\n")

    code, _, err = run("lfs-check")

    assert code != 0
    assert ":magic.png" in err
    assert "a1.png" not in err.replace("a[1].png", "")


@pytest.mark.parametrize(
    "content",
    [
        b"version https://git-lfs.github.com/spec/v1\noid sha256:" + b"a" * 64 + b"\n",  # no size
        b"version https://git-lfs.github.com/spec/v1\nsize 5\noid sha256:" + b"a" * 64 + b"\n",  # keys out of order
        b"version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 5\n",  # short oid
        b"version https://example.com/lfs/v9\noid sha256:" + b"a" * 64 + b"\nsize 5\n",  # unknown version
        b"version https://git-lfs.github.com/spec/v1\noid sha256:" + b"a" * 64 + b"\nsize 5",  # no final newline
        b"version https://git-lfs.github.com/spec/v1\r\noid sha256:" + b"a" * 64 + b"\r\nsize 5\r\n",  # CRLF
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
