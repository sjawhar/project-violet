"""`spinerig generate RIG.json --out OUT.json [--print-parts]`: builds a Spine 4.3 JSON
skeleton from a violet-rig v1 description (see generate.py). Writes `OUT.json` and, next
to it, `<out-stem>.meta.json` (the setup-pose height and facing every engine reads to
scale the rig).

`spinerig render SKELETON.json --parts DIR --anim NAME --out DIR [--fps 30] [--scale S]`:
plays that Spine 4.3 subset skeleton to `OUT_DIR/frame_%04d.png` and `OUT_DIR/<anim>.gif`
with Pillow, no Spine editor or runtime involved (see render.py). Errors name the
offending bone/slot/attachment/timeline/keyframe/file and exit 1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from spinerig.generate import RigError, generate
from spinerig.render import RenderError, render_animation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="spinerig", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    generate_cmd = commands.add_parser("generate", help="build a Spine 4.3 JSON skeleton from a violet-rig v1 description")
    generate_cmd.add_argument("rig", type=Path, metavar="RIG.json")
    generate_cmd.add_argument("--out", required=True, type=Path)
    generate_cmd.add_argument("--print-parts", action="store_true", help="print each part's image, width and height")
    generate_cmd.set_defaults(handler=cmd_generate)

    render_cmd = commands.add_parser("render", help="play a Spine 4.3 JSON subset skeleton to PNG frames and a GIF")
    render_cmd.add_argument("skeleton", type=Path, metavar="SKELETON.json")
    render_cmd.add_argument("--parts", required=True, type=Path, metavar="DIR", help="directory of <path>.png part images")
    render_cmd.add_argument("--anim", required=True, metavar="NAME")
    render_cmd.add_argument("--out", required=True, type=Path, metavar="DIR")
    render_cmd.add_argument("--fps", type=float, default=30.0)
    render_cmd.add_argument("--scale", type=float, default=1.0)
    render_cmd.set_defaults(handler=cmd_render)

    return parser


def cmd_generate(args: argparse.Namespace) -> int:
    rig_path: Path = args.rig
    out: Path = args.out
    rig = json.loads(rig_path.read_text())

    try:
        spine_json, meta_json, parts = generate(rig, rig_path.parent, out.parent)
    except RigError as error:
        print(f"spinerig: error: {error}", file=sys.stderr)
        return 1

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(spine_json, indent=2) + "\n")

    meta_path = out.parent / f"{out.stem}.meta.json"
    meta_path.write_text(json.dumps(meta_json, indent=2) + "\n")

    if args.print_parts:
        for part in parts:
            print(f"{part.slot}: {part.image} {part.width}x{part.height}")

    print(f"wrote {out} and {meta_path}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    spine = json.loads(args.skeleton.read_text())
    try:
        frames = render_animation(spine, args.parts, args.anim, fps=args.fps, scale=args.scale)
    except RenderError as error:
        print(f"spinerig: error: {error}", file=sys.stderr)
        return 1

    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    for index, frame in enumerate(frames):
        frame.save(out / f"frame_{index:04d}.png")

    gif_path = out / f"{args.anim}.gif"
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=round(1000 / args.fps),
        loop=0,
        disposal=2,
    )
    print(f"wrote {len(frames)} frames and {gif_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)
