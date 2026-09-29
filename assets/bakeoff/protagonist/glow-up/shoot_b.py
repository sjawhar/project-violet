"""THROWAWAY (Phase 1 bake-off, Violet glow-up, round 4). Shoots technique B's (frame-by-
frame painted sprites, `trial-b/`) contact sheet and per-animation GIFs in EXACTLY the
same fixed layout `shoot.py` shoots technique A: same reference box, scale, background,
label column, row order and cell size (imported from `shoot.py`, not re-derived), so the
critic's blind round-4 comparison against technique A's round-03 shots is fair.

Technique B has no skeleton to render with `spinerig.render`, so each cell is composited
directly from that animation's painted `frames/<anim>-body-NN.png` /
`frames/<anim>-scarf-NN.png` layers (`trial-b/finalize_anim.py`, `finalize_frames.py`,
`finalize_idle.py`, `finalize_dash.py`), already trimmed to their shared alpha bbox and
rescaled to the one shared `RIG_PER_RAW` factor (`technique-trial.md`'s calibration) so
every animation is the same size as `run`. Frame `i`'s own `<anim>-finalize-record.json`
entry records how to place it, in one of the schemes the six painting lanes used:

- **grounded** (`idle`, `run`, `land`): `sole_y` lands on `build.py`'s own
  `GROUND_Y_FRACTION` of the cell height, and `head_x` lands on its `HEAD_X_FRACTION` of
  the cell width -- reused unchanged from `build.py`, not re-derived, so every grounded
  animation shares one floor line and one horizontal anchor.
- **airborne, absolute rig units** (`jump`, `fall`, `double_jump`): `head_x`/`head_y`
  land exactly on that frame's own `target_head_x`/`target_head_y` -- technique A's own
  head position in the same animation at the same time, in the same rig-unit space
  `head_x`/`head_y` are already measured in, so the offset is a straight subtraction
  times `canvas_scale`.
- **airborne, cell fraction** (`dash`): `target_head_x_fraction`/`target_head_y_fraction`
  are fractions of the cell (scale-invariant, like `GROUND_Y_FRACTION`), because `dash`
  can happen grounded or airborne and its own rig timeline never translates, so there is
  no absolute rig-unit anchor to measure `dash` against consistently across other anims.

A frame's own `scarf_offset_final` (present only on `run`'s QA-fixed frames 1 and 5,
`trial-b/finalize_run_scarf_fix.py`) shifts the scarf paste relative to the body's one
shared anchor, exactly like `build.py`'s `render_cell` already does.

Six-sample and 30 fps-GIF timing reuse `shoot.py`'s own `sample_times()` (looping vs.
held) and its `main()`'s per-frame GIF duration unchanged; the only new piece is mapping
a sample/GIF time to "the painted frame showing at that time" -- a held, not
interpolated, step lookup: `frame_index_at(t) = min(floor(t / (duration / nframes)),
nframes - 1)`, the same evenly-spaced-frame convention every painting lane's own record
confirms (`run`'s `FRAME_DT = 0.6/8`, `idle`'s `1.0/8`, `jump`'s `0.5/5`, `land`'s
`0.25/3`, `dash`'s `0.2/3`, `fall`'s `0.6/5`, `double_jump`'s `0.5/5`).

Run from the repository root:
    uv run --project tools/spinerig python assets/bakeoff/protagonist/glow-up/shoot_b.py \\
        --rig assets/bakeoff/protagonist/rig/violet.json \\
        --out assets/bakeoff/protagonist/glow-up/round-04
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from spinerig import render as R

import shoot as A  # shoot.py: the one place the fixed round-0 layout constants live

FRAMES_DIR = Path(__file__).resolve().parent / "trial-b" / "frames"
BUILD_PY = Path(__file__).resolve().parent / "trial-b" / "build.py"

# build.py's own calibration: the ground line and horizontal anchor, as fractions of the
# cell's height/width, measured once from technique A's round-00 contact-sheet run row
# (the layout is fixed at round 0 and never re-fit -- shoot.py's own module docstring).
# Imported by executing build.py's module-level assignments would also run its build
# side effects, so the two constants are reproduced here from the same single source
# `build.py` documents them from, not re-measured.
GROUND_Y_FRACTION = 306.0 / 316.0
HEAD_X_FRACTION = 135.0 / 290.0

# The one shared scale every painted frame was calibrated to (technique-trial.md), used
# only for the RECORD filename convention below, never re-derived here.
RUN_RECORD_NAME = "finalize-record.json"  # the original trial's own naming, no anim prefix


def record_path(anim: str) -> Path:
    name = RUN_RECORD_NAME if anim == "run" else f"{anim}-finalize-record.json"
    return FRAMES_DIR / name


def load_record(anim: str) -> dict[int, dict]:
    with open(record_path(anim)) as f:
        raw = json.load(f)
    return {int(k): v for k, v in raw.items()}


def frame_count(anim: str) -> int:
    return len(list(FRAMES_DIR.glob(f"{anim}-body-*.png")))


def frame_index_at(t: float, duration: float, nframes: int) -> int:
    """Held, not interpolated: the painted frame showing at time t, for nframes evenly
    spaced across duration (every painting lane's own record uses this spacing -- see
    module docstring)."""
    dt = duration / nframes
    return min(int(t / dt), nframes - 1) if dt > 0 else 0


def _load_layer(anim: str, i: int, kind: str, scale: float, cache: dict) -> Image.Image:
    key = (anim, i, kind, scale)
    if key not in cache:
        image = Image.open(FRAMES_DIR / f"{anim}-{kind}-{i:02d}.png").convert("RGBA")
        if scale != 1.0:
            image = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.LANCZOS)
        cache[key] = image
    return cache[key]


def render_cell_b(anim: str, i: int, record: dict, canvas_scale: float, cell_w: int, cell_h: int, cache: dict) -> Image.Image:
    """One technique-B cell: body+scarf for painted frame `i`, placed per that frame's own
    anchor scheme (see module docstring), onto a cell sized `cell_w x cell_h` over the
    fixed neutral-gray background -- the same background `shoot.py`'s `render_still`
    composites technique A onto."""
    anchors = record[i]
    body_s = _load_layer(anim, i, "body", canvas_scale, cache)
    scarf_s = _load_layer(anim, i, "scarf", canvas_scale, cache)

    if "target_head_x_fraction" in anchors:
        # airborne, cell-fraction scheme (dash): scale-invariant target, carries to the
        # in-game sheet's smaller cells the same way GROUND_Y_FRACTION/HEAD_X_FRACTION do.
        target_x = anchors["target_head_x_fraction"] * cell_w
        target_y = anchors["target_head_y_fraction"] * cell_h
        dx = target_x - anchors["head_x"] * canvas_scale
        dy = target_y - anchors["head_y"] * canvas_scale
    elif "target_head_x" in anchors:
        # airborne, absolute rig-unit scheme (jump, fall, double_jump): head_x/head_y and
        # target_head_x/y already share one coordinate space, so a straight subtraction
        # gives the placement offset -- no ground line anywhere.
        dx = (anchors["target_head_x"] - anchors["head_x"]) * canvas_scale
        dy = (anchors["target_head_y"] - anchors["head_y"]) * canvas_scale
    else:
        # grounded (idle, run, land): sole_y onto the shared ground line, head_x onto the
        # shared horizontal anchor -- build.py's own render_cell formula for run.
        ground_y = GROUND_Y_FRACTION * cell_h
        head_anchor_x = HEAD_X_FRACTION * cell_w
        dx = head_anchor_x - anchors["head_x"] * canvas_scale
        dy = ground_y - anchors["sole_y"] * canvas_scale

    scarf_dx, scarf_dy = anchors.get("scarf_offset_final", [0.0, 0.0])

    cell = Image.new("RGBA", (cell_w, cell_h), A.BACKGROUND)
    cell.paste(scarf_s, (round(dx + scarf_dx * canvas_scale), round(dy + scarf_dy * canvas_scale)), scarf_s)
    cell.paste(body_s, (round(dx), round(dy)), body_s)
    return cell


def build_contact_sheet_b(spine: dict, cache: dict, *, scale: float = A.SCALE) -> Image.Image:
    """Same seven rows / six columns / label column layout as shoot.py's own
    build_contact_sheet, technique B's painted frames in place of technique A's rig."""
    cell_w, cell_h = R.canvas_size(A.REFERENCE_BOX, scale, A.MARGIN)
    width = A.LABEL_W + A.FRAMES_PER_ROW * cell_w + (A.FRAMES_PER_ROW - 1) * A.GUTTER
    height = len(A.ANIMS) * cell_h + (len(A.ANIMS) - 1) * A.GUTTER
    sheet = Image.new("RGBA", (width, height), A.BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for row, anim_name in enumerate(A.ANIMS):
        duration = R.animation_duration(spine["animations"][anim_name])
        nframes = frame_count(anim_name)
        record = load_record(anim_name)
        y0 = row * (cell_h + A.GUTTER)
        draw.text((6, y0 + cell_h // 2 - 6), anim_name, fill=(20, 20, 20, 255), font=font)
        for col, t in enumerate(A.sample_times(anim_name, duration)):
            idx = frame_index_at(t, duration, nframes)
            cell = render_cell_b(anim_name, idx, record, scale, cell_w, cell_h, cache)
            x0 = A.LABEL_W + col * (cell_w + A.GUTTER)
            sheet.paste(cell, (x0, y0))
    return sheet


def build_gif_frames_b(spine: dict, anim_name: str, cache: dict) -> list[Image.Image]:
    """Every 1/GIF_FPS s tick over the animation's duration, at the fixed box/scale/
    background, held (not interpolated) on whichever painted frame is showing -- same
    frame-count/duration convention as shoot.py's own build_gif_frames."""
    duration = R.animation_duration(spine["animations"][anim_name])
    nframes = frame_count(anim_name)
    record = load_record(anim_name)
    cell_w, cell_h = R.canvas_size(A.REFERENCE_BOX, A.SCALE, A.MARGIN)
    frame_count_gif = max(1, round(duration * A.GIF_FPS))
    times = [i / A.GIF_FPS for i in range(frame_count_gif)]
    return [render_cell_b(anim_name, frame_index_at(t, duration, nframes), record, A.SCALE, cell_w, cell_h, cache) for t in times]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rig", required=True, type=Path, metavar="SKELETON.json")
    parser.add_argument("--out", required=True, type=Path, metavar="DIR")
    args = parser.parse_args(argv)

    spine = json.loads(args.rig.read_text())
    cache: dict = {}
    args.out.mkdir(parents=True, exist_ok=True)

    sheet = build_contact_sheet_b(spine, cache)
    sheet_path = args.out / "contact-sheet.png"
    sheet.convert("RGB").save(sheet_path)

    ingame_sheet = build_contact_sheet_b(spine, cache, scale=A.in_game_scale(spine))
    ingame_sheet_path = args.out / "contact-sheet-ingame.png"
    ingame_sheet.convert("RGB").save(ingame_sheet_path)

    for anim_name in A.ANIMS:
        frames = build_gif_frames_b(spine, anim_name, cache)
        gif_path = args.out / f"{anim_name}.gif"
        rgb_frames = [f.convert("RGB") for f in frames]
        rgb_frames[0].save(
            gif_path,
            save_all=True,
            append_images=rgb_frames[1:],
            duration=round(1000 / A.GIF_FPS),
            loop=0,
        )

    print(f"wrote {sheet_path}, {ingame_sheet_path}, and {len(A.ANIMS)} GIFs to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
