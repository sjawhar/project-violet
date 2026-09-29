"""THROWAWAY (Phase 1 bake-off, Violet glow-up technique trial). Builds technique B's
(frame-by-frame painted) run-only contact-sheet row, in-game-scale row, and 30 fps GIF
from the finalized frame files in frames/ (each already trimmed to its frame's shared
body+scarf alpha bbox and rescaled to rig units by finalize_frames.py).

Uses shoot.py's own fixed reference box, cell-size formula and background so the sheet
is directly comparable to technique A's contact-sheet.png run row. Frame timing follows
rig-src/anims.py's run animation (duration 0.6 s, loop): 8 painted keyframes, evenly
spaced 0.075 s apart, each held (not interpolated) until the next frame's time -- the
"the frame showing at that time" rule from the assignment. See technique-trial.md for
the pose list and calibration reasoning.

Run from the repository root:
    uv run --project tools/spinerig python assets/bakeoff/protagonist/glow-up/trial-b/build.py
"""

from PIL import Image, ImageDraw, ImageFont
import json

RAW_DIR = "assets/bakeoff/protagonist/glow-up/trial-b/frames"
OUT_DIR = "assets/bakeoff/protagonist/glow-up/trial-b"

LABEL_W = 90
GUTTER = 2
FRAMES_PER_ROW = 6
GIF_FPS = 30.0
DURATION = 0.6  # rig-src/anims.py: A["run"] = {"duration": 0.6, "loop": True, ...}
NFRAMES = 8
FRAME_DT = DURATION / NFRAMES  # 0.075 s per painted key
BACKGROUND = (128, 128, 128, 255)  # #808080, shoot.py's BACKGROUND

# shoot.py's fixed reference box (docs/bakeoff/protagonist/glow-up/rounds.md, "Fixed layout").
REFERENCE_BOX = {"x": -763.6, "y": -40.0, "width": 1316.9, "height": 1434.7}
A_SCALE = 0.22  # shoot.py's SCALE

# Ground line and horizontal anchor, as fractions of the cell's own height/width, measured
# from technique A's own round-00 contact-sheet.png run row at SCALE=0.22 (ground: the
# measured sole y of every one of its six columns, 306-307 of a 316px cell; horizontal:
# the average bbox-center x across those six columns, ~135 of a 290px cell). Fractions
# (not absolute px) so both anchors scale correctly to the in-game sheet's smaller cells
# too, not just 0.22's.
GROUND_Y_FRACTION = 306.0 / 316.0
HEAD_X_FRACTION = 135.0 / 290.0

# character-rig.md's in-game scale formula, evaluated at the live rig's own setup height
# (violet.meta.json height_px), the same standard technique A's technique-trial.md/
# rounds.md sheets are held to.
HEIGHT_PX = 988.58081
IN_GAME_SCALE = (1.6 * 64.0) / HEIGHT_PX


def canvas_size(scale):
    return (round(REFERENCE_BOX["width"] * scale), round(REFERENCE_BOX["height"] * scale))


def load(i, kind):
    return Image.open(f"{RAW_DIR}/run-{kind}-{i:02d}.png").convert("RGBA")


with open(f"{RAW_DIR}/finalize-record.json") as f:
    FRAME_ANCHORS = {int(k): v for k, v in json.load(f).items()}


def render_cell(i, canvas_scale):
    """Body+scarf for painted frame i, scaled so canvas_scale rig-units-per-px matches
    shoot.py's own SCALE/in_game_scale, translated so the frame's own sole_y anchor lands
    on the ground line and its head_x anchor lands on the horizontal anchor, onto a cell
    sized by canvas_size(canvas_scale) over the fixed neutral-gray BACKGROUND. The frame
    files are already in rig-unit pixels (finalize_frames.py), so canvas_scale is the only
    remaining scale factor here. Body and scarf are resized independently (not forced to a
    shared size): the two QA-fixed frames (run-scarf-01/05, finalize_run_scarf_fix.py) crop
    the scarf to its own bbox rather than reusing the body's, and carry an extra
    `scarf_offset_final` (rig-unit space, absent/[0,0] for every other frame) shifting the
    scarf paste relative to the body's own anchor-derived position."""
    cell_w, cell_h = canvas_size(canvas_scale)
    ground_y = GROUND_Y_FRACTION * cell_h
    head_anchor_x = HEAD_X_FRACTION * cell_w
    anchors = FRAME_ANCHORS[i]
    body = load(i, "body")
    scarf = load(i, "scarf")
    body_s = body.resize((max(1, round(body.width * canvas_scale)), max(1, round(body.height * canvas_scale))), Image.LANCZOS)
    scarf_s = scarf.resize((max(1, round(scarf.width * canvas_scale)), max(1, round(scarf.height * canvas_scale))), Image.LANCZOS)
    dx = head_anchor_x - anchors["head_x"] * canvas_scale
    dy = ground_y - anchors["sole_y"] * canvas_scale
    scarf_dx, scarf_dy = anchors.get("scarf_offset_final", [0.0, 0.0])
    cell = Image.new("RGBA", (cell_w, cell_h), BACKGROUND)
    cell.paste(scarf_s, (round(dx + scarf_dx * canvas_scale), round(dy + scarf_dy * canvas_scale)), scarf_s)
    cell.paste(body_s, (round(dx), round(dy)), body_s)
    return cell


