
from PIL import Image, ImageDraw, ImageFont
import json

RAW_DIR = "assets/bakeoff/protagonist/glow-up/trial-b/frames"
OUT_DIR = "assets/bakeoff/protagonist/glow-up/trial-b"

LABEL_W = 90
GUTTER = 2
FRAMES_PER_ROW = 6
GIF_FPS = 30.0
DURATION = 0.6
NFRAMES = 8
FRAME_DT = DURATION / NFRAMES  # 0.075
BACKGROUND = (128, 128, 128, 255)

# shoot.py's fixed reference box (docs/bakeoff/protagonist/glow-up/rounds.md).
REFERENCE_BOX = {"x": -763.6, "y": -40.0, "width": 1316.9, "height": 1434.7}

# Calibration anchor, measured directly from round-00/contact-sheet.png's run row, t=0
# column (local-to-cell bbox: x 48-229, y 98-306; height 208 canvas px at SCALE=0.22).
A_CONTACT_HEIGHT_CANVASPX = 208.0
A_SCALE = 0.22
A_CONTACT_HEIGHT_RIGUNITS = A_CONTACT_HEIGHT_CANVASPX / A_SCALE  # 945.4545...

# Ground line and horizontal anchor, as fractions of the cell's own height/width, measured
# from A's own round-00 run row at SCALE=0.22 (ground: measured sole y 306 of 316; head-x:
# average bbox-center x 135 of 290 across the six run-row columns) so both anchors scale
# correctly to any canvas_scale (e.g. the in-game sheet's smaller cells), not just 0.22's.
GROUND_Y_FRACTION = 306.0 / 316.0
HEAD_X_FRACTION = 135.0 / 290.0

HEIGHT_PX = 988.58081
IN_GAME_SCALE = (1.6 * 64.0) / HEIGHT_PX


def canvas_size(scale):
    return (round(REFERENCE_BOX["width"] * scale), round(REFERENCE_BOX["height"] * scale))


def alpha_bbox(im):
    return im.split()[-1].getbbox()


def head_centroid_x(im, bbox):
    left, upper, right, lower = bbox
    band_h = max(1, int((lower - upper) * 0.18))
    a = im.split()[-1]
    px = a.load()
    total_w = 0.0
    total = 0.0
    for y in range(upper, upper + band_h):
        for x in range(left, right):
            v = px[x, y]
            if v > 8:
                total_w += v
                total += v * x
    return total / total_w if total_w else (left + right) / 2.0


def load(i, kind):
    return Image.open(f"{RAW_DIR}/run-{kind}-{i:02d}.png").convert("RGBA")


# --- Calibration from frame 0's body ---
body0 = load(0, "body")
bbox0 = alpha_bbox(body0)
crown_y0, sole_y0 = bbox0[1], bbox0[3]
height_raw0 = sole_y0 - crown_y0
RIG_PER_RAW = A_CONTACT_HEIGHT_RIGUNITS / height_raw0
print("calibration: height_raw0", height_raw0, "RIG_PER_RAW", RIG_PER_RAW)

frame_anchors = {}
for i in range(NFRAMES):
    body = load(i, "body")
    bbox = alpha_bbox(body)
    sole_y = bbox[3]
    head_x = head_centroid_x(body, bbox)
    frame_anchors[i] = {"sole_y": sole_y, "head_x": head_x}
    print(i, frame_anchors[i])


def render_cell(i, canvas_scale):
    """Body+scarf for frame i, scaled/translated so sole_y->ground line, head_x->the
    horizontal anchor, onto a cell sized by canvas_size(canvas_scale) over BACKGROUND."""
    cell_w, cell_h = canvas_size(canvas_scale)
    ground_y = GROUND_Y_FRACTION * cell_h
    head_anchor_x = HEAD_X_FRACTION * cell_w
    scale = RIG_PER_RAW * canvas_scale
    body = load(i, "body")
    scarf = load(i, "scarf")
    anchors = frame_anchors[i]
    new_w = max(1, round(body.width * scale))
    new_h = max(1, round(body.height * scale))
    body_s = body.resize((new_w, new_h), Image.LANCZOS)
    scarf_s = scarf.resize((new_w, new_h), Image.LANCZOS)
    dx = head_anchor_x - anchors["head_x"] * scale
    dy = ground_y - anchors["sole_y"] * scale
    cell = Image.new("RGBA", (cell_w, cell_h), BACKGROUND)
    cell.paste(scarf_s, (round(dx), round(dy)), scarf_s)
    cell.paste(body_s, (round(dx), round(dy)), body_s)
    return cell


def frame_index_at(t):
    idx = int(t / FRAME_DT)
    return min(idx, NFRAMES - 1)


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
# 1/30s tick); durations are each frame's held-span in ms, rounded to GIF's 10ms
# (centisecond) granularity via cumulative rounding, so the 8 stored durations sum to
# exactly round(DURATION*1000) rather than drifting from repeatedly rounding a single
# 1000/30 ms figure down.
boundaries_ms = [round(i * FRAME_DT * 1000) for i in range(NFRAMES + 1)]  # cumulative
cum_cs = [round(b / 10) for b in boundaries_ms]  # centiseconds
durations_ms = [(cum_cs[i + 1] - cum_cs[i]) * 10 for i in range(NFRAMES)]
assert sum(durations_ms) == round(DURATION * 1000), (durations_ms, sum(durations_ms))
gif_frames = [render_cell(i, A_SCALE).convert("RGB") for i in range(NFRAMES)]
gif_path = f"{OUT_DIR}/run.gif"
gif_frames[0].save(gif_path, save_all=True, append_images=gif_frames[1:], duration=durations_ms, loop=0)
print("wrote", gif_path, "durations_ms", durations_ms, "sum", sum(durations_ms))

with open(f"{OUT_DIR}/build-calibration.json", "w") as f:
    json.dump({
        "RIG_PER_RAW": RIG_PER_RAW,
        "height_raw0": height_raw0,
        "A_CONTACT_HEIGHT_RIGUNITS": A_CONTACT_HEIGHT_RIGUNITS,
        "GROUND_Y_FRACTION": GROUND_Y_FRACTION,
        "HEAD_X_FRACTION": HEAD_X_FRACTION,
        "IN_GAME_SCALE": IN_GAME_SCALE,
        "main_cell_size": canvas_size(A_SCALE),
        "ingame_cell_size": canvas_size(IN_GAME_SCALE),
        "frame_anchors": frame_anchors,
        "sample_times_mapping": mapping_main,
        "gif_durations_ms": durations_ms,
    }, f, indent=2)
print("done")
