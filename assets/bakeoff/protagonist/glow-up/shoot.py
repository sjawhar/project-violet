"""THROWAWAY (Phase 1 bake-off, Violet glow-up). Shoots the fixed-layout contact sheet
and per-animation GIFs for one round of the Violet glow-up (docs/bakeoff/glow-up.md).

The layout is fixed at round 0 and reused byte-for-byte every later round, so the
critic's comparison is fair: same reference box (skeleton-space, rig units), same
scale, same margin, same neutral-gray background, same frame-sampling rule. See
../glow-up/rounds.md's "Fixed layout" section for how REFERENCE_BOX was derived (the
union of all seven animations' own bounds, padded generously). Do not change the
constants below after round 0 ships, even if a later round's rig grows past the
padding -- the box has headroom for exactly that, and re-fitting it would make rounds
incomparable.

Run from the repository root:
    uv run --project tools/spinerig python assets/bakeoff/protagonist/glow-up/shoot.py \
        --rig assets/bakeoff/protagonist/rig/violet.json \
        --parts assets/bakeoff/protagonist/parts \
        --out assets/bakeoff/protagonist/glow-up/round-00
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from spinerig import render as R

ANIMS = ["idle", "run", "jump", "fall", "double_jump", "dash", "land"]
LOOPING = {"idle", "run"}  # character-rig.md: these loop; the other five play once and hold.

# Fixed round-0 layout (docs/bakeoff/protagonist/glow-up/rounds.md, "Fixed layout").
REFERENCE_BOX = {"x": -763.6, "y": -40.0, "width": 1316.9, "height": 1434.7}
SCALE = 0.22
MARGIN = 0.0
BACKGROUND = (128, 128, 128, 255)  # neutral gray, #808080
FRAMES_PER_ROW = 6
LABEL_W = 90
GUTTER = 2
GIF_FPS = 30.0


def sample_times(anim_name: str, duration: float) -> list[float]:
    """Six evenly spaced sample times. Looping animations (idle, run) sample across one
    loop period, excluding t=duration: their first and last keyframe already match, so
    that sample would just repeat t=0. Held animations sample both endpoints inclusive,
    so the row shows the held final pose, which is usually the point of the animation."""
    if anim_name in LOOPING:
        return [i * duration / FRAMES_PER_ROW for i in range(FRAMES_PER_ROW)]
    return [i * duration / (FRAMES_PER_ROW - 1) for i in range(FRAMES_PER_ROW)]


def render_still(spine: dict, parts_dir: Path, anim_name: str, t: float, cache: dict) -> Image.Image:
    """One frame, composited onto the fixed neutral-gray background (spinerig's own
    render_frame returns a transparent RGBA canvas)."""
    frame = R.render_frame(spine, parts_dir, anim_name, t, scale=SCALE, margin=MARGIN, image_cache=cache, bounds=REFERENCE_BOX)
    flat = Image.new("RGBA", frame.size, BACKGROUND)
    flat.paste(frame, (0, 0), frame)
    return flat


def build_contact_sheet(spine: dict, parts_dir: Path, cache: dict) -> Image.Image:
    """Seven rows (one per animation, in character-rig.md's order), six evenly spaced
    columns each, a label column on the left naming the animation."""
    cell_w, cell_h = R.canvas_size(REFERENCE_BOX, SCALE, MARGIN)
    width = LABEL_W + FRAMES_PER_ROW * cell_w + (FRAMES_PER_ROW - 1) * GUTTER
    height = len(ANIMS) * cell_h + (len(ANIMS) - 1) * GUTTER
    sheet = Image.new("RGBA", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for row, anim_name in enumerate(ANIMS):
        duration = R.animation_duration(spine["animations"][anim_name])
        y0 = row * (cell_h + GUTTER)
        draw.text((6, y0 + cell_h // 2 - 6), anim_name, fill=(20, 20, 20, 255), font=font)
        for col, t in enumerate(sample_times(anim_name, duration)):
            still = render_still(spine, parts_dir, anim_name, t, cache)
            x0 = LABEL_W + col * (cell_w + GUTTER)
            sheet.paste(still, (x0, y0))
    return sheet


def build_gif_frames(spine: dict, parts_dir: Path, anim_name: str, cache: dict) -> list[Image.Image]:
    """Every frame of the animation at GIF_FPS, on the same fixed box/scale/background
    as the contact sheet, so a round's GIFs are directly comparable to the next round's."""
    duration = R.animation_duration(spine["animations"][anim_name])
    frame_count = max(1, round(duration * GIF_FPS))
    times = [i / GIF_FPS for i in range(frame_count)]
    return [render_still(spine, parts_dir, anim_name, t, cache) for t in times]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rig", required=True, type=Path, metavar="SKELETON.json")
    parser.add_argument("--parts", required=True, type=Path, metavar="DIR")
    parser.add_argument("--out", required=True, type=Path, metavar="DIR")
    args = parser.parse_args(argv)

    spine = json.loads(args.rig.read_text())
    cache: dict = {}
    args.out.mkdir(parents=True, exist_ok=True)

    sheet = build_contact_sheet(spine, args.parts, cache)
    sheet_path = args.out / "contact-sheet.png"
    sheet.convert("RGB").save(sheet_path)

    for anim_name in ANIMS:
        frames = build_gif_frames(spine, args.parts, anim_name, cache)
        gif_path = args.out / f"{anim_name}.gif"
        rgb_frames = [f.convert("RGB") for f in frames]
        rgb_frames[0].save(
            gif_path,
            save_all=True,
            append_images=rgb_frames[1:],
            duration=round(1000 / GIF_FPS),
            loop=0,
        )

    print(f"wrote {sheet_path} and {len(ANIMS)} GIFs to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
