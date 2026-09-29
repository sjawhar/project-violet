"""THROWAWAY (bake-off lane G-A): prices bakeoff/g-a/reports/gen-usage.jsonl (written by gen_usage.py) into gen-cost.txt.

Status per generation: `kept` is the latest generation of a piece; `superseded` was kept in a pushed commit until a
later regeneration replaced it (listed in SUPERSEDED with what replaced it); `rejected` is every other earlier generation.

    python3 bakeoff/g-a/gen_cost.py > bakeoff/g-a/reports/gen-cost.txt          # the table
    python3 bakeoff/g-a/gen_cost.py --yaml                                       # LOG.md `costs` entries
"""
import json
import sys
from pathlib import Path

# USD per 1M tokens, https://developers.openai.com/api/docs/pricing ("Image generation models", standard), read 2026-09-27.
PRICES = {"gpt-image-2": {"text_in": 5.00, "image_in": 8.00, "image_out": 30.00}}

# (usage timestamp, file) -> the regeneration that replaced it.
SUPERSEDED = {
    ("2026-09-27T08:48:31+00:00", "wall-tile.png"): "the quality=high regeneration",
    ("2026-09-27T08:48:31+00:00", "orb.png"): "the quality=high regeneration",
    ("2026-09-27T08:48:32+00:00", "crystal-wall.png"): "the quality=high regeneration",
    ("2026-09-27T08:48:32+00:00", "ground-tile.png"): "the quality=high regeneration",
    ("2026-09-27T08:48:32+00:00", "platform-tile.png"): "the quality=high regeneration",
    ("2026-09-27T08:48:36+00:00", "crystal-platform.png"): "the quality=high regeneration",
    ("2026-09-27T08:49:48+00:00", "backdrop-near.png"): "the quality=high regeneration",
    ("2026-09-27T08:49:50+00:00", "backdrop-mid.png"): "the quality=high regeneration",
    ("2026-09-27T08:49:53+00:00", "backdrop-far.png"): "the quality=high regeneration",
    ("2026-09-27T08:49:55+00:00", "goal-gate.png"): "the quality=high regeneration",
    ("2026-09-27T09:32:58+00:00", "backdrop-near.png"): "the no-green regeneration",
    ("2026-09-27T09:24:26+00:00", "goal-gate.png"): "the no-green regeneration",
    ("2026-09-27T09:28:45+00:00", "crystal-wall.png"): "the no-crystal regeneration (tag-wall)",
    ("2026-09-27T09:24:47+00:00", "crystal-platform.png"): "the no-crystal regeneration (tag-platform)",
    ("2026-09-27T09:21:50+00:00", "orb.png"): "the no-crystal regeneration (smooth orb)",
    ("2026-09-27T09:28:46+00:00", "platform-tile.png"): "the painterly regeneration (glow-up round 6)",
    ("2026-09-27T09:28:46+00:00", "ground-tile.png"): "the painterly regeneration (glow-up round 6)",
    ("2026-09-27T09:28:49+00:00", "wall-tile.png"): "the painterly regeneration (glow-up round 6)",
}

rows = [json.loads(line) for line in Path("bakeoff/g-a/reports/gen-usage.jsonl").read_text().splitlines()]
last = {row["out"]: i for i, row in enumerate(rows)}
totals = {"kept": 0.0, "rejected": 0.0, "superseded": 0.0}
out = []
for i, row in enumerate(rows):
    usage, price = row["usage"], PRICES[row["model"]]
    text_in = usage["input_tokens_details"]["text_tokens"]
    image_in = usage["input_tokens_details"]["image_tokens"]
    image_out = usage["output_tokens_details"]["image_tokens"]
    usd = (text_in * price["text_in"] + image_in * price["image_in"] + image_out * price["image_out"]) / 1e6
    replaced_by = SUPERSEDED.get((row["at"], row["out"].rsplit("/", 1)[-1]))
    status = "kept" if last[row["out"]] == i else "superseded" if replaced_by else "rejected"
    totals[status] += usd
    out.append((row, status, text_in, image_in, image_out, usd, replaced_by))

if sys.argv[1:] == ["--yaml"]:
    for row, status, *_, usd, replaced_by in out:
        piece = row["out"].rsplit("/", 1)[-1].removesuffix(".png")
        what = f"gen image {row['model']} {row['size']} quality={row['quality']}, {piece}"
        item = f"superseded by {replaced_by}: {what}" if status == "superseded" else f"{what} ({status})"
        print(f'  - {{item: "{item}", usd: {usd:.4f}, evidence: "bakeoff/g-a/reports/gen-cost.txt ({row["at"]})"}}')
    sys.exit()
print("at\tout\tmodel\tquality\tsize\tstatus\ttext_in\timage_in\timage_out\tusd")
for row, status, text_in, image_in, image_out, usd, _ in out:
    print(f"{row['at']}\t{row['out']}\t{row['model']}\t{row['quality']}\t{row['size']}\t{status}\t{text_in}\t{image_in}\t{image_out}\t{usd:.4f}")
for status, usd in totals.items():
    print(f"total {status}\t\t\t\t\t\t\t\t\t{usd:.4f}")
print(f"total\t\t\t\t\t\t\t\t\t{sum(totals.values()):.4f}")
