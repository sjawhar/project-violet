"""THROWAWAY (Phase 1 bake-off, Violet glow-up, technique B, jump/land). Generalizes
run's finalize_frames.py to any held animation: trims each frame's body+scarf pair to
their shared alpha>8 bbox, rescales by the trial's own RIG_PER_RAW (reused unchanged, not
re-derived, per the rules -- "one shared scale... so every animation is the same size as
the run"), and records per-frame anchors in <anim>-finalize-record.json.

Two anchor modes, chosen per animation by the rules in docs/bakeoff/glow-up.md's lane
contract and the glow-up task ("Frames with ground contact... put the soles on the
ground line... airborne frames... place them so the head centroid matches technique A's
head position in the same animation at the same time"):

- grounded (land): records sole_y and head_x/head_y exactly like run's own scheme, so a
  build step can anchor sole_y to the shared ground line the same way run's frames do.
- airborne (jump): records head_x/head_y (this frame's own painted head centroid, in
  rig units) AND target_head_x/target_head_y -- technique A's own head-slot world centre
  at the same sample time, computed via spinerig's FK (`_placements` + `world_to_canvas`)
  against the fixed REFERENCE_BOX (rounds.md's "Fixed layout", scale=1.0, margin=0, so
  the value is in raw rig units, comparable across every animation, not just this one).
  A build step places each frame so head_x/head_y lands exactly on target_head_x/
  target_head_y (times whatever canvas_scale it uses) -- no ground line at all for jump.

Run from the repository root:
    uv run --project tools/spinerig python assets/bakeoff/protagonist/glow-up/trial-b/finalize_anim.py \\
        jump --mode airborne --nframes 5 --times 0.0 0.1 0.2 0.3 0.4
    uv run --project tools/spinerig python assets/bakeoff/protagonist/glow-up/trial-b/finalize_anim.py \\
        land --mode grounded --nframes 3
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "tools" / "spinerig" / "src"))
from spinerig import render as R  # noqa: E402

FRAMES_DIR = Path(__file__).resolve().parent / "frames"
ALPHA_THRESH = 8  # README.md: "kept pixels with alpha 1-8" was the bug; strict is > 8

# Reused verbatim from the run trial's own calibration (technique-trial.md,
# finalize_frames.py): calibrated once against technique A's round-00 contact-sheet.png
# run row, t=0 column (208 canvas px at SCALE=0.22 = 945.4545 rig units), divided by the
# run's own frame 0 raw body bbox height (838 px). One shared scale for every animation,
# not re-derived per animation.
RIG_PER_RAW = 1.128227381210675

RIG_JSON = Path(__file__).resolve().parents[2] / "rig" / "violet.json"
# rounds.md's "Fixed layout": skeleton space, rig units, root at the feet.
REFERENCE_BOX = {"x": -763.6, "y": -40.0, "width": 1316.9, "height": 1434.7}


def strict_bbox(im: Image.Image):
    a = im.split()[-1]
    a2 = a.point(lambda v: 255 if v > ALPHA_THRESH else 0)
    return a2.getbbox()


def load(anim: str, i: int, kind: str) -> Image.Image:
    return Image.open(FRAMES_DIR / f"{anim}-{kind}-{i:02d}.png").convert("RGBA")


def head_centroid(im: Image.Image, bbox, band_frac: float = 0.18):
    """Alpha-weighted centroid of the top band of bbox (the head/hood region) -- same
    heuristic as finalize_frames.py's head_centroid_x, extended to also return y."""
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
    if total_w == 0:
        return (left + right) / 2.0, upper + band_h / 2.0
    return total_x / total_w, total_y / total_w


def technique_a_head_targets(anim: str, times: list[float]) -> dict[float, tuple[float, float]]:
    """Technique A's own head-slot world centre at each of `times`, in raw rig units,
    y-down, against the fixed REFERENCE_BOX (rounds.md) -- the same coordinate space
    every technique's frames are ultimately composited into, so a value measured here is
    comparable across animations, not just within one spinerig render call."""
    with open(RIG_JSON) as f:
        spine = json.load(f)
    animation = spine["animations"][anim]
    out = {}
    for t in times:
        placements = R._placements(spine, animation, t)
        _, _attachment, cx, cy, _rotation = next(p for p in placements if p[0] == "head")
        out[t] = R.world_to_canvas(cx, cy, REFERENCE_BOX, 1.0, 0.0)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("anim")
    parser.add_argument("--mode", choices=["airborne", "grounded"], required=True)
    parser.add_argument("--nframes", type=int, required=True)
    parser.add_argument("--times", type=float, nargs="*", help="airborne mode only: sample time per frame, same order as frame indices")
    args = parser.parse_args()

    if args.mode == "airborne":
        if not args.times or len(args.times) != args.nframes:
            parser.error("--times must give exactly --nframes values for airborne mode")
        a_targets = technique_a_head_targets(args.anim, args.times)

    records = {}
    for i in range(args.nframes):
        body = load(args.anim, i, "body")
        scarf = load(args.anim, i, "scarf")
        bbody = strict_bbox(body)
        bscarf = strict_bbox(scarf)
        union = (min(bbody[0], bscarf[0]), min(bbody[1], bscarf[1]),
                 max(bbody[2], bscarf[2]), max(bbody[3], bscarf[3]))

        # anchors measured on the ORIGINAL (untrimmed) body, before crop/rescale
        sole_y_orig = bbody[3]
        head_x_orig, head_y_orig = head_centroid(body, bbody)

        body_c = body.crop(union)
        scarf_c = scarf.crop(union)
        new_w = max(1, round(body_c.width * RIG_PER_RAW))
        new_h = max(1, round(body_c.height * RIG_PER_RAW))
        body_r = body_c.resize((new_w, new_h), Image.LANCZOS)
        scarf_r = scarf_c.resize((new_w, new_h), Image.LANCZOS)
        body_r.save(FRAMES_DIR / f"{args.anim}-body-{i:02d}.png")
        scarf_r.save(FRAMES_DIR / f"{args.anim}-scarf-{i:02d}.png")

        # anchors in the NEW cropped+rescaled coordinate system
        sole_y_new = (sole_y_orig - union[1]) * RIG_PER_RAW
        head_x_new = (head_x_orig - union[0]) * RIG_PER_RAW
        head_y_new = (head_y_orig - union[1]) * RIG_PER_RAW

        record = {
            "union_bbox_orig_1024canvas": union,
            "orig_size": list(body.size),
            "trimmed_size": list(body_c.size),
            "final_size": [new_w, new_h],
            "rig_per_raw": RIG_PER_RAW,
            "head_x": head_x_new,
            "head_y": head_y_new,
        }
        if args.mode == "grounded":
            record["sole_y"] = sole_y_new
            record["anchor_mode"] = "grounded"
        else:
            t = args.times[i]
            target_x, target_y = a_targets[t]
            record["t"] = t
            record["target_head_x"] = target_x
            record["target_head_y"] = target_y
            record["anchor_mode"] = "airborne_head"
        records[i] = record
        print(i, record)

    with open(FRAMES_DIR / f"{args.anim}-finalize-record.json", "w") as f:
        json.dump(records, f, indent=2)
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
