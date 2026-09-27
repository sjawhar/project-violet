"""Text for Steam's "Pre-Generated AI Content" disclosure, built from provenance records."""

from collections.abc import Callable

from provenance.config import ProvenanceError
from provenance.records import Record

# Disclosure section -> record kinds, in display order.
SECTIONS = {
    "Art": ("image", "model3d"),
    "Audio": ("audio",),
    "Animation": ("animation",),
    "Text": ("text",),
    "Other": ("other",),
}


class Lineage:
    """The generators behind each asset, following derived assets back through their inputs' records."""

    def __init__(self, lookup: Callable[[str], Record]) -> None:
        self._lookup = lookup
        self._done: dict[str, list[dict]] = {}
        self._visiting: set[str] = set()

    def ai_generators(self, path: str) -> list[dict]:
        """Every generator whose AI output went into the asset at path; empty when no AI was involved.

        Generated assets always involve AI. A derived asset does when its own generator names a model or
        when any of its inputs involves AI. Human assets never do.
        """
        if path in self._done:
            return self._done[path]
        if path in self._visiting:
            raise ProvenanceError(f"{path}: its inputs lead back to itself")
        self._visiting.add(path)
        record = self._lookup(path)
        found: list[dict] = []
        if record["origin"] != "human":
            generator = record["generator"]
            upstream = [g for item in generator["inputs"] for g in self.ai_generators(item["path"])]
            if record["origin"] == "generated" or "model" in generator or upstream:
                found = [generator, *upstream]
        self._visiting.discard(path)
        self._done[path] = found
        return found


def _assets(count: int) -> str:
    return f"{count} asset" + ("" if count == 1 else "s")


def _model(generator: dict) -> str:
    version = f" {generator['model_version']}" if "model_version" in generator else ""
    return f"{generator['model']}{version} ({generator['provider']})"


def steam_report(assets: dict[str, Record], lookup: Callable[[str], Record]) -> str:
    """Markdown naming, per kind of content, the AI tools and models behind the recorded assets.

    `assets` maps each recorded asset's repository path to its record; `lookup` finds the record for any
    path, including inputs outside the asset roots. Returns "" when no recorded asset involves AI.
    """
    lineage = Lineage(lookup)
    ai = {path: lineage.ai_generators(path) for path in assets}
    ai = {path: generators for path, generators in ai.items() if generators}
    if not ai:
        return ""

    lines = [f"The following content was created with generative AI tools during development ({_assets(len(ai))}):", ""]
    for title, kinds in SECTIONS.items():
        group = [generators for path, generators in ai.items() if assets[path]["kind"] in kinds]
        if not group:
            continue
        generators = [g for chain in group for g in chain]
        tools = sorted({f"{g['tool']} {g['tool_version']}" for g in generators})
        models = sorted({_model(g) for g in generators if "model" in g})
        lines += [
            f"### {title} ({_assets(len(group))})",
            "",
            f"- Tools: {', '.join(tools)}",
            f"- Models: {', '.join(models)}",
            "",
        ]
    return "\n".join(lines)
