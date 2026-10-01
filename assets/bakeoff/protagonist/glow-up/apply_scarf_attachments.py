"""Bind each painted scarf knot to its authored neck landmark.

Run after any frame finalization, before shoot_b.py:
    python assets/bakeoff/protagonist/glow-up/apply_scarf_attachments.py apply
    python assets/bakeoff/protagonist/glow-up/apply_scarf_attachments.py check

Landmarks belong to exact PNG bytes. New artwork needs new visually verified
landmarks; crop origins alone are not anatomical attachment points.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from PIL import Image

GLOWUP = Path(__file__).resolve().parent
FRAMES = GLOWUP / "trial-b/frames"
PINS = GLOWUP / "scarf_attachments.json"


def validate_sources() -> list[dict]:
    pins = json.loads(PINS.read_text())["frames"]
    expected = {
        (p.stem.rsplit("-", 2)[0], int(p.stem.rsplit("-", 1)[1]))
        for p in FRAMES.glob("*-body-??.png")
    }
    seen = set()
    for pin in pins:
        key = (pin["animation"], pin["index"])
        if key in seen:
            raise ValueError(f"Duplicate attachment: {key}")
        seen.add(key)
        for kind, field in (("body", "body_neck"), ("scarf", "scarf_knot")):
            path = FRAMES / f"{key[0]}-{kind}-{key[1]:02}.png"
            if hashlib.sha256(path.read_bytes()).hexdigest() != pin[f"{kind}_sha256"]:
                raise ValueError(f"{path.name}: pixels changed; re-author its attachment landmark")
            point = pin[field]
            with Image.open(path) as image:
                if len(point) != 2 or not all(math.isfinite(v) for v in point):
                    raise ValueError(f"{path.name}: invalid {field}")
                x, y = map(round, point)
                if not (0 <= x < image.width and 0 <= y < image.height):
                    raise ValueError(f"{path.name}: {field} is outside its image")
                if image.convert("RGBA").getpixel((x, y))[3] <= 8:
                    raise ValueError(f"{path.name}: {field} is on transparent pixels")
    if seen != expected:
        raise ValueError(f"Attachment coverage: missing={expected - seen}, extra={seen - expected}")
    return pins


def check_attachments(*, apply: bool = False) -> int:
    pins = validate_sources()
    records = {}
    for pin in pins:
        anim, index = pin["animation"], pin["index"]
        path = FRAMES / ("finalize-record.json" if anim == "run" else f"{anim}-finalize-record.json")
        if path not in records:
            records[path] = json.loads(path.read_text())
        frame = records[path][str(index)]
        wanted = [pin["body_neck"][j] - pin["scarf_knot"][j] for j in (0, 1)]
        if apply:
            frame["scarf_offset_final"] = wanted
        elif not math.dist(frame.get("scarf_offset_final", [0, 0]), wanted) <= 1:
            raise ValueError(f"{anim} frame {index}: scarf knot misses neck; run apply_scarf_attachments.py apply")
    if apply:
        for path, record in records.items():
            path.write_text(json.dumps(record, indent=2) + "\n")
    return len(pins)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("check", "apply"))
    args = parser.parse_args()
    count = check_attachments(apply=args.mode == "apply")
    print(f"Scarf attachment {args.mode}: {count} frame pairs")


if __name__ == "__main__":
    main()
