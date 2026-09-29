"""THROWAWAY (Phase 1 bake-off): lowest opaque point of each foot (leg_*_lower part) in
skeleton space, per frame, using spinerig's own FK/placement code (render._placements).
Used by ground.py; run it directly from the repository root to print every animation's
foot heights per frame:

    uv run --project tools/spinerig --with numpy python assets/bakeoff/protagonist/rig-src/feet.py
"""
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image

from spinerig.generate import generate
from spinerig.render import _placements

PARTS = Path("assets/bakeoff/protagonist/parts")
FEET = ("leg_back_lower", "leg_front_lower")
_pts = {}


def points(slot):
    if slot not in _pts:
        a = np.asarray(Image.open(PARTS / f"{slot}.png").convert("RGBA"))[..., 3]
        h, w = a.shape
        ys, xs = np.nonzero(a > 128)
        # image px -> centred coords, y up
        _pts[slot] = np.stack([xs + 0.5 - w / 2, h / 2 - (ys + 0.5)], 1)
    return _pts[slot]


def spine_of(rig_path):
    rig_path = Path(rig_path)
    return generate(json.loads(rig_path.read_text()), rig_path.parent, rig_path.parent)[0]


def feet(spine, anim, t):
    """{slot: (min_y, x_at_min)} for both feet at time t ('__setup' = no animation)."""
    animation = spine["animations"].get(anim, {"bones": {}})
    out = {}
    for slot, att, cx, cy, rot in _placements(spine, animation, t):
        if slot not in FEET:
            continue
        r = math.radians(rot)
        p = points(slot)
        wx = cx + p[:, 0] * math.cos(r) - p[:, 1] * math.sin(r)
        wy = cy + p[:, 0] * math.sin(r) + p[:, 1] * math.cos(r)
        i = int(np.argmin(wy))
        out[slot] = (float(wy[i]), float(wx[i]), float(wx.min()), float(wx.max()))
    return out


def report(rig_path, anims=("idle", "run", "jump", "fall", "double_jump", "dash", "land"), fps=30):
    spine = spine_of(rig_path)
    s = feet(spine, "__setup", 0)
    print("setup", {k: round(v[0], 1) for k, v in s.items()})
    for a in anims:
        keys = [k for tl in spine["animations"][a]["bones"].values() for kl in tl.values() for k in kl]
        dur = max(k["time"] for k in keys)
        n = max(1, round(dur * fps))
        rows = []
        for i in range(n):
            f = feet(spine, a, i / fps)
            rows.append("%d:%s" % (i, "/".join(f"{f[k][0]:.0f}" for k in FEET)))
        print(a, " ".join(rows))


if __name__ == "__main__":
    report(sys.argv[1] if len(sys.argv) > 1 else "assets/bakeoff/protagonist/rig-src/rig.json")
