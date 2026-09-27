"""Text for Steam's "Pre-Generated AI Content" disclosure, built from provenance records."""

# Disclosure section -> record kinds, in display order.
SECTIONS = {
    "Art": ("image", "model3d"),
    "Audio": ("audio",),
    "Animation": ("animation",),
    "Text": ("text",),
    "Other": ("other",),
}


def _assets(count: int) -> str:
    return f"{count} asset" + ("" if count == 1 else "s")


def _model(generator: dict) -> str:
    version = f" {generator['model_version']}" if "model_version" in generator else ""
    return f"{generator['model']}{version} ({generator['provider']})"


def steam_report(records: list[dict]) -> str:
    """Markdown naming, per kind of content, the AI tools and models behind every non-human asset."""
    ai = [record for record in records if record["origin"] != "human"]
    if not ai:
        return "Violet contains no pre-generated AI content.\n"

    lines = [
        f"Violet contains content created with generative AI tools during development ({_assets(len(ai))}). "
        "By type, with the tools and models used:",
        "",
    ]
    for title, kinds in SECTIONS.items():
        generators = [record["generator"] for record in ai if record["kind"] in kinds]
        if not generators:
            continue
        tools = sorted({f"{g['tool']} {g['tool_version']}" for g in generators})
        models = sorted({_model(g) for g in generators})
        lines += [
            f"### {title} ({_assets(len(generators))})",
            "",
            f"- Tools: {', '.join(tools)}",
            f"- Models: {', '.join(models)}",
            "",
        ]
    return "\n".join(lines)
