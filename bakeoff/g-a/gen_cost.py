"""THROWAWAY (bake-off lane G-A): prices bakeoff/g-a/reports/gen-usage.jsonl (written by gen_usage.py) into gen-cost.txt.

    python3 bakeoff/g-a/gen_cost.py > bakeoff/g-a/reports/gen-cost.txt
"""
import json
from pathlib import Path

# USD per 1M tokens, https://developers.openai.com/api/docs/pricing ("Image generation models", standard), read 2026-09-27.
PRICES = {"gpt-image-2": {"text_in": 5.00, "image_in": 8.00, "image_out": 30.00}}

total = 0.0
print("at\tout\tmodel\tquality\tsize\ttext_in\timage_in\timage_out\tusd")
for line in Path("bakeoff/g-a/reports/gen-usage.jsonl").read_text().splitlines():
    row = json.loads(line)
    usage, price = row["usage"], PRICES[row["model"]]
    text_in = usage["input_tokens_details"]["text_tokens"]
    image_in = usage["input_tokens_details"]["image_tokens"]
    image_out = usage["output_tokens_details"]["image_tokens"]
    usd = (text_in * price["text_in"] + image_in * price["image_in"] + image_out * price["image_out"]) / 1e6
    total += usd
    print(f"{row['at']}\t{row['out']}\t{row['model']}\t{row['quality']}\t{row['size']}\t{text_in}\t{image_in}\t{image_out}\t{usd:.4f}")
print(f"total\t\t\t\t\t\t\t\t{total:.4f}")
