"""THROWAWAY (Phase 1 bake-off): writes assets/bakeoff/protagonist/rig-src/rig.json.

Run from the repository root:

    uv run --project tools/spinerig --with numpy python assets/bakeoff/protagonist/rig-src/mkrig.py

Bones, parts, draw order and the scarf config are the literals below; the animations
come from anims.py (executed into this namespace, filling `A`); ground.py then puts the
soles on the floor (setup lower-leg pivots, and hips translate keys on grounded frames).
Then run `spinerig generate` on the result (see ../README.md).
"""
import json
from pathlib import Path

HERE = Path("assets/bakeoff/protagonist/rig-src")
RIG = HERE / "rig.json"

bones = [
    {"name": "root"},
    {"name": "hips", "parent": "root", "y": 540, "length": 60},
    {"name": "skirt", "parent": "hips", "y": 82, "rotation": -90, "length": 520},
    {"name": "torso", "parent": "hips", "y": 82, "rotation": 90, "length": 134},
    {"name": "head", "parent": "torso", "x": 176, "y": -6, "length": 170},
    {"name": "scarf1", "parent": "head", "x": -8, "y": 34, "rotation": 158, "length": 180},
    {"name": "scarf2", "parent": "scarf1", "x": 180, "rotation": -6, "length": 180},
    {"name": "scarf3", "parent": "scarf2", "x": 180, "rotation": -6, "length": 200},
    {"name": "arm_back_upper", "parent": "torso", "x": 128, "y": 4, "rotation": -182, "length": 153},
    {"name": "arm_back_lower", "parent": "arm_back_upper", "x": 153, "rotation": 10, "length": 205},
    {"name": "arm_front_upper", "parent": "torso", "x": 128, "y": -4, "rotation": -178, "length": 153},
    {"name": "arm_front_lower", "parent": "arm_front_upper", "x": 153, "rotation": 10, "length": 213},
    {"name": "leg_back_upper", "parent": "hips", "x": -3, "rotation": -90, "length": 292},
    {"name": "leg_back_lower", "parent": "leg_back_upper", "x": 292, "rotation": 0, "length": 228},
    {"name": "leg_front_upper", "parent": "hips", "x": 3, "rotation": -90, "length": 292},
    {"name": "leg_front_lower", "parent": "leg_front_upper", "x": 292, "rotation": 0, "length": 228},
]
P = lambda slot, pivot, rot, bone=None: {"slot": slot, "bone": bone or slot, "image": f"{slot}.png", "pivot": pivot, "rotation": rot}
parts = [
    P("hips", [0.52, 0.966], 90, bone="skirt"),
    P("torso", [0.5, 0.35], -90),
    P("head", [0.62, 0.12], -90),
    # Arms: the upper sleeve ends in a rounded elbow whose centre is the elbow pivot, and it
    # draws over the forearm, so the seam stays hidden at any bend. Rotations are -phi, the
    # painted limb's own angle from the joint (the uppers lean a few degrees in the painting).
    P("arm_back_upper", [0.27, 0.91], 81),
    P("arm_back_lower", [0.27, 0.92], 87.5),
    P("arm_front_upper", [0.38, 0.91], 85),
    P("arm_front_lower", [0.34, 0.92], 90),
    P("leg_back_upper", [0.5, 0.95], 90),
    P("leg_back_lower", [0.18, 0.945], 90),
    P("leg_front_upper", [0.5, 0.97], 90),
    P("leg_front_lower", [0.3, 0.845], 90),
    P("scarf1", [0.5, 0.97], 90),
    P("scarf2", [0.5, 0.95], 90),
    P("scarf3", [0.5, 0.96], 90),
]
draw_order = ["arm_back_lower", "arm_back_upper", "leg_back_lower", "leg_back_upper",
              "leg_front_lower", "leg_front_upper", "hips", "torso",
              "scarf3", "scarf2", "scarf1", "head", "arm_front_lower", "arm_front_upper"]

A = {}
A["idle"] = {"duration": 1.0, "bones": {}}
rig = {"parts_dir": "../parts", "bones": bones, "parts": parts, "draw_order": draw_order,
       "scarf": {"bones": ["scarf1", "scarf2", "scarf3"],
                 "trail_deg": {"idle": 3, "run": 22, "jump": 10, "fall": 45, "double_jump": 50, "dash": 30, "land": -6},
                 "flutter_deg": 5, "flutter_hz": 2.0, "lag_frames": 2, "gain": [1.0, 0.75, 0.5]},
       "animations": A}
exec((HERE / "anims.py").read_text())
RIG.write_text(json.dumps(rig, indent=2))

import sys  # noqa: E402
sys.path.insert(0, str(HERE))
from ground import ground  # noqa: E402
ground(RIG)
