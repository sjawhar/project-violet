# THROWAWAY (Phase 1 bake-off). Executed inside mkrig.py: fills A (animations). Angles are deltas on the setup pose.
# Conventions (setup world rotations): torso/head point up (90), limbs point down (~-90).
# Positive = counter-clockwise: a downward limb swings its far end FORWARD (+x, she faces
# right); the torso tilts BACK. Knee flex = negative lower-leg delta; elbow flex = positive.

RISE = {  # airborne rising pose shared by jump's end, fall's start, double_jump's end
    "leg_front_upper": 45, "leg_front_lower": -60, "leg_back_upper": 15, "leg_back_lower": -80,
    "arm_front_upper": 110, "arm_front_lower": 15, "arm_back_upper": 90, "arm_back_lower": 15,
    "torso": 2, "head": -2, "skirt": 20,
}


def pose_keys(frames, loop=False):
    """frames: [(t, {bone: angle}, {bone: (x, y)})] -> {bone: {rotate/translate}}; a bone
    missing from a frame holds 0 there."""
    bones_r = sorted({b for _, r, _ in frames for b in r})
    bones_t = sorted({b for _, _, tr_ in frames for b in tr_})
    out = {}
    for b in bones_r:
        out.setdefault(b, {})["rotate"] = [{"time": t, "angle": r.get(b, 0)} for t, r, _ in frames]
    for b in bones_t:
        out.setdefault(b, {})["translate"] = [
            {"time": t, "x": tr_.get(b, (0, 0))[0], "y": tr_.get(b, (0, 0))[1]} for t, _, tr_ in frames]
    return out


# idle: 1.0 s breathing sway; the upper body settles 4 px and leans, head counters.
A["idle"] = {"duration": 1.0, "loop": True, "bones": pose_keys([
    (0.0, {}, {"torso": (0, 0)}),
    (0.5, {"torso": -2, "head": 3, "arm_front_upper": 3, "arm_front_lower": 3,
           "arm_back_upper": -2, "arm_back_lower": 2}, {"torso": (0, -4)}),
    (1.0, {}, {"torso": (0, 0)}),
])}

# run: 0.6 s; contact at 0 (front leg forward) and 0.3 (back leg forward), passing at
# 0.15/0.45; arms swing opposite the legs; body lowest at mid-stance.
LEAN = {"torso": -10, "head": 7}
def run_frame(front_upper, front_lower, back_upper, back_lower, arm, skirt):
    f = dict(LEAN)
    f["skirt"] = skirt
    f.update({"leg_front_upper": front_upper, "leg_front_lower": front_lower,
              "leg_back_upper": back_upper, "leg_back_lower": back_lower,
              "arm_front_upper": -arm, "arm_front_lower": 45 + arm * 0.6,
              "arm_back_upper": arm, "arm_back_lower": 45 - arm * 0.6})
    return f
A["run"] = {"duration": 0.6, "loop": True, "bones": pose_keys([
    (0.0, run_frame(24, -8, -24, -30, 28, -2), {"hips": (0, -4)}),
    (0.15, run_frame(0, -18, 8, -80, 0, -7), {"hips": (0, -12)}),
    (0.3, run_frame(-24, -30, 24, -8, -28, -2), {"hips": (0, -4)}),
    (0.45, run_frame(8, -80, 0, -18, 0, -7), {"hips": (0, -12)}),
    (0.6, run_frame(24, -8, -24, -30, 28, -2), {"hips": (0, -4)}),
])}

# jump: 0.5 s; crouch, extend at take-off, then the rising tuck (held).
A["jump"] = {"duration": 0.5, "loop": False, "bones": pose_keys([
    (0.0, {"leg_front_upper": 25, "leg_front_lower": -55, "leg_back_upper": 20, "leg_back_lower": -50,
           "torso": -18, "head": 10, "arm_front_upper": -35, "arm_front_lower": 10,
           "arm_back_upper": -30, "arm_back_lower": 10, "skirt": 8}, {"hips": (0, -60)}),
    (0.12, {"leg_front_upper": -5, "leg_front_lower": 0, "leg_back_upper": -8, "leg_back_lower": -5,
            "torso": 4, "head": -2, "arm_front_upper": 140, "arm_front_lower": 10,
            "arm_back_upper": 120, "arm_back_lower": 10, "skirt": 4}, {"hips": (0, 12)}),
    (0.3, RISE, {"hips": (0, 0)}),
    (0.5, RISE, {"hips": (0, 0)}),
])}

# fall: 0.6 s, plays once and holds; legs drop and spread, arms go up and out.
A["fall"] = {"duration": 0.6, "loop": False, "bones": pose_keys([
    (0.0, RISE, {}),
    (0.3, {"leg_front_upper": 22, "leg_front_lower": -18, "leg_back_upper": -18, "leg_back_lower": -38,
           "arm_front_upper": 125, "arm_front_lower": 25, "arm_back_upper": -70, "arm_back_lower": 20,
           "torso": 5, "head": -4, "skirt": 6}, {}),
    (0.6, {"leg_front_upper": 16, "leg_front_lower": -22, "leg_back_upper": -24, "leg_back_lower": -32,
           "arm_front_upper": 118, "arm_front_lower": 30, "arm_back_upper": -80, "arm_back_lower": 25,
           "torso": 7, "head": -6, "skirt": 4}, {}),
])}

