"""greybox check|render: validate and picture a violet-greybox level (docs/bakeoff/greybox-format.md). THROWAWAY bake-off tooling."""
import argparse, json, sys
from pathlib import Path
from PIL import Image, ImageDraw
KINDS = {"empty", "solid", "wall_red", "wall_green", "platform_red", "platform_green", "start", "goal", "orb_red", "orb_green", "hazard"}
COLORS = {"empty": (245, 240, 230), "solid": (90, 80, 70), "wall_red": (200, 60, 50), "wall_green": (60, 170, 90), "platform_red": (230, 120, 110),
          "platform_green": (120, 210, 150), "start": (40, 120, 220), "goal": (240, 200, 40), "orb_red": (255, 30, 30), "orb_green": (30, 220, 80), "hazard": (20, 20, 20)}
NEEDS_ORB = {"wall_red": "orb_red", "platform_red": "orb_red", "wall_green": "orb_green", "platform_green": "orb_green"}


def load(path: Path) -> dict:
    data = json.loads(path.read_text())
    if data.get("format") != "violet-greybox" or data.get("version") != 1:
        raise SystemExit(f"{path}: not a violet-greybox v1 file")
    return data


def check(level: dict) -> list[str]:
    problems, rows, legend = [], level["rows"], level["legend"]
    width = len(rows[0]); counts: dict[str, int] = {}
    for r, row in enumerate(rows):
        if len(row) != width:
            problems.append(f"row {r}: {len(row)} columns, expected {width}")
        for c, ch in enumerate(row):
            kind = legend.get(ch)
            if kind is None: problems.append(f"row {r} col {c}: character {ch!r} is not in the legend"); continue
            if kind not in KINDS: problems.append(f"legend {ch!r}: unknown kind {kind}")
            counts[kind] = counts.get(kind, 0) + 1
    for single in ("start", "goal"):
        if counts.get(single, 0) != 1: problems.append(f"expected exactly one {single}, found {counts.get(single, 0)}")
    for tagged, orb in NEEDS_ORB.items():
        if counts.get(tagged) and not counts.get(orb): problems.append(f"{tagged} is used but there is no {orb}")
    if level["tile_size_px"] not in (32, 64, 128): problems.append("tile_size_px must be 32, 64 or 128")
    return problems


def render(level: dict, out: Path, scale: int) -> None:
    rows, legend = level["rows"], level["legend"]
    img = Image.new("RGB", (len(rows[0]) * scale, len(rows) * scale), COLORS["empty"]); draw = ImageDraw.Draw(img)
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            draw.rectangle([c * scale, r * scale, (c + 1) * scale - 1, (r + 1) * scale - 1], fill=COLORS[legend[ch]])
    out.parent.mkdir(parents=True, exist_ok=True); img.save(out)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="greybox"); sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("level", type=Path)
    r = sub.add_parser("render"); r.add_argument("level", type=Path); r.add_argument("--out", type=Path, required=True); r.add_argument("--scale", type=int, default=8)
    a = p.parse_args(argv); level = load(a.level)
    if a.cmd == "check":
        problems = check(level); print(*problems, sep="\n", file=sys.stderr); print(f"greybox check: {len(problems)} problem(s)"); return 1 if problems else 0
    if check(level): return main(["check", str(a.level)])
    render(level, a.out, a.scale); print(f"wrote {a.out}"); return 0
