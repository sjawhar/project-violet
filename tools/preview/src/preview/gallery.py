"""The review gallery page for one PR."""

from html import escape

STYLE = """
body { margin: 0; padding: 1rem; background: #111116; color: #e5e5ea; font: 15px/1.45 system-ui, sans-serif; }
h1 { font-size: 1.25rem; margin: 0 0 1rem; }
.sheet img { max-width: 100%; border-radius: 6px; }
.items { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fill, minmax(min(100%, 420px), 1fr)); margin-top: 1rem; }
.item { background: #1b1b22; border-radius: 8px; padding: .75rem; }
.item h2 { font-size: 1rem; margin: 0 0 .5rem; word-break: break-all; }
.item img, .item video { width: 100%; border-radius: 4px; background: #000; }
.item audio { width: 100%; margin-top: .5rem; }
.provenance { margin: .5rem 0 0; font-size: .85rem; color: #b9b9c6; }
.provenance dt { font-weight: 600; float: left; clear: left; margin-right: .4rem; }
.provenance dd { margin: 0 0 .15rem; white-space: pre-wrap; }
.missing { color: #f59e8b; }
"""


def _provenance(summary: dict | None) -> str:
    if summary is None:
        return '<p class="provenance missing">No provenance record.</p>'
    rows = [("origin", summary["origin"])]
    if summary["origin"] == "human":
        rows.append(("by", ", ".join(summary["authors"])))
    else:
        rows += [(key, summary[key]) for key in ("tool", "provider", "model", "prompt") if summary.get(key)]
    body = "".join(f"<dt>{escape(key)}</dt><dd>{escape(str(value))}</dd>" for key, value in rows)
    return f'<dl class="provenance">{body}</dl>'


def _media(item: dict) -> str:
    media = {key: escape(path) for key, path in item["media"].items()}
    kind = item["kind"]
    if kind == "image":
        return f'<a href="{media["image"]}"><img src="{media["image"]}" alt="{escape(item["name"])}" loading="lazy"></a>'
    if kind in ("animation", "model"):
        return (
            f'<video src="{media["video"]}" controls loop muted playsinline preload="metadata"></video>'
            f'<p><a href="{media["gif"]}">GIF</a></p>'
        )
    if kind == "audio":
        return f'<img src="{media["waveform"]}" alt="waveform of {escape(item["name"])}"><audio src="{media["audio"]}" controls preload="metadata"></audio>'
    raise ValueError(f"unknown kind {kind}")


def page(manifest: dict) -> str:
    title = f"Review: PR {manifest['pr']}"
    sheet = f'<div class="sheet"><img src="{escape(manifest["contact_sheet"])}" alt="contact sheet"></div>' if manifest["contact_sheet"] else ""
    items = "".join(
        f'<section class="item"><h2>{escape(item["name"])}</h2>{_media(item)}{_provenance(item["provenance"])}</section>'
        for item in manifest["items"]
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{escape(title)}</title><style>{STYLE}</style></head>"
        f'<body><h1>{escape(title)}</h1>{sheet}<div class="items">{items}</div></body></html>\n'
    )
