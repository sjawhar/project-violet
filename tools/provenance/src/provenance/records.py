"""Provenance sidecars: where they live, how they are validated, and how assets are found."""

import hashlib
import json
from functools import cache
from pathlib import Path

from jsonschema import Draft202012Validator

from provenance.config import SIDECAR_SUFFIX, Config, ProvenanceError

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schema" / "provenance-v1.json"


@cache
def validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)


def sidecar_for(asset: Path) -> Path:
    return asset.with_name(asset.name + SIDECAR_SUFFIX)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def schema_errors(record: object) -> list[str]:
    """Schema violations as '<json path>: <message>', one per violation."""
    errors = sorted(validator().iter_errors(record), key=lambda error: (error.json_path, error.message))
    # jsonschema's "not" message repeats the whole offending value; the path already names it.
    return [f"{error.json_path}: {'is not allowed here' if error.validator == 'not' else error.message}" for error in errors]


def load_record(sidecar: Path) -> tuple[dict | None, list[str]]:
    """Parse and schema-validate a sidecar; return the record when valid, else the problems."""
    try:
        record = json.loads(sidecar.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        return None, [f"not valid JSON: {error}"]
    problems = schema_errors(record)
    return (None if problems else record), problems


def check_asset(config: Config, asset: Path) -> list[str]:
    """Problems with one asset's sidecar, each prefixed with the file it concerns."""
    sidecar = sidecar_for(asset)
    if not sidecar.is_file():
        return [f"{config.display(asset)}: no provenance record ({config.display(sidecar)} is missing)"]

    record, problems = load_record(sidecar)
    if record is None:
        return [f"{config.display(sidecar)}: {problem}" for problem in problems]

    if record["asset"] != asset.name:
        return [f"{config.display(sidecar)}: $.asset: names '{record['asset']}', but the sidecar belongs to '{asset.name}'"]

    actual = sha256_file(asset)
    if record["sha256"] != actual:
        return [
            f"{config.display(asset)}: sha256 mismatch: {config.display(sidecar)} records {record['sha256']}, "
            f"the file hashes to {actual}; re-record it"
        ]
    return []


def assets_under(config: Config, directory: Path) -> list[Path]:
    return sorted(path for path in directory.rglob("*") if path.is_file() and config.is_asset(path))


def discover_assets(config: Config, paths: list[Path]) -> list[Path]:
    """Assets under every configured root, or under the given paths when there are any."""
    if not paths:
        return [asset for root in config.roots if (config.root / root).is_dir() for asset in assets_under(config, config.root / root)]

    assets: list[Path] = []
    for path in paths:
        if path.is_dir():
            assets.extend(assets_under(config, path))
        elif path.is_file():
            assets.append(path)
        else:
            raise ProvenanceError(f"{config.display(path)}: no such file or directory")
    return assets
