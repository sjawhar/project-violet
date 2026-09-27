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
    """Directory name (lower case) -> extensions that are assets only inside such a directory."""

    def is_asset(self, path: Path) -> bool:
        if path.name.endswith(SIDECAR_SUFFIX):
            return False
        extension = path.suffix.lower().removeprefix(".")
        if extension in self.extensions:
            return True
        within = path.relative_to(self.root) if path.is_relative_to(self.root) else path
        directories = {part.lower() for part in within.parent.parts}
        return any(
            extension in extensions and directory in directories
            for directory, extensions in self.directory_extensions.items()
        )

    def display(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix() if path.is_relative_to(self.root) else str(path)


def find_config(start: Path) -> Path:
    for directory in (start, *start.parents):
        candidate = directory / CONFIG_NAME
        if candidate.is_file():
            return candidate
    raise ProvenanceError(f"{CONFIG_NAME} not found in {start} or any parent directory")


def _names(value: object, where: str, what: str) -> frozenset[str]:
    """A list of plain names: non-empty, and free of '/' and a leading '.', which could never match."""
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ProvenanceError(f"{where} must be a list of strings")
    for item in value:
        if not item or "/" in item or item.startswith("."):
            raise ProvenanceError(f"{where}: {item!r} is not a valid {what} (no dots, no slashes)")
    return frozenset(item.lower() for item in value)


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

    roots = data["roots"]
    if not isinstance(roots, list) or not all(isinstance(root, str) and root and not Path(root).is_absolute() for root in roots):
        raise ProvenanceError(f"{path}: roots must be a list of relative paths")

    directory_extensions = data.get("directory_extensions", {})
    if not isinstance(directory_extensions, dict):
        raise ProvenanceError(f"{path}: directory_extensions must be a table")
    _names(list(directory_extensions), f"{path}: directory_extensions", "directory name")

    return Config(
        root=path.parent,
        roots=tuple(roots),
        extensions=_names(data["extensions"], f"{path}: extensions", "extension"),
        directory_extensions={
            directory.lower(): _names(extensions, f"{path}: directory_extensions.{directory}", "extension")
            for directory, extensions in directory_extensions.items()
        },
    )
