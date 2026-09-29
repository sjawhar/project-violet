"""THROWAWAY (Phase 1 bake-off, Violet glow-up, technique B). Generalizes run's
finalize_frames.py to any held animation: trims each frame's body+scarf pair to their
shared alpha>8 bbox, rescales by the trial's own RIG_PER_RAW (reused unchanged, not
re-derived, per the rules -- "one shared scale... so every animation is the same size as
the run"), and records per-frame anchors in <anim>-finalize-record.json.

Two anchor modes, chosen per animation by the rules in docs/bakeoff/glow-up.md's lane
contract and the glow-up task ("Frames with ground contact... put the soles on the
ground line... airborne frames... place them so the head centroid matches technique A's
head position in the same animation at the same time"):

- grounded (land): records sole_y and head_x/head_y exactly like run's own scheme, so a
  build step can anchor sole_y to the shared ground line the same way run's frames do.
- airborne (jump, fall, double_jump): records head_x/head_y (this frame's own painted
  head centroid, in rig units) AND target_head_x/target_head_y -- technique A's own
  head-slot world centre at the same sample time, computed via spinerig's FK
  (`_placements` + `world_to_canvas`) against the fixed REFERENCE_BOX (rounds.md's "Fixed
  layout", scale=1.0, margin=0, so the value is in raw rig units, comparable across every
  animation, not just this one). A build step places each frame so head_x/head_y lands
  exactly on target_head_x/target_head_y (times whatever canvas_scale it uses) -- no
  ground line at all for an airborne animation.

**Incremental.** Frame indices already present in `<anim>-finalize-record.json` were
trimmed+rescaled by a previous run of this script; their on-disk pixels are no longer raw
1024x1024 generations, so redoing the trim+rescale on them would compound RIG_PER_RAW a
second time. Each run only discovers and processes `<anim>-body-NN.png` indices that are
NOT already in the record (via glob over the frames directory, not a required --nframes
count), merges the new entries into the existing record, and leaves every already-
finalized frame's bytes and record entry untouched. Re-running with nothing new to do
prints "already finalized, nothing to do" and writes no files at all.

**Head-position trust check.** The top-band alpha centroid above is a heuristic, and can
lock onto a flared sleeve, scarf, or hair strand that happens to reach higher than the
hood instead of the head itself (found in `fall` frame 4, round 4's integration pass:
the heuristic put her head off in the flared sleeve, ~180px away from her actual face).
Every genuine head band in this style shows some visible face (skin tone), so a newly
processed frame whose top band has none raises loudly instead of silently recording a
wrong position -- see `skin_fraction()`/`SKIN_MIN_FRACTION`. A frame flagged this way (or
any other known-bad automatic measurement) gets a hand-measured `HEAD_OVERRIDES` entry
instead, in the frame's own original (pre-crop) coordinates.

Run from the repository root:
    uv run --project tools/spinerig python assets/bakeoff/protagonist/glow-up/trial-b/finalize_anim.py \\
        jump --mode airborne
    uv run --project tools/spinerig python assets/bakeoff/protagonist/glow-up/trial-b/finalize_anim.py \\
        land --mode grounded
    uv run --project tools/spinerig python assets/bakeoff/protagonist/glow-up/trial-b/finalize_anim.py \\
        fall --mode airborne
    uv run --project tools/spinerig python assets/bakeoff/protagonist/glow-up/trial-b/finalize_anim.py \\
        double_jump --mode airborne

`--times` is optional: given explicitly (one value per newly-processed index, in index
order) when a frame's own sample time doesn't fall on an even grid, or left out to let
each new index `i` default to `t = i * (animation_duration / frame_count)` -- the run
trial's own `FRAME_DT = duration/NFRAMES` convention, generalized. `--nframes` is
likewise optional, used only to size that default grid; when omitted it is the discovered
frame count (existing + new).
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

# Explicit per-frame head-position overrides, in the frame's ORIGINAL (untrimmed
# 1024-canvas, pre-crop/rescale) coordinate space -- the same space head_centroid()
# below measures in, before the union-crop transform converts it into the record's own
# final coordinates. Populated when the automatic top-band heuristic (below) locks onto
# something that is not the head -- most often a flared sleeve or scarf reaching higher
# than the hood -- and a human re-measures the real head position by eye.
#
# ("fall", 4): the heuristic's top-18%-band centroid landed on this pose's flared sleeve
# tip (which reaches above the hood crown here), not the head. Re-measured by
# VioletRound4Integrate, 2026-09-29, as the alpha-weighted centroid of a hand-picked
# hood+face box on the CURRENT (already finalized) fall-body-04.png, [385,210]-[620,425],
# verified against a red-crosshair overlay, then converted back to this original-space
# coordinate system via the frame's own union_bbox_orig_1024canvas/rig_per_raw. See
# fall-finalize-record.json frame "4"'s own "head_correction" note for the full story.
HEAD_OVERRIDES: dict[tuple[str, int], tuple[float, float]] = {
    ("fall", 4): (656.9768968282829, 313.8777457761695),
}

# A frame whose top band is genuinely the head always shows some of her face (every
# painted frame in this style keeps "a clearly readable young face in profile with a
# visible eye, brow, nose and mouth" -- technique-trial.md's own body prompt, reused
# unchanged by every later lane). A flared sleeve or scarf tip has none of that warm
# skin-tone color at all. Measured on the known-good/known-bad frames on hand when this
# check was added: every correctly-measured head band had at least 0.27% skin-toned
# pixels; the one known bad case (fall frame 4, before its HEAD_OVERRIDES entry above)
# had 0.00%. This threshold sits with a wide margin below the lowest genuine value.
SKIN_MIN_FRACTION = 0.0015


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


def skin_fraction(im: Image.Image, bbox, band_frac: float = 0.18) -> float:
    """The fraction of the same top band head_centroid() measures that is warm skin-tone
    color -- a cheap, semantically-grounded trust check: every one of this style's heads
    shows a visible face (see SKIN_MIN_FRACTION's own comment), so a top band with none
    of that color is not the head, whatever its alpha centroid says."""
    left, upper, right, lower = bbox
    band_h = max(1, int((lower - upper) * band_frac))
    rgb = im.convert("RGB")
    a = im.split()[-1]
    pxrgb = rgb.load()
    pxa = a.load()
    skin = total = 0
    for y in range(upper, upper + band_h):
        for x in range(left, right):
            if pxa[x, y] <= ALPHA_THRESH:
                continue
            total += 1
            r, g, b = pxrgb[x, y]
            if r > 180 and g > 130 and b > 90 and (r - b) > 40 and (r - g) < 60:
                skin += 1
    return skin / total if total else 0.0


def technique_a_head_targets(anim: str, times: dict[int, float]) -> dict[int, tuple[float, float]]:
    """Technique A's own head-slot world centre at each requested frame index's time, in
    raw rig units, y-down, against the fixed REFERENCE_BOX (rounds.md) -- the same
    coordinate space every technique's frames are ultimately composited into, so a value
    measured here is comparable across animations, not just within one spinerig render
    call."""
    with open(RIG_JSON) as f:
        spine = json.load(f)
    animation = spine["animations"][anim]
    out = {}
    for i, t in times.items():
        placements = R._placements(spine, animation, t)
        _, _attachment, cx, cy, _rotation = next(p for p in placements if p[0] == "head")
        out[i] = R.world_to_canvas(cx, cy, REFERENCE_BOX, 1.0, 0.0)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("anim")
    parser.add_argument("--mode", choices=["airborne", "grounded"], required=True)
    parser.add_argument("--nframes", type=int, default=None, help="total frame count, for the default even time grid; discovered from disk when omitted")
    parser.add_argument("--times", type=float, nargs="*", default=None, help="airborne mode only: one sample time per NEWLY processed index, in index order; defaults to an even i*(duration/nframes) grid")
    args = parser.parse_args()

    indices = sorted(
        int(p.stem.rsplit("-", 1)[-1])
        for p in FRAMES_DIR.glob(f"{args.anim}-body-*.png")
    )
    if not indices:
        parser.error(f"no {args.anim}-body-NN.png frames found in {FRAMES_DIR}")

    record_path = FRAMES_DIR / f"{args.anim}-finalize-record.json"
    records: dict[int, dict] = {}
    if record_path.exists():
        with open(record_path) as f:
            records = {int(k): v for k, v in json.load(f).items()}

    # Frames already in the record were trimmed+rescaled by a previous run -- redoing the
    # trim+rescale on them would compound RIG_PER_RAW a second time. Only process indices
    # new since the last run; leave already-finalized frames' bytes and record entries
    # untouched (not even a re-serialize of the unchanged JSON, so hashes stay stable).
    to_process = [i for i in indices if i not in records]
    if not to_process:
        print(f"{args.anim}: frames {indices} already finalized, nothing to do")
        return 0
    print(f"{args.anim}: finalizing new frames {to_process} (already finalized: {sorted(records)})")

    nframes = args.nframes or len(indices)
    if args.mode == "airborne":
        if args.times is not None:
            if len(args.times) != len(to_process):
                parser.error("--times must give exactly one value per newly-processed index")
            times = dict(zip(to_process, args.times))
        else:
            with open(RIG_JSON) as f:
                spine = json.load(f)
            duration = R.animation_duration(spine["animations"][args.anim])
            frame_dt = duration / nframes
            times = {i: i * frame_dt for i in to_process}
        a_targets = technique_a_head_targets(args.anim, times)

    for i in to_process:
        body = load(args.anim, i, "body")
        scarf = load(args.anim, i, "scarf")
        bbody = strict_bbox(body)
        bscarf = strict_bbox(scarf)
        union = (min(bbody[0], bscarf[0]), min(bbody[1], bscarf[1]),
                 max(bbody[2], bscarf[2]), max(bbody[3], bscarf[3]))

        # anchors measured on the ORIGINAL (untrimmed) body, before crop/rescale
        sole_y_orig = bbody[3]
        if (args.anim, i) in HEAD_OVERRIDES:
            head_x_orig, head_y_orig = HEAD_OVERRIDES[(args.anim, i)]
        else:
            head_x_orig, head_y_orig = head_centroid(body, bbody)
            trust = skin_fraction(body, bbody)
            if trust < SKIN_MIN_FRACTION:
                raise RuntimeError(
                    f"{args.anim} frame {i}: the top-band head heuristic's own region has "
                    f"only {trust:.3%} skin-tone pixels (< {SKIN_MIN_FRACTION:.3%}) -- it "
                    "almost certainly caught a sleeve, scarf, or hair strand reaching above "
                    "the hood, not the actual head (every frame in this style shows a "
                    "visible face). Look at the frame, hand-measure the real head_x/head_y "
                    "in its ORIGINAL (pre-crop) coordinates, and add "
                    f"(\"{args.anim}\", {i}) to HEAD_OVERRIDES with that value."
                )

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
            target_x, target_y = a_targets[i]
            record["t"] = times[i]
            record["target_head_x"] = target_x
            record["target_head_y"] = target_y
            record["anchor_mode"] = "airborne_head"
        records[i] = record
        print(i, record)

    with open(record_path, "w") as f:
        json.dump({str(k): v for k, v in sorted(records.items())}, f, indent=2)
    print("wrote", record_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
