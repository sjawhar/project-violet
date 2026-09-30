"""Consumer-level checks for the painted-character preview's scarf attachment."""
from pathlib import Path
import importlib
import json
import math

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
GLOWUP = ROOT / "assets/bakeoff/protagonist/glow-up"


@pytest.mark.parametrize("scale", [0.22, 1.0])
def test_scarf_collar_remains_visible_over_opaque_clothing(tmp_path, monkeypatch, scale):
    monkeypatch.syspath_prepend(str(GLOWUP))
    renderer = importlib.import_module("shoot_b")
    monkeypatch.setattr(renderer, "FRAMES_DIR", tmp_path)
    robe = (80, 60, 40, 255)
    collar = (230, 230, 230, 255)
    Image.new("RGBA", (40, 60), robe).save(tmp_path / "idle-body-00.png")
    Image.new("RGBA", (20, 20), collar).save(tmp_path / "idle-scarf-00.png")
    # Neck (18, 12) and knot (10, 5) coincide with this layer offset.
    record = {0: {"head_x": 0, "sole_y": 60, "scarf_offset_final": [8, 7]}}
    cell = renderer.render_cell_b("idle", 0, record, scale, 100, 100, {})
    x = round(renderer.HEAD_X_FRACTION * 100 + 18 * scale)
    y = round(renderer.GROUND_Y_FRACTION * 100 - 60 * scale + 12 * scale)
    assert cell.getpixel((x, y)) == collar, "The body painted over the scarf's neck wrap"


@pytest.mark.parametrize(
    "pin",
    json.loads((GLOWUP / "scarf_attachments.json").read_text())["frames"],
    ids=lambda p: f"{p['animation']}-{p['index']:02}",
)
def test_painted_scarf_knot_meets_the_annotated_neck(pin):
    """The landmarks were visually authored, independently of the old crop offsets."""
    name = "finalize-record.json" if pin["animation"] == "run" else f"{pin['animation']}-finalize-record.json"
    record = json.loads((GLOWUP / "trial-b/frames" / name).read_text())[str(pin["index"])]
    offset = record.get("scarf_offset_final", [0, 0])
    placed_knot = [offset[j] + pin["scarf_knot"][j] for j in (0, 1)]
    assert math.dist(placed_knot, pin["body_neck"]) <= 1, (
        f"{pin['animation']} frame {pin['index']}: scarf knot {placed_knot} "
        f"misses the neck at {pin['body_neck']}"
    )
