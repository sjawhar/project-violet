"""Provenance sidecars: where they live, how they are validated, and how assets are found."""

import hashlib
import json
from functools import cache
from importlib.resources import files
from pathlib import Path

from jsonschema import Draft202012Validator

from provenance.config import SIDECAR_SUFFIX, Config, ProvenanceError
from provenance.lfs import POINTER_MAX_BYTES, pointer_oid

Record = dict
"""A sidecar's JSON object, valid against schema/provenance-v1.json."""


@cache
def validator() -> Draft202012Validator:
    schema = json.loads(files("provenance").joinpath("schema/provenance-v1.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)


def sidecar_for(asset: Path) -> Path:
    return asset.with_name(asset.name + SIDECAR_SUFFIX)


def lfs_pointer_oid(path: Path) -> str | None:
    """The content sha256 when the file on disk is a Git LFS pointer (as in CI, which skips LFS downloads)."""
    return pointer_oid(path.read_bytes()) if path.stat().st_size < POINTER_MAX_BYTES else None


def content_sha256(path: Path) -> str:
    """sha256 of the asset's content; for a Git LFS pointer file, the oid of the content it points to."""
    oid = lfs_pointer_oid(path)
    if oid is not None:
        return oid
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def schema_errors(record: object) -> list[str]:
    """Schema violations as '<json path>: <message>', one per violation."""
    errors = sorted(validator().iter_errors(record), key=lambda error: (error.json_path, error.message))
    # jsonschema's "not" message repeats the whole offending value; the path already names it.
    return [f"{error.json_path}: {'is not allowed here' if error.validator == 'not' else error.message}" for error in errors]


def load_record(sidecar: Path) -> tuple[Record | None, list[str]]:
    """Parse and schema-validate a sidecar; return the record when valid, else the problems."""
    try:
        record = json.loads(sidecar.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        return None, [f"not valid JSON: {error}"]
    problems = schema_errors(record)
    return (None if problems else record), problems


def check_asset(config: Config, asset: Path) -> tuple[list[str], Record | None]:
    """Problems with one asset's sidecar, each prefixed with the file it concerns, and the record when it is sound."""
    sidecar = sidecar_for(asset)
    if not sidecar.is_file():
        return [f"{config.display(asset)}: no provenance record ({config.display(sidecar)} is missing)"], None

    record, problems = load_record(sidecar)
    if record is None:
        return [f"{config.display(sidecar)}: {problem}" for problem in problems], None

    if record["asset"] != asset.name:
        return [f"{config.display(sidecar)}: $.asset: names '{record['asset']}', but the sidecar belongs to '{asset.name}'"], None

    actual = content_sha256(asset)
    if record["sha256"] != actual:
        return [
            f"{config.display(asset)}: sha256 mismatch: {config.display(sidecar)} records {record['sha256']}, "
            f"the file's content hashes to {actual}. If a person edited it, run `provenance edit`; "
            "if it was regenerated, run `provenance record --force`"
        ], None
    return [], record


def missing_roots(config: Config) -> list[str]:
    return [root for root in config.roots if not (config.root / root).is_dir()]


def _assets_under(config: Config, directory: Path) -> list[Path]:
    return sorted(path for path in directory.rglob("*") if path.is_file() and config.is_asset(path))


def discover_assets(config: Config, paths: list[Path]) -> list[Path]:
    """Assets under every configured root, or under the given absolute paths when there are any.

    A sidecar path stands for its asset. Each asset appears once.
    """
    if not paths:
        return [asset for root in config.roots if (config.root / root).is_dir() for asset in _assets_under(config, config.root / root)]

    assets: list[Path] = []
    for path in paths:
        if path.name.endswith(SIDECAR_SUFFIX):
            path = path.with_name(path.name.removesuffix(SIDECAR_SUFFIX))
        if path.is_dir():
            assets.extend(_assets_under(config, path))
        elif path.is_file():
            assets.append(path)
        else:
            raise ProvenanceError(f"{config.display(path)}: no such file or directory")
    return list(dict.fromkeys(assets))
