"""Write provenance sidecars: a new record for an asset, or a human edit appended to an existing one."""

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from provenance.config import Config, ProvenanceError
from provenance.records import Record, check_asset, content_sha256, lfs_pointer_oid, load_record, schema_errors, sidecar_for

# Record field -> command-line flag, in the order fields appear in the sidecar.
GENERATOR_FLAGS = {
    "tool": "--tool",
    "tool_version": "--tool-version",
    "provider": "--provider",
    "model": "--model",
    "model_version": "--model-version",
    "prompt": "--prompt",
    "negative_prompt": "--negative-prompt",
    "seed": "--seed",
}
REQUIRED_GENERATOR_FIELDS = {
    "generated": ("tool", "tool_version", "provider", "model", "prompt"),
    "derived": ("tool", "tool_version"),
}


@dataclass
class RecordRequest:
    asset: Path
    kind: str
    origin: str
    license: str
    source_url: str | None = None
    authors: list[str] = field(default_factory=list)
    generator: dict[str, str | int] = field(default_factory=dict)
    """Only the generator fields that were given, in GENERATOR_FLAGS order."""
    params: dict[str, str] = field(default_factory=dict)
    inputs: list[Path] = field(default_factory=list)


def _timestamp(now: datetime) -> str:
    return now.astimezone(UTC).isoformat(timespec="seconds")


def _refuse_pointer(config: Config, path: Path) -> None:
    if lfs_pointer_oid(path) is not None:
        raise ProvenanceError(f"{config.display(path)} is a Git LFS pointer, not the asset itself; run `git lfs pull` first")


def _input_entry(config: Config, path: Path) -> dict[str, str]:
    if not path.is_file():
        raise ProvenanceError(f"--input {path}: no such file")
    if not path.is_relative_to(config.root):
        raise ProvenanceError(f"--input {path}: inputs must live inside the repository ({config.root})")
    return {"path": config.display(path), "sha256": content_sha256(path)}


def _generator(config: Config, request: RecordRequest) -> dict:
    missing = [GENERATOR_FLAGS[name] for name in REQUIRED_GENERATOR_FIELDS[request.origin] if name not in request.generator]
    if request.origin == "derived" and not request.inputs:
        missing.append("--input")
    if "model" in request.generator and "provider" not in request.generator:
        missing.append("--provider (with --model)")
    if missing:
        raise ProvenanceError(f"origin '{request.origin}' requires {', '.join(missing)}")
    return {**request.generator, "params": request.params, "inputs": [_input_entry(config, path) for path in request.inputs]}


def build_record(config: Config, request: RecordRequest, now: datetime) -> Record:
    if not request.asset.is_file():
        raise ProvenanceError(f"{config.display(request.asset)}: no such file")
    _refuse_pointer(config, request.asset)

    record: Record = {
        "schema_version": 1,
        "asset": request.asset.name,
        "sha256": content_sha256(request.asset),
        "kind": request.kind,
        "origin": request.origin,
        "created_at": _timestamp(now),
    }

    if request.origin == "human":
        stray = [GENERATOR_FLAGS[name] for name in request.generator]
        if request.params:
            stray.append("--param")
        if request.inputs:
            stray.append("--input")
        if stray:
            raise ProvenanceError(f"origin 'human' takes no generator flags, got {', '.join(stray)}")
        if not request.authors:
            raise ProvenanceError("origin 'human' requires at least one --author")
        record["authors"] = request.authors
    else:
        record["generator"] = _generator(config, request)
        if request.authors:
            record["authors"] = request.authors

    record["human_edits"] = []
    record["license"] = request.license
    if request.source_url is not None:
        record["source_url"] = request.source_url
    return record


def _write(config: Config, sidecar: Path, record: Record) -> None:
    problems = schema_errors(record)
    if problems:
        raise ProvenanceError(f"{config.display(sidecar)} would be invalid:\n  " + "\n  ".join(problems))
    sidecar.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_record(config: Config, request: RecordRequest, *, force: bool, now: datetime) -> Path:
    sidecar = sidecar_for(request.asset)
    if sidecar.exists() and not force:
        raise ProvenanceError(f"{config.display(sidecar)} already exists; pass --force to replace it")
    _write(config, sidecar, build_record(config, request, now))
    return sidecar


def add_human_edit(config: Config, asset: Path, *, by: str, description: str, now: datetime) -> Path:
    """Append a human edit to the asset's record and re-hash it; every other field is kept."""
    sidecar = sidecar_for(asset)
    if not asset.is_file():
        raise ProvenanceError(f"{config.display(asset)}: no such file")
    if not sidecar.is_file():
        raise ProvenanceError(f"{config.display(asset)}: no provenance record to edit; run `provenance record` first")
    _refuse_pointer(config, asset)
    record, problems = load_record(sidecar)
    if record is None:
        raise ProvenanceError(f"{config.display(sidecar)} is invalid:\n  " + "\n  ".join(problems))
    if record["asset"] != asset.name:
        # check_asset explains the mismatch in the same words `check` uses.
        raise ProvenanceError(check_asset(config, asset)[0][0])
    record["sha256"] = content_sha256(asset)
    record["human_edits"].append({"by": by, "description": description, "at": _timestamp(now)})
    _write(config, sidecar, record)
    return sidecar
