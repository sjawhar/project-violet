"""Build and write the provenance sidecar for one asset."""

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from provenance.config import Config, ProvenanceError
from provenance.records import schema_errors, sha256_file, sidecar_for

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
REQUIRED_GENERATOR_FIELDS = ("tool", "tool_version", "provider", "model", "prompt")


@dataclass
class RecordRequest:
    asset: Path
    kind: str
    origin: str
    license: str
    source_url: str | None = None
    authors: list[str] = field(default_factory=list)
    generator: dict[str, str | int] = field(default_factory=dict)
    """Only the generator fields that were given."""
    params: dict[str, str] = field(default_factory=dict)
    inputs: list[Path] = field(default_factory=list)
    human_edits: list[tuple[str, str]] = field(default_factory=list)
    """(by, description) pairs."""


def _input_entry(config: Config, path: Path) -> dict[str, str]:
    if not path.is_file():
        raise ProvenanceError(f"--input {path}: no such file")
    try:
        relative = path.relative_to(config.root)
    except ValueError:
        raise ProvenanceError(f"--input {path}: inputs must live inside the repository ({config.root})") from None
    return {"path": relative.as_posix(), "sha256": sha256_file(path)}


def _generator(config: Config, request: RecordRequest) -> dict:
    missing = [GENERATOR_FLAGS[name] for name in REQUIRED_GENERATOR_FIELDS if name not in request.generator]
    if missing:
        raise ProvenanceError(f"origin '{request.origin}' requires {', '.join(missing)}")
    generator = {name: request.generator[name] for name in GENERATOR_FLAGS if name in request.generator}
    generator["params"] = request.params
    generator["inputs"] = [_input_entry(config, path) for path in request.inputs]
    return generator


def build_record(config: Config, request: RecordRequest, now: datetime) -> dict:
    if not request.asset.is_file():
        raise ProvenanceError(f"{config.display(request.asset)}: no such file")

    created_at = now.astimezone(UTC).isoformat(timespec="seconds")
    record: dict = {
        "schema_version": 1,
        "asset": request.asset.name,
        "sha256": sha256_file(request.asset),
        "kind": request.kind,
        "origin": request.origin,
        "created_at": created_at,
    }

    if request.origin == "human":
        stray = [GENERATOR_FLAGS[name] for name in request.generator]
        stray += ["--param"] * bool(request.params) + ["--input"] * bool(request.inputs)
        if stray:
            raise ProvenanceError(f"origin 'human' takes no generator flags, got {', '.join(stray)}")
        if not request.authors:
            raise ProvenanceError("origin 'human' requires at least one --author")
        record["authors"] = request.authors
    else:
        record["generator"] = _generator(config, request)
        if request.authors:
            record["authors"] = request.authors

    record["human_edits"] = [{"by": by, "description": description, "at": created_at} for by, description in request.human_edits]
    record["license"] = request.license
    if request.source_url is not None:
        record["source_url"] = request.source_url

    problems = schema_errors(record)
    if problems:
        raise ProvenanceError("the record would be invalid:\n  " + "\n  ".join(problems))
    return record


def write_record(config: Config, request: RecordRequest, *, force: bool, now: datetime) -> Path:
    sidecar = sidecar_for(request.asset)
    if sidecar.exists() and not force:
        raise ProvenanceError(f"{config.display(sidecar)} already exists; pass --force to replace it")
    record = build_record(config, request, now)
    sidecar.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return sidecar
