"""THROWAWAY (Phase 1 bake-off, Violet glow-up, technique B carried to `dash`). Finalizes
the 3 raw `dash-body-NN.png`/`dash-scarf-NN.png` frames exactly like the trial's own
`finalize_frames.py`: crop both layers of a frame to their shared alpha>8 bbox union (so
they stay pixel-aligned), then rescale by the trial's OWN `rig_per_raw` factor
(1.128227381210675, reused verbatim -- see `docs/bakeoff/protagonist/glow-up/trial-b/
technique-trial.md`'s Calibration and `dash.md`'s "why reuse, not re-derive" -- so `dash`
comes out the same overall size as `run`).

`dash` differs from `run` in one respect the trial's script didn't need: `mechanic.md`'s
dash can happen on the ground OR in the air (an unlimited ground dash, one air-dash per
airborne period), and the rig's own `dash` animation has no bone `translate` at all (every
keyframe is `rotate`-only -- checked in `rig-src/anims.py`), so there is no single "ground
line" fraction to reuse the way `idle`/`run` do. Per the assignment, every dash frame is
instead anchored by matching technique A's own HEAD position in the same animation at the
same time (never the sole), measured directly from the skeleton's forward kinematics
(`spinerig.render._placements`, the "head" slot's attachment centre) in the SAME fixed
`REFERENCE_BOX`/scale-invariant-fraction convention `build.py` already uses for
`HEAD_X_FRACTION`/`GROUND_Y_FRACTION`, so a renderer using either convention shares one
coordinate system. Each painted frame's own head centroid (2D: x and y, the same alpha-
weighted top-18%-of-bbox band `finalize_frames.py` used for x alone) is recorded alongside
that per-frame target, in `dash-finalize-record.json`, so any renderer can align them.

Run from the repository root:
    uv run --project tools/spinerig python assets/bakeoff/protagonist/glow-up/trial-b/finalize_dash.py
"""

import json
import sys

from PIL import Image

sys.path.insert(0, "tools/spinerig/src")
from spinerig.render import _placements  # noqa: E402

FRAMES_DIR = "assets/bakeoff/protagonist/glow-up/trial-b/frames"
NFRAMES = 3
ALPHA_THRESH = 8  # matches finalize_frames.py's own convention

# Reused verbatim from the trial's finalize_frames.py -- never re-derived -- so dash comes
# out at the same overall scale as run.
RIG_PER_RAW = 1.128227381210675

# The trial's own fixed reference box (shoot.py / build.py), used only to express A's
# measured head position as a fraction of that one shared cell -- scale-invariant, so it
# carries over to the in-game sheet's smaller cells the same way HEAD_X_FRACTION/
# GROUND_Y_FRACTION already do.
REFERENCE_BOX = {"x": -763.6, "y": -40.0, "width": 1316.9, "height": 1434.7}

DURATION = 0.2  # rig-src/anims.py: A["dash"] = {"duration": 0.2, "loop": False, ...}
FRAME_DT = DURATION / NFRAMES  # 3 painted keys, evenly spaced 0.0667 s apart


def strict_bbox(im):
    a = im.split()[-1]
    a2 = a.point(lambda v: 255 if v > ALPHA_THRESH else 0)
    return a2.getbbox()


def load(i, kind):
    return Image.open(f"{FRAMES_DIR}/dash-{kind}-{i:02d}.png").convert("RGBA")


def head_centroid(im, bbox):
    """Alpha-weighted centroid (x AND y) of the top 18% of the body's own alpha bbox --
    the same head-locating band finalize_frames.py used for x alone."""
    left, upper, right, lower = bbox
    band_h = max(1, int((lower - upper) * 0.18))
    a = im.split()[-1]
    px = a.load()
    total_w = 0.0
    total_x = 0.0
    total_y = 0.0
    for y in range(upper, upper + band_h):
        for x in range(left, right):
            v = px[x, y]
            if v > ALPHA_THRESH:
                total_w += v
                total_x += v * x
                total_y += v * y
    if not total_w:
        return (left + right) / 2.0, upper + band_h / 2.0
    return total_x / total_w, total_y / total_w


def target_head_fraction(spine, i):
    """A's own 'head' slot attachment centre for the dash animation at this painted
    frame's evenly-spaced time, expressed as a fraction of REFERENCE_BOX (scale-invariant)."""
    t = i * FRAME_DT
    anim = spine["animations"]["dash"]
    placements = _placements(spine, anim, t)
    _, _, cx, cy, _ = next(p for p in placements if p[0] == "head")
    fx = (cx - REFERENCE_BOX["x"]) / REFERENCE_BOX["width"]
    fy = (REFERENCE_BOX["y"] + REFERENCE_BOX["height"] - cy) / REFERENCE_BOX["height"]
    return fx, fy, t


with open("assets/bakeoff/protagonist/rig/violet.json") as f:
    SPINE = json.load(f)

records = {}
for i in range(NFRAMES):
    body = load(i, "body")
    scarf = load(i, "scarf")
    bbody = strict_bbox(body)
    bscarf = strict_bbox(scarf)
    union = (min(bbody[0], bscarf[0]), min(bbody[1], bscarf[1]), max(bbody[2], bscarf[2]), max(bbody[3], bscarf[3]))

    # anchors measured on the ORIGINAL (untrimmed) body, before crop/rescale
    sole_y_orig = bbody[3]
    head_x_orig, head_y_orig = head_centroid(body, bbody)

    body_c = body.crop(union)
    scarf_c = scarf.crop(union)
    new_w = max(1, round(body_c.width * RIG_PER_RAW))
    new_h = max(1, round(body_c.height * RIG_PER_RAW))
    body_r = body_c.resize((new_w, new_h), Image.LANCZOS)
    scarf_r = scarf_c.resize((new_w, new_h), Image.LANCZOS)

    body_path = f"{FRAMES_DIR}/dash-body-{i:02d}.png"
    scarf_path = f"{FRAMES_DIR}/dash-scarf-{i:02d}.png"
    body_r.save(body_path)
    scarf_r.save(scarf_path)

    # anchors in the NEW cropped+rescaled coordinate system
    sole_y_new = (sole_y_orig - union[1]) * RIG_PER_RAW
    head_x_new = (head_x_orig - union[0]) * RIG_PER_RAW
    head_y_new = (head_y_orig - union[1]) * RIG_PER_RAW

    target_fx, target_fy, t = target_head_fraction(SPINE, i)

    records[i] = {
        "t": t,
        "union_bbox_orig_1024canvas": union,
        "orig_size": body.size,
        "trimmed_size": body_c.size,
        "final_size": [new_w, new_h],
        "rig_per_raw": RIG_PER_RAW,
        "sole_y": sole_y_new,
        "head_x": head_x_new,
        "head_y": head_y_new,
        "target_head_x_fraction": target_fx,
        "target_head_y_fraction": target_fy,
        "ground_anchored": False,
    }
    print(i, records[i])

with open(f"{FRAMES_DIR}/dash-finalize-record.json", "w") as f:
    json.dump(records, f, indent=2)
print("done")
