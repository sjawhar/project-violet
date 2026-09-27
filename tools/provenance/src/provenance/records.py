"""Provenance sidecars: where they live, how they are validated, and how assets are found."""

import hashlib
import json
import os
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


def _scan(config: Config, directory: Path) -> tuple[list[Path], list[str]]:
    """Assets under a directory, plus problems that would otherwise hide files from the check:
    symlinked directories (never followed), dangling symlinks, and sidecars whose asset is gone."""
    assets: list[Path] = []
    problems: list[str] = []
    for dirpath, dirnames, filenames in os.walk(directory):
        base = Path(dirpath)
        for name in sorted(dirnames):
            if (base / name).is_symlink():
                problems.append(f"{config.display(base / name)}: symlinked directory; the check does not follow it, so move the files under the root")
        for name in sorted(filenames):
            path = base / name
            if path.is_symlink() and not path.exists():
                problems.append(f"{config.display(path)}: dangling symlink")
            elif name.endswith(SIDECAR_SUFFIX):
                if not path.with_name(name.removesuffix(SIDECAR_SUFFIX)).exists():
                    problems.append(f"{config.display(path)}: no asset '{name.removesuffix(SIDECAR_SUFFIX)}' beside it; delete or move the sidecar")
            elif config.is_asset(path):
                assets.append(path)
    return sorted(assets), problems


def discover_assets(config: Config, paths: list[Path]) -> tuple[list[Path], list[str]]:
    """Assets under every configured root, or under the given absolute paths when there are any, plus scan problems.

    A sidecar path stands for its asset. Each asset appears once.
    """
    directories = [config.root / root for root in config.roots if (config.root / root).is_dir()] if not paths else []
    assets: list[Path] = []
    for path in paths:
        if path.name.endswith(SIDECAR_SUFFIX):
            path = path.with_name(path.name.removesuffix(SIDECAR_SUFFIX))
        if path.is_dir():
            directories.append(path)
        elif path.is_file():
            assets.append(path)
        else:
            raise ProvenanceError(f"{config.display(path)}: no such file or directory")
    problems: list[str] = []
    for directory in directories:
        found, scan_problems = _scan(config, directory)
        assets += found
        problems += scan_problems
    return list(dict.fromkeys(assets)), list(dict.fromkeys(problems))


class Checker:
    """Checks assets and, transitively, the records of every input they were made from.

    Each asset is checked once; `problems` accumulates everything found, in order.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self.problems: list[str] = []
        self.records: dict[Path, Record] = {}
        self._checked: set[Path] = set()
        self._visiting: set[Path] = set()

    def check(self, asset: Path) -> Record | None:
        """Check the asset and its inputs; return its record when the asset's own record is sound."""
        if asset in self._checked:
            return self.records.get(asset)
        self._checked.add(asset)
        self._visiting.add(asset)
        problems, record = check_asset(self.config, asset)
        self.problems += problems
        if record is not None:
            self.records[asset] = record
            if record["origin"] != "human":
                self._check_inputs(asset, record)
        self._visiting.discard(asset)
        return record

    def _check_inputs(self, asset: Path, record: Record) -> None:
        sidecar = self.config.display(sidecar_for(asset))
        for index, item in enumerate(record["generator"]["inputs"]):
            where = f"{sidecar}: $.generator.inputs[{index}]: {item['path']}"
            path = self.config.root / item["path"]
            if path in self._visiting:
                self.problems.append(f"{where} leads back to this asset")
                continue
            if not path.is_file():
                self.problems.append(f"{where} does not exist")
                continue
            input_record = self.check(path)
            if input_record is None:
                self.problems.append(f"{where} has no valid, current provenance record")
            elif input_record["sha256"] != item["sha256"]:
                self.problems.append(
                    f"{where} was {item['sha256']} when this asset was made, but its record now says "
                    f"{input_record['sha256']}; regenerate or re-record this asset"
                )
