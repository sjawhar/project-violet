"""THROWAWAY (bake-off lane G-A): prices bakeoff/g-a/reports/gen-usage.jsonl (written by gen_usage.py) into gen-cost.txt.

Status per generation: `kept` is the latest generation of a piece; `superseded` is the piece's latest generation at an
earlier quality (kept until the quality=high regeneration replaced it); `rejected` is every other earlier generation.

    python3 bakeoff/g-a/gen_cost.py > bakeoff/g-a/reports/gen-cost.txt          # the table
    python3 bakeoff/g-a/gen_cost.py --yaml                                       # LOG.md `costs` entries
"""
import json
import sys
from pathlib import Path

# USD per 1M tokens, https://developers.openai.com/api/docs/pricing ("Image generation models", standard), read 2026-09-27.
PRICES = {"gpt-image-2": {"text_in": 5.00, "image_in": 8.00, "image_out": 30.00}}

rows = [json.loads(line) for line in Path("bakeoff/g-a/reports/gen-usage.jsonl").read_text().splitlines()]
last = {row["out"]: i for i, row in enumerate(rows)}
last_at_quality = {(row["out"], row["quality"]): i for i, row in enumerate(rows)}
totals = {"kept": 0.0, "rejected": 0.0, "superseded": 0.0}
out = []
for i, row in enumerate(rows):
    usage, price = row["usage"], PRICES[row["model"]]
    text_in = usage["input_tokens_details"]["text_tokens"]
    image_in = usage["input_tokens_details"]["image_tokens"]
    image_out = usage["output_tokens_details"]["image_tokens"]
    usd = (text_in * price["text_in"] + image_in * price["image_in"] + image_out * price["image_out"]) / 1e6
    kept_quality = rows[last[row["out"]]]["quality"]
    status = "kept" if last[row["out"]] == i else "superseded" if row["quality"] != kept_quality and last_at_quality[(row["out"], row["quality"])] == i else "rejected"
    totals[status] += usd
    out.append((row, status, text_in, image_in, image_out, usd))

if sys.argv[1:] == ["--yaml"]:
    for row, status, *_, usd in out:
        piece = row["out"].rsplit("/", 1)[-1].removesuffix(".png")
        what = f"gen image {row['model']} {row['size']} quality={row['quality']}, {piece}"
        item = f"superseded by the quality=high regeneration: {what}" if status == "superseded" else f"{what} ({status})"
        print(f'  - {{item: "{item}", usd: {usd:.4f}, evidence: "bakeoff/g-a/reports/gen-cost.txt ({row["at"]})"}}')
    sys.exit()
print("at\tout\tmodel\tquality\tsize\tstatus\ttext_in\timage_in\timage_out\tusd")
for row, status, text_in, image_in, image_out, usd in out:
    print(f"{row['at']}\t{row['out']}\t{row['model']}\t{row['quality']}\t{row['size']}\t{status}\t{text_in}\t{image_in}\t{image_out}\t{usd:.4f}")
for status, usd in totals.items():
    print(f"total {status}\t\t\t\t\t\t\t\t\t{usd:.4f}")
print(f"total\t\t\t\t\t\t\t\t\t{sum(totals.values()):.4f}")
