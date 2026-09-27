"""Text for Steam's "Pre-Generated AI Content" disclosure, built from provenance records."""

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

    def __init__(self, records: dict[str, Record]) -> None:
        """`records` maps the repository path of every checked asset and input to its record."""
        self._records = records
        self._done: dict[str, list[dict]] = {}

    def ai_generators(self, path: str) -> list[dict]:
        """Every generator whose AI output went into the asset at path; empty when no AI was involved.

        Generated assets always involve AI. A derived asset does when its generator names a model (a
        derived record without one states "model": null) or when any of its inputs involves AI. Human
        assets never do.
        """
        if path in self._done:
            return self._done[path]
        record = self._records[path]
        found: list[dict] = []
        if record["origin"] != "human":
            generator = record["generator"]
            upstream = [g for item in generator["inputs"] for g in self.ai_generators(item["path"])]
            if record["origin"] == "generated" or generator["model"] is not None or upstream:
                found = [generator, *upstream]
        self._done[path] = found
        return found


def _assets(count: int) -> str:
    return f"{count} asset" + ("" if count == 1 else "s")


def _model(generator: dict) -> str:
    version = f" {generator['model_version']}" if "model_version" in generator else ""
    return f"{generator['model']}{version} ({generator['provider']})"


def steam_report(assets: list[str], records: dict[str, Record]) -> str:
    """Markdown naming, per kind of content, the AI tools and models behind the recorded assets.

    `assets` lists the repository paths the disclosure covers; `records` maps those paths and every input
    they were made from to its record. Returns "" when no listed asset involves AI.
    """
    lineage = Lineage(records)
    ai = {path: lineage.ai_generators(path) for path in assets}
    ai = {path: generators for path, generators in ai.items() if generators}
    if not ai:
        return ""

    lines = [f"The following content was created with generative AI tools during development ({_assets(len(ai))}):", ""]
    for title, kinds in SECTIONS.items():
        group = [generators for path, generators in ai.items() if records[path]["kind"] in kinds]
        if not group:
            continue
        generators = [g for chain in group for g in chain]
        tools = sorted({f"{g['tool']} {g['tool_version']}" for g in generators})
        models = sorted({_model(g) for g in generators if g["model"] is not None})
        lines += [
            f"### {title} ({_assets(len(group))})",
            "",
            f"- Tools: {', '.join(tools)}",
            f"- Models: {', '.join(models)}",
            "",
        ]
    return "\n".join(lines)