# double_jump: 0.5 s; snap into a tuck and front-flip 360 degrees about the hips by
# 0.35 s, then open back out to the rising pose.
TUCK = {"leg_front_upper": 105, "leg_front_lower": -135, "leg_back_upper": 98, "leg_back_lower": -132,
        "arm_front_upper": 60, "arm_front_lower": 80, "arm_back_upper": 50, "arm_back_lower": 80,
        "torso": -30, "head": -18, "skirt": 85}
def with_hips(pose, angle):
    p = dict(pose); p["hips"] = angle; return p
A["double_jump"] = {"duration": 0.5, "loop": False, "bones": pose_keys([
    (0.0, with_hips(RISE, 0), {}),
    (0.06, with_hips(TUCK, -30), {}),
    (0.1325, with_hips(TUCK, -112.5), {}),
    (0.205, with_hips(TUCK, -195), {}),
    (0.2775, with_hips(TUCK, -277.5), {}),
    (0.35, with_hips(TUCK, -360), {}),
    (0.5, with_hips(RISE, -360), {}),
])}

# dash: 0.2 s, plays once and holds; hard forward lean, arms swept back, legs trailing.
DASH = {"hips": -12, "torso": -22, "head": 20, "arm_front_upper": -65, "arm_front_lower": 15,
        "arm_back_upper": -75, "arm_back_lower": 15, "leg_front_upper": 30, "leg_front_lower": -15,
        "leg_back_upper": -30, "leg_back_lower": -35, "skirt": -16}
A["dash"] = {"duration": 0.2, "loop": False, "bones": pose_keys([
    (0.0, {"hips": -4, "torso": -10, "head": 8, "arm_front_upper": -25, "arm_back_upper": -30,
           "leg_front_upper": 12, "leg_back_upper": -12, "leg_back_lower": -15}, {}),
    (0.08, DASH, {}),
    (0.2, DASH, {}),
])}

# land: 0.25 s. Impact squash keyed every frame: hips drop and shift back while both
# feet stay planted (grounded exactly by ground.py), knees bend, torso folds forward.
L1, L2 = 292.0, 228.0
def squat(d, s):
    """Grounded crouch: hips down d, shins tilted s degrees (knee forward of the ankle).
    Returns (thigh delta, knee delta, hips dx) that keep each ankle where it stood."""
    import math
    ca = (L1 + L2 - d - L2 * math.cos(math.radians(s))) / L1
    a = math.degrees(math.acos(max(-1.0, min(1.0, ca))))
    dx = -(L1 * math.sin(math.radians(a)) - L2 * math.sin(math.radians(s)))
    return a, -s - a, dx
LAND = [(0 / 30, 34, 8), (1 / 30, 40, 10), (2 / 30, 40, 10), (3 / 30, 34, 8), (4 / 30, 26, 6),
        (5 / 30, 17, 4), (6 / 30, 9, 2), (7 / 30, 3, 1), (0.25, 0, 0)]
land_bones = {b: {"rotate": []} for b in ("leg_front_upper", "leg_front_lower", "leg_back_upper", "leg_back_lower")}
land_bones["hips"] = {"translate": []}
for t, d, s_ in LAND:
    a, b, dx = squat(d, s_)
    t = round(t, 6)
    for side in ("front", "back"):
        land_bones[f"leg_{side}_upper"]["rotate"].append({"time": t, "angle": round(a, 3)})
        land_bones[f"leg_{side}_lower"]["rotate"].append({"time": t, "angle": round(b, 3)})
    land_bones["hips"]["translate"].append({"time": t, "x": round(dx, 3), "y": -d})
upper = pose_keys([
    (0.0, {"torso": -18, "head": 9, "arm_front_upper": 28, "arm_front_lower": 22,
           "arm_back_upper": 20, "arm_back_lower": 20, "skirt": 8}, {}),
    (0.07, {"torso": -26, "head": 14, "arm_front_upper": 40, "arm_front_lower": 30,
            "arm_back_upper": 30, "arm_back_lower": 26, "skirt": 12}, {}),
    (0.25, {}, {}),
])
land_bones.update(upper)
A["land"] = {"duration": 0.25, "loop": False, "bones": land_bones}

# jump's crouch (t=0) uses the same grounded squat.
_a, _b, _dx = squat(45, 10)
for side in ("front", "back"):
    A["jump"]["bones"][f"leg_{side}_upper"]["rotate"][0]["angle"] = round(_a, 3)
    A["jump"]["bones"][f"leg_{side}_lower"]["rotate"][0]["angle"] = round(_b, 3)
A["jump"]["bones"]["hips"]["translate"][0].update({"x": round(_dx, 3), "y": -45})
A["jump"]["bones"]["torso"]["rotate"][0]["angle"] = -24
