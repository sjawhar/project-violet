"""Finalize script for technique B's airborne animations (fall, double_jump), generalizing
finalize_frames.py's trim+rescale approach to painted frames that don't touch the ground.

Usage: uv run --project tools/spinerig python assets/bakeoff/protagonist/glow-up/trial-b/finalize_anim.py <anim>

For each frame NN present as <anim>-body-NN.png / <anim>-scarf-NN.png in frames/:
  1. Union-bbox trim (alpha>8) shared between body and scarf, exactly like finalize_frames.py.
  2. Rescale by RIG_PER_RAW = 1.128227381210675, the exact factor finalize_frames.py calibrated
     for run's frame 0 (technique-trial.md's calibration), reused unchanged here so every
     animation is the same size as run.
  3. Record head_x/head_y: the local alpha-weighted centroid of the body layer's top 18% band
     (by height), in the new cropped+rescaled coordinate system -- the same heuristic
     finalize_frames.py's head_centroid_x uses for x, extended here to also return y. Valid
     because every fall/double_jump pose keeps both hands at or below the crown of the hood by
     prompt constraint, so the topmost significant alpha mass is the head/hood.
  4. Record target_head_x/target_head_y: technique A's own head-slot world center at this
     frame's own designated time t (FRAME_DT * i), converted to the same rig-unit "canvas"
     space via spinerig.render._placements() + world_to_canvas(cx, cy, REFERENCE_BOX, 1.0, 0)
     (REFERENCE_BOX is rounds.md's fixed layout box; scale=1.0 keeps it in raw rig units, not
     canvas px, so a later build step can multiply by whatever canvas_scale it renders at).

A later build step positions each frame with (no ground line, since every frame here is
airborne): dx = (target_head_x - head_x) * canvas_scale, dy = (target_head_y - head_y) * canvas_scale.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "tools/spinerig/src")
from PIL import Image
from spinerig import render as R

RAW_DIR = "assets/bakeoff/protagonist/glow-up/trial-b/frames"
ALPHA_THRESH = 8
RIG_PER_RAW = 1.128227381210675  # reused unchanged from trial-b/frames/finalize-record.json (run's own calibration)

REFERENCE_BOX = {"x": -763.6, "y": -40.0, "width": 1316.9, "height": 1434.7}  # rounds.md's fixed layout
RIG_PATH = "assets/bakeoff/protagonist/rig/violet.json"

FRAME_DT = {"fall": 0.6 / 5, "double_jump": 0.5 / 5}


def strict_bbox(im):
    a = im.split()[-1]
    a2 = a.point(lambda v: 255 if v > ALPHA_THRESH else 0)
    return a2.getbbox()


def load(anim, i, kind):
    return Image.open(f"{RAW_DIR}/{anim}-{kind}-{i:02d}.png").convert("RGBA")


def head_centroid(im, bbox, band_frac=0.18):
    left, upper, right, lower = bbox
    band_h = max(1, int((lower - upper) * band_frac))
    a = im.split()[-1]
    px = a.load()
    total_w = total_x = total_y = 0.0
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


def target_head_canvas(anim, t):
    with open(RIG_PATH) as f:
        spine = json.load(f)
    animation = spine["animations"][anim]
    for slot_name, attachment, cx, cy, rot in R._placements(spine, animation, t):
        if slot_name == "head":
            return R.world_to_canvas(cx, cy, REFERENCE_BOX, 1.0, 0.0)
    raise RuntimeError("no head slot")


def main():
    anim = sys.argv[1]
    dt = FRAME_DT[anim]
    frames_dir = Path(RAW_DIR)
    indices = sorted(
        int(p.stem.split("-")[-1])
        for p in frames_dir.glob(f"{anim}-body-*.png")
    )
    if not indices:
        raise SystemExit(f"no {anim}-body-NN.png frames found in {RAW_DIR}")

    out_path = f"{RAW_DIR}/{anim}-finalize-record.json"
    records = {}
    if Path(out_path).exists():
        with open(out_path) as f:
            records = {int(k): v for k, v in json.load(f).items()}

    # Frames already in the record were trimmed+rescaled by a previous run of this
    # script and their on-disk pixels are no longer raw 1024x1024 generations -- redoing
    # the trim+rescale on them would compound RIG_PER_RAW a second time. Only process
    # indices new since the last run; leave already-finalized frames' bytes and record
    # entries untouched.
    to_process = [i for i in indices if i not in records]
    if not to_process:
        print(f"{anim}: frames {indices} already finalized, nothing to do")
        return
    print(f"{anim}: finalizing new frames {to_process} (already finalized: {sorted(records)})")

    for i in to_process:
        body = load(anim, i, "body")
        scarf = load(anim, i, "scarf")
        bbody = strict_bbox(body)
        bscarf = strict_bbox(scarf)
        union = (min(bbody[0], bscarf[0]), min(bbody[1], bscarf[1]),
                 max(bbody[2], bscarf[2]), max(bbody[3], bscarf[3]))

        head_x_orig, head_y_orig = head_centroid(body, bbody)

        body_c = body.crop(union)
        scarf_c = scarf.crop(union)
        new_w = max(1, round(body_c.width * RIG_PER_RAW))
        new_h = max(1, round(body_c.height * RIG_PER_RAW))
        body_r = body_c.resize((new_w, new_h), Image.LANCZOS)
        scarf_r = scarf_c.resize((new_w, new_h), Image.LANCZOS)

        body_path = f"{RAW_DIR}/{anim}-body-{i:02d}.png"
        scarf_path = f"{RAW_DIR}/{anim}-scarf-{i:02d}.png"
        body_r.save(body_path)
        scarf_r.save(scarf_path)

        head_x_new = (head_x_orig - union[0]) * RIG_PER_RAW
        head_y_new = (head_y_orig - union[1]) * RIG_PER_RAW

        t = i * dt
        target_x, target_y = target_head_canvas(anim, t)

        records[i] = {
            "t": t,
            "union_bbox_orig_1024canvas": union,
            "orig_size": body.size,
            "trimmed_size": body_c.size,
            "final_size": [new_w, new_h],
            "rig_per_raw": RIG_PER_RAW,
            "head_x": head_x_new,
            "head_y": head_y_new,
            "target_head_x": target_x,
            "target_head_y": target_y,
        }
        print(i, records[i])

    with open(out_path, "w") as f:
        json.dump({str(k): v for k, v in sorted(records.items())}, f, indent=2)
    print("wrote", out_path)


if __name__ == "__main__":
    main()
