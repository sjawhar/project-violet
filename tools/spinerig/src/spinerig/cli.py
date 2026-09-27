"""`spinerig generate RIG.json --out OUT.json [--print-parts]`: builds a Spine 4.3 JSON
skeleton from a violet-rig v1 description (see generate.py). Writes `OUT.json` and, next
to it, `<out-stem>.meta.json` (the setup-pose height and facing every engine reads to
scale the rig)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from spinerig.generate import RigError, generate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="spinerig", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    generate_cmd = commands.add_parser("generate", help="build a Spine 4.3 JSON skeleton from a violet-rig v1 description")
    generate_cmd.add_argument("rig", type=Path, metavar="RIG.json")
    generate_cmd.add_argument("--out", required=True, type=Path)
    generate_cmd.add_argument("--print-parts", action="store_true", help="print each part's image, width and height")
    generate_cmd.set_defaults(handler=cmd_generate)

    return parser


def cmd_generate(args: argparse.Namespace) -> int:
    rig_path: Path = args.rig
    rig = json.loads(rig_path.read_text())

    try:
        spine_json, meta_json, parts = generate(rig, rig_path.parent)
    except RigError as error:
        print(f"spinerig: error: {error}", file=sys.stderr)
        return 1

    out: Path = args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(spine_json, indent=2) + "\n")

    meta_path = out.parent / f"{out.stem}.meta.json"
    meta_path.write_text(json.dumps(meta_json, indent=2) + "\n")

    if args.print_parts:
        for part in parts:
            print(f"{part.slot}: {part.image} {part.width}x{part.height}")

    print(f"wrote {out} and {meta_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)
