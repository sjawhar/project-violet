"""THROWAWAY (bake-off lane G-A): the two manual edits the generated art gets, in place. bakeoff/g-a/edit-art.sh runs
them and records each with `provenance edit`.

  key IMAGE   magenta #ff00ff background -> transparency. Alpha ramps with the color distance from magenta, and
              half-transparent edge pixels have the magenta they were blended with removed (no pink fringe).
  seam IMAGE  makes a backdrop repeat side by side: keeps the columns x1..x2 (x1 in the first eighth, x2 in the
              last eighth) whose 48 px bands at either end look most alike, then crossfades those bands so the
              right edge runs straight into the left one. The width shrinks; Parallax2D repeats at the texture width.

    uv run --no-project --with pillow --with numpy python bakeoff/g-a/art_edit.py key|seam IMAGE
"""

import sys

import numpy as np
from PIL import Image

MAGENTA = np.array([255.0, 0.0, 255.0])
NEAR, FAR = 60.0, 150.0  # color distance from magenta: fully transparent below NEAR, fully opaque above FAR
BAND = 48


def key(path: str) -> None:
    rgb = np.asarray(Image.open(path).convert("RGB"), dtype=np.float64)
    alpha = np.clip((np.linalg.norm(rgb - MAGENTA, axis=2) - NEAR) / (FAR - NEAR), 0.0, 1.0)
    safe = np.where(alpha > 0, alpha, 1.0)[..., None]
    color = np.clip(MAGENTA + (rgb - MAGENTA) / safe, 0, 255)
    rgba = np.dstack([np.where(alpha[..., None] > 0, color, 0), alpha * 255]).round().astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(path)
    print(f"key: {path}: {100 * (alpha == 0).mean():.0f}% transparent")


def seam(path: str) -> None:
    image = Image.open(path)
    mode = "RGBA" if image.mode in ("RGBA", "LA") or "transparency" in image.info else "RGB"
    px = np.asarray(image.convert(mode), dtype=np.float64)
    width = px.shape[1]
    reach = width // 8

    # Premultiplied color, so transparent pixels count as empty whatever their RGB; every 4th row is enough to compare.
    flat = (px[::4, :, :3] * px[::4, :, 3:4] / 255) if mode == "RGBA" else px[::4]

    def mismatch(x1: int, x2: int) -> float:
        # The crossfade blends the last BAND columns (ending at x2) into the first BAND columns (starting at x1):
        # those two bands must look alike, or the blend shows a half-transparent ghost of whatever differs.
        return float(np.abs(flat[:, x2 - BAND + 1 : x2 + 1] - flat[:, x1 : x1 + BAND]).mean())

    _, x1, x2 = min((mismatch(x1, x2), x1, x2) for x1 in range(0, reach, 2) for x2 in range(width - reach, width, 2))
    crop = px[:, x1 : x2 + 1]
    length = crop.shape[1]
    t = np.linspace(0.0, 1.0, BAND, endpoint=False)[None, :, None]
    head = crop[:, length - BAND :] * (1 - t) + crop[:, :BAND] * t
    out = np.concatenate([head, crop[:, BAND : length - BAND]], axis=1)
    Image.fromarray(out.round().astype(np.uint8), mode).save(path)
    print(f"seam: {path}: kept columns {x1}..{x2}, crossfaded {BAND} px, width {width} -> {out.shape[1]}")


if __name__ == "__main__":
    {"key": key, "seam": seam}[sys.argv[1]](sys.argv[2])
