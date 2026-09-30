"""THROWAWAY (Phase 1 bake-off, Violet glow-up, round 9). Driver helpers for round 9's
scarf-only repaint pass: freezing pre-overwrite inputs (rounds.md's "Frozen inputs"
convention), computing scarf_offset_final for a scarf-only regen against an unchanged
body (finalize_run_scarf_fix.py's own recipe, generalized to any anim/index), applying
trial-b/grade_b.py's grade_scarf directly, and re-pointing round-08's own stale shot
provenance at the frozen copies.
"""
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grade_b  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tools" / "provenance" / "src"))
from provenance.config import find_config, load_config  # noqa: E402
from provenance.record import add_human_edit  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[6]
FRAMES_DIR = Path(__file__).resolve().parent / "frames"
GLOWUP_DIR = FRAMES_DIR.parents[1]
ALPHA_THRESH = 8
RIG_PER_RAW = 1.128227381210675
BY = "VioletRound9 (Claude)"

CONFIG = load_config(find_config(Path.cwd()))


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def strict_bbox(im: Image.Image):
    a = im.split()[-1]
    a2 = a.point(lambda v: 255 if v > ALPHA_THRESH else 0)
    return a2.getbbox()


def freeze(path: Path, freeze_round: int, reason: str) -> Path:
    """Copy path + its sidecar to <name>.round-NN.<ext> before path gets overwritten."""
    frozen = path.with_name(f"{path.stem}.round-{freeze_round:02d}{path.suffix}")
    sidecar = path.with_name(path.name + ".provenance.json")
    frozen_sidecar = frozen.with_name(frozen.name + ".provenance.json")
    if frozen.exists():
        print(f"  (already frozen: {frozen.name})")
        return frozen
    frozen.write_bytes(path.read_bytes())
    record = json.loads(sidecar.read_text())
    record["asset"] = frozen.name
    frozen_sidecar.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    add_human_edit(
        CONFIG,
        frozen,
        by=BY,
        description=f"Frozen as {frozen.name} for round {freeze_round}'s own shot provenance "
        f"(identical bytes to the live {path.name} through round {freeze_round}) before glow-up "
        f"round 9 {reason}; see assets/bakeoff/protagonist/glow-up/rounds.md.",
        now=datetime.now(UTC),
    )
    print(f"  froze {path.name} -> {frozen.name}")
    return frozen


def repoint_shot_inputs(shot_path: Path, renames: dict[str, str]) -> int:
    """Rewrite a round-08 shot's own generator.inputs paths for files that got frozen,
    keeping sha256 identical (frozen copy = same bytes), then append a human_edits note."""
    sidecar = shot_path.with_name(shot_path.name + ".provenance.json")
    record = json.loads(sidecar.read_text())
    changed = []
    for entry in record["generator"]["inputs"]:
        name = entry["path"].split("/")[-1]
        if name in renames:
            entry["path"] = entry["path"].rsplit("/", 1)[0] + "/" + renames[name]
            changed.append(name)
    if not changed:
        return 0
    sidecar.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    add_human_edit(
        CONFIG,
        shot_path,
        by=BY,
        description=(
            "Round 9: re-pointed this round-08 shot record's own stale generator.inputs entries "
            f"({', '.join(changed)}) at their round-08-frozen copies (same bytes/sha256, since "
            "round 9 overwrote the live scarf-only repaint targets) -- same correction round 6/7 made "
            "for their own predecessor rounds' shot records."
        ),
        now=datetime.now(UTC),
    )
    print(f"  re-pointed {shot_path.name}: {changed}")
    return len(changed)


def load_finalize_record(anim: str) -> dict:
    name = "finalize-record.json" if anim == "run" else f"{anim}-finalize-record.json"
    path = FRAMES_DIR / name
    return path, json.loads(path.read_text())


def finalize_scarf_only(anim: str, index: int, raw_scarf_path: Path) -> tuple[float, float]:
    """finalize_run_scarf_fix.py's recipe, generalized: crop the freshly generated raw
    scarf to its own alpha bbox, rescale by RIG_PER_RAW, and compute scarf_offset_final
    (final/rescaled coordinate space) relative to this frame's already-recorded
    union_bbox_orig_1024canvas -- the SAME raw-canvas coordinate frame the body's own
    original crop was measured in, since this regen's --input was that same (unchanged)
    body PNG. Overwrites <anim>-scarf-<NN>.png in place; updates the finalize record."""
    record_path, records = load_finalize_record(anim)
    rec = records[str(index)]
    body_box = tuple(rec["union_bbox_orig_1024canvas"])
    rig_per_raw = rec["rig_per_raw"]
    assert abs(rig_per_raw - RIG_PER_RAW) < 1e-9

    raw = Image.open(raw_scarf_path).convert("RGBA")
    scarf_box = strict_bbox(raw)
    cropped = raw.crop(scarf_box)
    new_w = max(1, round(cropped.width * rig_per_raw))
    new_h = max(1, round(cropped.height * rig_per_raw))
    resized = cropped.resize((new_w, new_h), Image.LANCZOS)

    offset_x = (scarf_box[0] - body_box[0]) * rig_per_raw
    offset_y = (scarf_box[1] - body_box[1]) * rig_per_raw

    final_path = FRAMES_DIR / f"{anim}-scarf-{index:02d}.png"
    resized.save(final_path)
    rec["scarf_bbox_orig_1024canvas"] = list(scarf_box)
    rec["scarf_final_size"] = [new_w, new_h]
    rec["scarf_offset_final"] = [offset_x, offset_y]
    record_path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")
    print(f"  {anim} frame {index}: wrote {final_path.name} at {resized.size}, scarf_offset_final={(offset_x, offset_y)}")
    return offset_x, offset_y


def grade_scarf_inplace(anim: str, index: int) -> None:
    path = FRAMES_DIR / f"{anim}-scarf-{index:02d}.png"
    graded = grade_b.grade_scarf(Image.open(path))
    graded.save(path)
    print(f"  graded {path.name} (grade_b.grade_scarf, alpha solidify)")


def edit_provenance(path: Path, description: str) -> None:
    add_human_edit(CONFIG, path, by=BY, description=description, now=datetime.now(UTC))
    print(f"  provenance edit: {path.name}")


def measure_std(anim: str, index: int, alpha_thresh: int = 200) -> tuple[float, float, int]:
    import numpy as np

    path = FRAMES_DIR / f"{anim}-scarf-{index:02d}.png"
    arr = np.array(Image.open(path).convert("RGBA"))
    a = arr[..., 3]
    opaque = a > alpha_thresh
    lum = arr[..., :3].astype(np.float64).max(axis=-1)
    vals = lum[opaque]
    return float(vals.mean()), float(vals.std()), int(opaque.sum())
