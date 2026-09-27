"""THROWAWAY (lane G-A): draws flat placeholder part images for placeholder.violet-rig.json, so the rig tests'
spinerig fixture needs no painted art and no binary is committed. Run by make-fixture.sh:
uv run --project tools/spinerig python placeholder_parts.py OUT_DIR"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw

# slot -> (width, height, fill). Every part runs along its bone from its joint: the image's up-axis points along the
# bone (the rig gives it rotation -90, pivot on the bottom edge), as character-rig.md asks. The character faces right;
# back limbs are darker than front ones.
PARTS = {
    "head": (44, 44, "#e8c9a0"),
    "torso": (40, 60, "#8a8078"),
    "hips": (44, 40, "#6f665f"),
    "arm_back_upper": (14, 36, "#5d5650"),
    "arm_back_lower": (12, 36, "#5d5650"),
    "arm_front_upper": (14, 36, "#a39890"),
    "arm_front_lower": (12, 36, "#a39890"),
    "leg_back_upper": (18, 48, "#4f4944"),
    "leg_back_lower": (16, 50, "#4f4944"),
    "leg_front_upper": (18, 48, "#948a82"),
    "leg_front_lower": (16, 50, "#948a82"),
    # White, so the slot color (the active Resonance color) shows as-is.
    "scarf1": (10, 26, "#f4f4f4"),
    "scarf2": (10, 26, "#f4f4f4"),
    "scarf3": (10, 26, "#f4f4f4"),
}

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
for slot, (width, height, fill) in PARTS.items():
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width - 1, height - 1), fill=fill, outline="#2d2540", width=2)
    if slot == "head":  # an eye on the facing side, so a flip shows
        draw.rectangle((width - 14, 14, width - 8, 20), fill="#2d2540")
    image.save(out / f"{slot}.png")
