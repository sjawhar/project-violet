"""THROWAWAY (Phase 1 bake-off, Violet glow-up). Production-QA fix for two of the trial's
run scarf layers (`run-scarf-01.png`, `run-scarf-05.png`), which the trial's critic and
its own "Honest read of frame consistency" section both flagged: the scarf painted as
three overlapping, semi-transparent copies of the same ribbon at slightly different
offsets, instead of one opaque flowing shape (technique-trial.md, "Honest read of frame
consistency"). The body frames and the other six scarves are untouched.

Each fixed scarf is a fresh `tools/gen` call using that frame's EXISTING (already
finalized/cropped) body PNG as `--input`, exactly the recipe the trial itself used for
every scarf (verified: `run-scarf-00.png`'s own provenance records `run-body-00.png`'s
CURRENT, already-finalized sha256 as its input, not a separate raw canvas).

The new scarf is a FRESH raw 1024x1024 generation, so its own raw-canvas coordinates are
not guaranteed to fall inside the frame's ORIGINAL crop box (`union_bbox_orig_1024canvas`,
computed once from the original raw body+scarf pair) -- and empirically here the new,
healthier single-piece scarf trails slightly further than the old defective one on both
ends. Since the body file must not change, this script crops the new scarf to its OWN
alpha bbox (not reused/clamped to the old box), rescales it by the SAME shared
`rig_per_raw` factor (never re-derived), and records the resulting origin's offset from
the body's existing crop origin as `scarf_offset_final` (in the already-rescaled, final
coordinate space) -- so `build.py`'s `render_cell` can shift the scarf paste by that extra
delta on top of the frame's one shared body-derived anchor, keeping the two layers
correctly registered without moving or re-cropping the body.

Run from the repository root:
    uv run --project tools/spinerig python assets/bakeoff/protagonist/glow-up/trial-b/finalize_run_scarf_fix.py
"""

from PIL import Image
import json

FRAMES_DIR = "assets/bakeoff/protagonist/glow-up/trial-b/frames"
ALPHA_THRESH = 8  # matches finalize_frames.py's own convention

with open(f"{FRAMES_DIR}/finalize-record.json") as f:
    RECORD = json.load(f)

FIXED_FRAMES = [1, 5]


def strict_bbox(im):
    a = im.split()[-1]
    a2 = a.point(lambda v: 255 if v > ALPHA_THRESH else 0)
    return a2.getbbox()


for i in FIXED_FRAMES:
    rec = RECORD[str(i)]
    body_box = tuple(rec["union_bbox_orig_1024canvas"])
    rig_per_raw = rec["rig_per_raw"]

    raw_path = f"{FRAMES_DIR}/run-scarf-{i:02d}-fix-raw.png"
    raw = Image.open(raw_path).convert("RGBA")

    scarf_box = strict_bbox(raw)
    cropped = raw.crop(scarf_box)
    new_w = max(1, round(cropped.width * rig_per_raw))
    new_h = max(1, round(cropped.height * rig_per_raw))
    resized = cropped.resize((new_w, new_h), Image.LANCZOS)

    # Offset (final, rescaled space) from the body's own crop origin to this scarf's own
    # crop origin, so a renderer that already places the body via its per-frame anchor
    # can shift the scarf by this extra delta to keep both layers registered.
    offset_x = (scarf_box[0] - body_box[0]) * rig_per_raw
    offset_y = (scarf_box[1] - body_box[1]) * rig_per_raw

    final_path = f"{FRAMES_DIR}/run-scarf-{i:02d}.png"
    resized.save(final_path)
    rec["scarf_bbox_orig_1024canvas"] = list(scarf_box)
    rec["scarf_final_size"] = [new_w, new_h]
    rec["scarf_offset_final"] = [offset_x, offset_y]
    print(
        f"frame {i}: wrote {final_path} at {resized.size}, "
        f"scarf_offset_final={(offset_x, offset_y)} (body untouched at {rec['final_size']})"
    )

with open(f"{FRAMES_DIR}/finalize-record.json", "w") as f:
    json.dump(RECORD, f, indent=2)
print("done")
