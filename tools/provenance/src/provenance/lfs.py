"""Git LFS pointers: recognising them, and failing on files that should be pointers but are not.

`lfs_check` reads the git index, not the working tree: a local checkout holds the real (smudged)
files, while what matters is whether the committed blob is a pointer. In a jj colocated repository the
index holds the parent of the working-copy commit. Attribute matching is delegated to
`git check-attr --cached`, so nested .gitattributes files and git's pattern rules apply exactly.
"""

import os
import re
import subprocess
from pathlib import Path

from provenance.config import ProvenanceError

# https://github.com/git-lfs/git-lfs/blob/main/docs/spec.md
POINTER_MAX_BYTES = 1024
POINTER_VERSIONS = {"https://git-lfs.github.com/spec/v1", "https://hawser.github.com/spec/v1"}
KEY = re.compile(r"[a-z0-9.-]+")
OID = re.compile(r"sha256:([0-9a-f]{64})")
SIZE = re.compile(r"0|[1-9][0-9]*")
# git-lfs converts only regular files; symlinks (120000) and submodules (160000) never become pointers.
REGULAR_FILE_MODES = {"100644", "100755"}


def pointer_oid(data: bytes) -> str | None:
    """The sha256 a Git LFS pointer file refers to, or None when the data is not a pointer."""
    if not data or len(data) >= POINTER_MAX_BYTES or not data.endswith(b"\n"):
        return None
    try:
        lines = data.decode("utf-8").removesuffix("\n").split("\n")
    except UnicodeDecodeError:
        return None
    pairs = [line.partition(" ") for line in lines]
    if any(not sep or not KEY.fullmatch(key) or "\r" in value for key, sep, value in pairs):
        return None
    (first_key, _, version), rest = pairs[0], pairs[1:]
    if first_key != "version" or version not in POINTER_VERSIONS:
        return None
    keys = [key for key, _, _ in rest]
    if keys != sorted(set(keys)):
        return None
    values = {key: value for key, _, value in rest}
    oid = OID.fullmatch(values.get("oid", ""))
    return oid.group(1) if oid and SIZE.fullmatch(values.get("size", "")) else None


def is_pointer(data: bytes) -> bool:
    # git-lfs stores an empty file as-is: the spec treats it as its own pointer.
    return data == b"" or pointer_oid(data) is not None


def _git(root: Path, *args: str, stdin: bytes | None = None) -> bytes:
    try:
        result = subprocess.run(["git", *args], cwd=root, input=stdin, capture_output=True, check=True)
    except FileNotFoundError as error:
        raise ProvenanceError("lfs-check needs git on PATH") from error
    except subprocess.CalledProcessError as error:
        raise ProvenanceError(f"git {args[0]} failed in {root}: {error.stderr.decode().strip()}") from error
    return result.stdout


def _nul_fields(data: bytes) -> list[str]:
    return [os.fsdecode(field) for field in data.split(b"\0")[:-1]]


def _nul_join(items: list[str]) -> bytes:
    return b"".join(os.fsencode(item) + b"\0" for item in items)


def _staged_regular_files(root: Path) -> list[tuple[str, str, str]]:
    """(path, stage, blob id) for every regular file in the index, merge stages included."""
    entries = []
    for entry in _nul_fields(_git(root, "ls-files", "--stage", "-z")):
        meta, _, path = entry.partition("\t")
        mode, blob, stage = meta.split()
        if mode in REGULAR_FILE_MODES:
            entries.append((path, stage, blob))
    return entries


def _lfs_filtered(root: Path, paths: list[str]) -> set[str]:
    output = _nul_fields(_git(root, "check-attr", "--cached", "-z", "--stdin", "filter", stdin=_nul_join(paths)))
    return {path for path, _, value in zip(output[0::3], output[1::3], output[2::3], strict=True) if value == "lfs"}


def _small_blobs(root: Path, blob_ids: list[str]) -> dict[str, bytes]:
    """Contents of the blobs small enough to be pointers; larger blobs are omitted."""
    request = "".join(f"{blob}\n" for blob in blob_ids).encode()
    small = []
    for line in _git(root, "cat-file", "--batch-check=%(objectname) %(objectsize)", stdin=request).decode().splitlines():
        blob, size = line.split()
        if int(size) < POINTER_MAX_BYTES:
            small.append(blob)
    if not small:
        return {}
    output = _git(root, "cat-file", "--batch", stdin="".join(f"{blob}\n" for blob in small).encode())
    contents, offset = {}, 0
    for blob in small:
        header_end = output.index(b"\n", offset)
        length = int(output[offset:header_end].split()[2])
        contents[blob] = output[header_end + 1 : header_end + 1 + length]
        offset = header_end + 1 + length + 1  # the blob is followed by a newline
    return contents


def lfs_check(root: Path) -> list[str]:
    """Problems, one per staged regular file whose LFS state contradicts .gitattributes: a file matching
    filter=lfs that is not a pointer, or a pointer that no filter=lfs rule covers (checkouts would get the
    pointer text; `git lfs fsck --pointers` flags the same thing)."""
    staged = _staged_regular_files(root)
    if not staged:
        return []
    lfs_paths = _lfs_filtered(root, sorted({path for path, _, _ in staged}))
    contents = _small_blobs(root, sorted({blob for _, _, blob in staged}))
    problems = []
    for path, stage, blob in sorted(staged):
        where = f"{path}{f' (merge stage {stage})' if stage != '0' else ''}"
        content = contents.get(blob)
        if path in lfs_paths and (content is None or not is_pointer(content)):
            problems.append(
                f"{where}: matches a filter=lfs rule in .gitattributes but is committed as a regular blob, "
                f"not an LFS pointer; with git-lfs installed, run `git add --renormalize {path}`"
            )
        elif path not in lfs_paths and content is not None and pointer_oid(content) is not None:
            problems.append(
                f"{where}: is a Git LFS pointer, but no filter=lfs rule in .gitattributes covers it, so checkouts "
                "get the pointer text; add a rule for it or commit the real file"
            )
    return problems
