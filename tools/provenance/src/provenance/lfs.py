"""Fail on files that .gitattributes routes through Git LFS but that were committed as regular blobs.

This reads the git index, not the working tree: a local checkout holds the real (smudged) files, while
what matters is whether the committed blob is a pointer. Attribute matching is delegated to
`git check-attr --cached`, so nested .gitattributes files and git's pattern rules apply exactly.
"""

import re
import subprocess
from pathlib import Path

from provenance.config import ProvenanceError

# https://github.com/git-lfs/git-lfs/blob/main/docs/spec.md
POINTER_MAX_BYTES = 1024
POINTER_VERSIONS = {"https://git-lfs.github.com/spec/v1", "https://hawser.github.com/spec/v1"}
KEY = re.compile(r"[a-z0-9.-]+")
OID = re.compile(r"sha256:[0-9a-f]{64}")
SIZE = re.compile(r"0|[1-9][0-9]*")


def is_pointer(data: bytes) -> bool:
    if len(data) >= POINTER_MAX_BYTES or not data.endswith(b"\n"):
        return False
    try:
        lines = data.decode("utf-8").removesuffix("\n").split("\n")
    except UnicodeDecodeError:
        return False
    pairs = [line.partition(" ") for line in lines]
    if any(not sep or not KEY.fullmatch(key) or "\r" in value for key, sep, value in pairs):
        return False
    (first_key, _, version), rest = pairs[0], pairs[1:]
    if first_key != "version" or version not in POINTER_VERSIONS:
        return False
    keys = [key for key, _, _ in rest]
    if keys != sorted(set(keys)):
        return False
    values = {key: value for key, _, value in rest}
    return OID.fullmatch(values.get("oid", "")) is not None and SIZE.fullmatch(values.get("size", "")) is not None


def _git(root: Path, *args: str, stdin: bytes | None = None) -> bytes:
    try:
        result = subprocess.run(["git", *args], cwd=root, input=stdin, capture_output=True, check=True)
    except subprocess.CalledProcessError as error:
        raise ProvenanceError(f"git {args[0]} failed in {root}: {error.stderr.decode().strip()}") from error
    return result.stdout


def _nul_fields(data: bytes) -> list[str]:
    return data.decode("utf-8").split("\0")[:-1]


def lfs_paths(root: Path) -> list[str]:
    """Tracked paths whose filter attribute is lfs, relative to root."""
    paths = _nul_fields(_git(root, "ls-files", "-z"))
    if not paths:
        return []
    fields = _nul_fields(_git(root, "check-attr", "--cached", "-z", "--stdin", "filter", stdin="\0".join(paths).encode() + b"\0"))
    triples = zip(fields[0::3], fields[1::3], fields[2::3], strict=True)
    return [path for path, _, value in triples if value == "lfs"]


def _read_blobs(root: Path, blob_ids: list[str]) -> dict[str, bytes]:
    """Contents of the given blobs, except those too large to be pointers (mapped to b'')."""
    if not blob_ids:
        return {}
    request = "".join(f"{blob}\n" for blob in blob_ids).encode()
    sizes = {}
    for line in _git(root, "cat-file", "--batch-check=%(objectname) %(objectsize)", stdin=request).decode().splitlines():
        blob, size = line.split()
        sizes[blob] = int(size)
    small = [blob for blob in blob_ids if sizes[blob] < POINTER_MAX_BYTES]
    contents = {blob: b"" for blob in blob_ids if blob not in small}
    output = _git(root, "cat-file", "--batch", stdin="".join(f"{blob}\n" for blob in small).encode()) if small else b""
    offset = 0
    for blob in small:
        header_end = output.index(b"\n", offset)
        size = int(output[offset:header_end].split()[2])
        contents[blob] = output[header_end + 1 : header_end + 1 + size]
        offset = header_end + 1 + size + 1
    return contents


def lfs_check(root: Path) -> list[str]:
    """Problems, one per tracked file that matches filter=lfs but whose staged blob is not a pointer."""
    paths = lfs_paths(root)
    if not paths:
        return []
    staged: dict[str, str] = {}
    for entry in _nul_fields(_git(root, "ls-files", "-s", "-z", "--", *paths)):
        meta, _, path = entry.partition("\t")
        staged[path] = meta.split()[1]
    contents = _read_blobs(root, sorted(set(staged.values())))
    return [
        f"{path}: matches a filter=lfs rule in .gitattributes but is committed as a regular blob, not an LFS pointer; "
        f"with git-lfs installed, run `git add --renormalize {path}`"
        for path, blob in sorted(staged.items())
        if not is_pointer(contents[blob])
    ]
