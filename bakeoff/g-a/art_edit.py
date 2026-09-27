"""THROWAWAY (bake-off lane G-A): the manual edit the generated backdrops get, in place. bakeoff/g-a/edit-art.sh runs it
and records it with `provenance edit`.

  seam IMAGE  makes a backdrop repeat side by side: keeps the columns x1..x2 (x1 in the first eighth, x2 in the
              last eighth) whose 48 px bands at either end look most alike, then crossfades those bands so the
              right edge runs straight into the left one. Transparent layers are blended premultiplied, so the
              fully transparent pixels' RGB never bleeds in. The width shrinks; Parallax2D repeats at the texture width.

    uv run --no-project --with pillow --with numpy python bakeoff/g-a/art_edit.py seam IMAGE
"""

import sys

import numpy as np
from PIL import Image

BAND = 48


def seam(path: str) -> None:
    image = Image.open(path)
    mode = "RGBA" if image.mode in ("RGBA", "LA") or "transparency" in image.info else "RGB"
    px = np.asarray(image.convert(mode), dtype=np.float64)
    width = px.shape[1]
    reach = width // 8

    # Premultiplied color, so transparent pixels count as empty whatever their RGB, plus the alpha itself weighted
    # threefold: a shape present in one band and missing from the other is the ghost to avoid. Every 4th row is enough.
    flat = np.dstack([px[::4, :, :3] * px[::4, :, 3:4] / 255, 3 * px[::4, :, 3:4]]) if mode == "RGBA" else px[::4]

    def mismatch(x1: int, x2: int) -> float:
        # The crossfade blends the last BAND columns (ending at x2) into the first BAND columns (starting at x1):
        # those two bands must look alike, or the blend shows a half-transparent ghost of whatever differs.
        return float(np.abs(flat[:, x2 - BAND + 1 : x2 + 1] - flat[:, x1 : x1 + BAND]).mean())

    _, x1, x2 = min((mismatch(x1, x2), x1, x2) for x1 in range(0, reach, 2) for x2 in range(width - reach, width, 2))
    crop = px[:, x1 : x2 + 1].copy()
    if mode == "RGBA":
        crop[..., :3] *= crop[..., 3:4] / 255
    length = crop.shape[1]
    t = np.linspace(0.0, 1.0, BAND, endpoint=False)[None, :, None]
    head = crop[:, length - BAND :] * (1 - t) + crop[:, :BAND] * t
    out = np.concatenate([head, crop[:, BAND : length - BAND]], axis=1)
    if mode == "RGBA":
        alpha = out[..., 3:4]
        out[..., :3] = np.where(alpha > 0, out[..., :3] * 255 / np.where(alpha > 0, alpha, 1), 0)
    Image.fromarray(out.round().astype(np.uint8), mode).save(path)
    print(f"seam: {path}: kept columns {x1}..{x2}, crossfaded {BAND} px, width {width} -> {out.shape[1]}")


if __name__ == "__main__":
    {"seam": seam}[sys.argv[1]](sys.argv[2])
