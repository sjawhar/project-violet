"""THROWAWAY (Phase 1 bake-off, Violet glow-up technique B). Finalizes `idle`'s 8 painted
frames the same way trial-b/finalize_frames.py finalized `run`'s 8 frames: for each frame,
union-trim body+scarf to their shared alpha>8 bounding box (keeps the two layers pixel-
aligned), then rescale by the ONE shared RIG_PER_RAW factor the run trial calibrated
against technique A's own round-00 contact-sheet run row (t=0 column, 208 canvas px at
SCALE=0.22 = 945.4545 rig units, divided by run frame 0's own raw 838px bbox height ->
1.128227381210675 -- see trial-b/frames/finalize-record.json's frame "0"). Reusing that
exact constant (not re-deriving a new one from idle's own frame 0) is deliberate: it is
what makes every technique-B animation share one absolute scale with `run`, per
docs/bakeoff/glow-up.md's rounds.md-successor contract ("Calibration: one shared scale").

Writes assets/bakeoff/protagonist/glow-up/trial-b/frames/idle-{body,scarf}-NN.png in place
(overwriting the raw generations) and their per-frame anchors (sole_y, head_x, in the same
rescaled coordinate system) to trial-b/frames/idle-finalize-record.json. idle is a grounded
loop, so every frame's sole lands on the shared ground line at shoot/build time the same
way run's frames do -- this script only computes and records the anchors, exactly like
finalize_frames.py did for run; it does not itself build a row/GIF.
"""

from PIL import Image
import json

RAW_DIR = "assets/bakeoff/protagonist/glow-up/trial-b/frames"
ANIM = "idle"
NFRAMES = 8
ALPHA_THRESH = 8  # strict threshold, matches finalize_frames.py / README.md's own convention

# The one shared scale factor, reused byte-for-byte from run's own calibration
# (trial-b/frames/finalize-record.json's frame "0": rig_per_raw).
RIG_PER_RAW = 1.128227381210675


def strict_bbox(im):
    a = im.split()[-1]
    a2 = a.point(lambda v: 255 if v > ALPHA_THRESH else 0)
    return a2.getbbox()


def load(i, kind):
    return Image.open(f"{RAW_DIR}/{ANIM}-{kind}-{i:02d}.png").convert("RGBA")


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
            if v > ALPHA_THRESH:
                total_w += v
                total += v * x
    return total / total_w if total_w else (left + right) / 2.0


records = {}
for i in range(NFRAMES):
    body = load(i, "body")
    scarf = load(i, "scarf")
    bbody = strict_bbox(body)
    bscarf = strict_bbox(scarf)
    union = (min(bbody[0], bscarf[0]), min(bbody[1], bscarf[1]),
             max(bbody[2], bscarf[2]), max(bbody[3], bscarf[3]))

    # anchors measured on the ORIGINAL (untrimmed) body, before crop/rescale
    sole_y_orig = bbody[3]
    head_x_orig = head_centroid_x(body, bbody)

    body_c = body.crop(union)
    scarf_c = scarf.crop(union)
    new_w = max(1, round(body_c.width * RIG_PER_RAW))
    new_h = max(1, round(body_c.height * RIG_PER_RAW))
    body_r = body_c.resize((new_w, new_h), Image.LANCZOS)
    scarf_r = scarf_c.resize((new_w, new_h), Image.LANCZOS)

    body_path = f"{RAW_DIR}/{ANIM}-body-{i:02d}.png"
    scarf_path = f"{RAW_DIR}/{ANIM}-scarf-{i:02d}.png"
    body_r.save(body_path)
    scarf_r.save(scarf_path)

    sole_y_new = (sole_y_orig - union[1]) * RIG_PER_RAW
    head_x_new = (head_x_orig - union[0]) * RIG_PER_RAW

    records[i] = {
        "union_bbox_orig_1024canvas": union,
        "orig_size": body.size,
        "trimmed_size": body_c.size,
        "final_size": [new_w, new_h],
        "rig_per_raw": RIG_PER_RAW,
        "sole_y": sole_y_new,
        "head_x": head_x_new,
    }
    print(i, records[i])

with open(f"{RAW_DIR}/{ANIM}-finalize-record.json", "w") as f:
    json.dump(records, f, indent=2)
print("done")
