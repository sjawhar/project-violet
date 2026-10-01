
from PIL import Image
import json

RAW_DIR = "assets/bakeoff/protagonist/glow-up/trial-b/frames"
NFRAMES = 8
ALPHA_THRESH = 8  # matches the project's own convention (README.md: "kept pixels with alpha 1-8" was the bug; strict is > 8)

A_CONTACT_HEIGHT_CANVASPX = 208.0
A_SCALE = 0.22
A_CONTACT_HEIGHT_RIGUNITS = A_CONTACT_HEIGHT_CANVASPX / A_SCALE

def strict_bbox(im):
    a = im.split()[-1]
    # zero out anything <= ALPHA_THRESH, like `magick -trim` with a strict threshold
    a2 = a.point(lambda v: 255 if v > ALPHA_THRESH else 0)
    return a2.getbbox()

def load(i, kind):
    return Image.open(f"{RAW_DIR}/run-{kind}-{i:02d}.png").convert("RGBA")

# calibration from frame 0's body, BEFORE any trim/rescale (raw 1024 canvas)
body0 = load(0, "body")
bbox0 = strict_bbox(body0)
height_raw0 = bbox0[3] - bbox0[1]
RIG_PER_RAW = A_CONTACT_HEIGHT_RIGUNITS / height_raw0
print("RIG_PER_RAW", RIG_PER_RAW, "height_raw0", height_raw0)

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
    union = (min(bbody[0], bscarf[0]), min(bbody[1], bscarf[1]), max(bbody[2], bscarf[2]), max(bbody[3], bscarf[3]))

    # anchors measured on the ORIGINAL (untrimmed) body, before crop/rescale
    sole_y_orig = bbody[3]
    head_x_orig = head_centroid_x(body, bbody)

    body_c = body.crop(union)
    scarf_c = scarf.crop(union)
    new_w = max(1, round(body_c.width * RIG_PER_RAW))
    new_h = max(1, round(body_c.height * RIG_PER_RAW))
    body_r = body_c.resize((new_w, new_h), Image.LANCZOS)
    scarf_r = scarf_c.resize((new_w, new_h), Image.LANCZOS)

    body_path = f"{RAW_DIR}/run-body-{i:02d}.png"
    scarf_path = f"{RAW_DIR}/run-scarf-{i:02d}.png"
    body_r.save(body_path)
    scarf_r.save(scarf_path)

    # anchors in the NEW cropped+rescaled coordinate system
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

with open(f"{RAW_DIR}/finalize-record.json", "w") as f:
    json.dump(records, f, indent=2)
print("done")
