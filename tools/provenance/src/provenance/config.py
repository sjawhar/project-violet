"""Load provenance.toml, which says which files under which roots are assets."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

CONFIG_NAME = "provenance.toml"
SIDECAR_SUFFIX = ".provenance.json"


class ProvenanceError(Exception):
    """A failure whose message is shown to the user as-is."""


@dataclass(frozen=True)
class Config:
    root: Path
    """Directory holding provenance.toml; asset roots and display paths are relative to it."""
    roots: tuple[str, ...]
    extensions: frozenset[str]
    directory_extensions: dict[str, frozenset[str]]

    def is_asset(self, path: Path) -> bool:
        if path.name.endswith(SIDECAR_SUFFIX):
            return False
        extension = path.suffix.lower().removeprefix(".")
        if extension in self.extensions:
            return True
        try:
            directories = path.relative_to(self.root).parent.parts
        except ValueError:
            directories = path.parent.parts
        return any(
            extension in extensions and directory in directories
            for directory, extensions in self.directory_extensions.items()
        )

    def display(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return str(path)


def find_config(start: Path) -> Path:
    for directory in (start, *start.parents):
        candidate = directory / CONFIG_NAME
        if candidate.is_file():
            return candidate
    raise ProvenanceError(f"{CONFIG_NAME} not found in {start} or any parent directory")


def _string_list(value: object, where: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ProvenanceError(f"{where} must be a list of non-empty strings")
    return value


def load_config(path: Path) -> Config:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise ProvenanceError(f"{path}: invalid TOML: {error}") from error

    unknown = set(data) - {"roots", "extensions", "directory_extensions"}
    if unknown:
        raise ProvenanceError(f"{path}: unknown keys: {', '.join(sorted(unknown))}")
    for key in ("roots", "extensions"):
        if key not in data:
            raise ProvenanceError(f"{path}: missing required key '{key}'")

    directory_extensions = data.get("directory_extensions", {})
    if not isinstance(directory_extensions, dict):
        raise ProvenanceError(f"{path}: directory_extensions must be a table")

    return Config(
        root=path.parent,
        roots=tuple(_string_list(data["roots"], f"{path}: roots")),
        extensions=frozenset(e.lower() for e in _string_list(data["extensions"], f"{path}: extensions")),
        directory_extensions={
            directory: frozenset(e.lower() for e in _string_list(exts, f"{path}: directory_extensions.{directory}"))
            for directory, exts in directory_extensions.items()
        },
    )
