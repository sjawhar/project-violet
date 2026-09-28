"""THROWAWAY (Phase 1 bake-off): put the soles exactly on the floor (skeleton y = 0 =
feet_y_px). Called by mkrig.py on the rig.json it just wrote.
1. Setup: shift each lower-leg pivot so that foot's lowest opaque point is at y = 0.
2. Planted keys (land, jump's crouch): even out the two feet with a small thigh/knee trade.
3. Grounded animations: re-key `hips` translate so the lowest foot touches y = 0 at every
   sampled frame (hips translate moves both legs rigidly, so one pass is exact)."""
import json, math
from pathlib import Path

from feet import spine_of, feet, FEET

FPS = 60
L1 = 292.0


def sample(keys, t, field):
    if t <= keys[0]["time"]:
        return keys[0].get(field, 0.0)
    if t >= keys[-1]["time"]:
        return keys[-1].get(field, 0.0)
    for a, b in zip(keys, keys[1:]):
        if a["time"] <= t <= b["time"]:
            f = (t - a["time"]) / (b["time"] - a["time"]) if b["time"] > a["time"] else 0
            return a.get(field, 0.0) + f * (b.get(field, 0.0) - a.get(field, 0.0))


def ground(RIG: Path) -> None:
    def save(rig):
        RIG.write_text(json.dumps(rig, indent=2) + "\n")

    rig = json.loads(RIG.read_text())
    for _ in range(3):
        spine = spine_of(RIG)
        f = feet(spine, "__setup", 0)
        for part in rig["parts"]:
            if part["slot"] in FEET:
                h = next(s for s in spine["skins"][0]["attachments"][part["slot"]].values())["height"]
                part["pivot"][1] = round(part["pivot"][1] + f[part["slot"]][0] / h, 5)
        save(rig)
    print("setup feet", {k: round(v[0], 2) for k, v in feet(spine_of(RIG), "__setup", 0).items()})

    # Feet-planted keys (land every frame, jump's crouch): the two feet differ in shape, so
    # after the shared squat one can sit a pixel or two above the other. Swing that leg's
    # thigh back toward vertical by the matching angle (knee compensates, shin angle kept).
    spine = spine_of(RIG)
    for anim, times in (("land", None), ("jump", [0.0])):
        bones = rig["animations"][anim]["bones"]
        for side in ("front", "back"):
            up, lo = bones[f"leg_{side}_upper"]["rotate"], bones[f"leg_{side}_lower"]["rotate"]
            for k_up, k_lo in zip(up, lo):
                t = k_up["time"]
                if times is not None and t not in times:
                    continue
                fs = feet(spine, anim, t)
                m = min(v[0] for v in fs.values())
                r = fs[f"leg_{side}_lower"][0] - m
                a = math.radians(k_up["angle"])
                if r > 0.3 and abs(math.sin(a)) > 0.05:
                    d = math.degrees(r / (L1 * math.sin(a)))
                    k_up["angle"] = round(k_up["angle"] - d, 3)
                    k_lo["angle"] = round(k_lo["angle"] + d, 3)
    save(rig)

    GROUNDED = {"run": "all", "dash": "all", "land": "all", "jump": "clamp"}
    spine = spine_of(RIG)
    for anim, which in GROUNDED.items():
        a = rig["animations"][anim]
        dur = a["duration"]
        times = [round(i / FPS, 6) for i in range(round(dur * FPS))] + [dur]
        hips = a["bones"].setdefault("hips", {})
        base = hips.get("translate", [{"time": 0, "x": 0, "y": 0}])
        new = {}
        for t in times:
            m = min(v[0] for v in feet(spine, anim, t).values())
            if which == "clamp":
                m = min(m, 0.0)
            new[t] = {"time": t, "x": round(sample(base, t, "x"), 3), "y": round(sample(base, t, "y") - m, 3)}
        hips["translate"] = [new[t] for t in sorted(new)]
    save(rig)