def frame_index_at(t):
    return min(int(t / FRAME_DT), NFRAMES - 1)


def build_row(canvas_scale, sample_times, out_path, label="run"):
    cell_w, cell_h = canvas_size(canvas_scale)
    width = LABEL_W + FRAMES_PER_ROW * cell_w + (FRAMES_PER_ROW - 1) * GUTTER
    height = cell_h
    sheet = Image.new("RGBA", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((6, height // 2 - 6), label, fill=(20, 20, 20, 255), font=font)
    mapping = []
    for col, t in enumerate(sample_times):
        idx = frame_index_at(t)
        mapping.append((t, idx))
        cell = render_cell(idx, canvas_scale)
        x0 = LABEL_W + col * (cell_w + GUTTER)
        sheet.paste(cell, (x0, 0))
    sheet.convert("RGB").save(out_path)
    print("wrote", out_path, "size", sheet.size, "mapping", mapping)
    return mapping


sample_times = [i * DURATION / FRAMES_PER_ROW for i in range(FRAMES_PER_ROW)]
print("sample_times", sample_times)

mapping_main = build_row(A_SCALE, sample_times, f"{OUT_DIR}/run-row.png")
mapping_ingame = build_row(IN_GAME_SCALE, sample_times, f"{OUT_DIR}/run-row-ingame.png")

# GIF at 30 fps, main SCALE (matches shoot.py's own GIFs, which are also at SCALE not
# in-game scale). Each of the NFRAMES painted frames holds from its own start time to
# the next frame's start time (a discrete, "on the frame" hold, not resampled every
# 1/30s tick, since technique B has no in-between interpolation); durations are each
# frame's held-span in ms, rounded to GIF's 10ms (centisecond) granularity via cumulative
# rounding, so the 8 stored durations sum to exactly round(DURATION*1000) rather than
# drifting low from repeatedly rounding a single 1000/30 ms figure down.
boundaries_ms = [round(i * FRAME_DT * 1000) for i in range(NFRAMES + 1)]
cum_cs = [round(b / 10) for b in boundaries_ms]
durations_ms = [(cum_cs[i + 1] - cum_cs[i]) * 10 for i in range(NFRAMES)]
assert sum(durations_ms) == round(DURATION * 1000), (durations_ms, sum(durations_ms))
gif_frames = [render_cell(i, A_SCALE).convert("RGB") for i in range(NFRAMES)]
gif_path = f"{OUT_DIR}/run.gif"
gif_frames[0].save(gif_path, save_all=True, append_images=gif_frames[1:], duration=durations_ms, loop=0)
print("wrote", gif_path, "durations_ms", durations_ms, "sum", sum(durations_ms))

with open(f"{OUT_DIR}/build-calibration.json", "w") as f:
    json.dump({
        "GROUND_Y_FRACTION": GROUND_Y_FRACTION,
        "HEAD_X_FRACTION": HEAD_X_FRACTION,
        "IN_GAME_SCALE": IN_GAME_SCALE,
        "main_cell_size": canvas_size(A_SCALE),
        "ingame_cell_size": canvas_size(IN_GAME_SCALE),
        "frame_anchors": FRAME_ANCHORS,
        "sample_times_mapping": mapping_main,
        "gif_durations_ms": durations_ms,
    }, f, indent=2)
print("done")
