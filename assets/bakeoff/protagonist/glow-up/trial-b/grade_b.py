"""THROWAWAY (Phase 1 bake-off, Violet glow-up, round 5). A deterministic value pass over
every technique-B painted frame (`frames/<anim>-{body,scarf}-NN.png`, all seven
animations), fixing round 4's gap 3 (`round-04/critic.md`: "the scarf is a pale
semi-transparent haze and the mid-brown body sits close to the gray, so the figure
doesn't separate from the background"). Three independent lane glow-ups found the same
lever for a painted character in a game world: a darker body against a lighter ground,
plus a warm rim; an outline alone read as a "sticker".

- **Body layer:** darkens each pixel's own value (`V = max(R, G, B)`) with a curve that
  is a no-op at `V=255` and strongest around the mid-tones, then adds a soft, low-
  opacity warm tint in a narrow band a few px inside the body's own alpha edge (not an
  outline: a linear falloff over a handful of px, smoothed by one small blur, blended
  as color -- never a full-opacity stroke). Scaling R, G and B by one shared per-pixel
  factor changes only V and leaves hue and saturation exactly as they were (for
  `c' = c*s`, `max' = max*s` and `min' = min*s`, so `(max'-min')/max' = (max-min)/max`),
  which is how this stays in the approved palette family -- same hues, same warm-brown
  robe, just darker.
- **Scarf layer:** untouched color (it must stay neutral gray -- lanes tint it), but its
  alpha is solidified: a small morphological close removes stray low-alpha interior
  speckles, then a single narrow-sigma blur of the closed silhouette leaves only a
  couple of px of soft edge around the true silhouette; everywhere else inside is fully
  opaque, everywhere else outside is fully transparent.

**Idempotent.** Every transform reads the frozen `<name>.round-04.png` copy beside each
live frame (`rounds.md`'s "Frozen inputs" convention), never the live file itself, so
re-running this script never compounds a previous run's darkening or alpha changes.

No image generation, no network calls, no randomness: pure per-pixel post-processing,
$0.

Run from the repository root:
    uv run --project tools/spinerig python assets/bakeoff/protagonist/glow-up/trial-b/grade_b.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

FRAMES_DIR = Path(__file__).resolve().parent / "frames"
ALPHA_THRESH = 8  # matches finalize_anim.py's own "kept pixels with alpha 1-8 was the bug" convention

# character-rig.md's seven animations, with each one's painted frame count
# (trial-b/frames/<anim>-{body,scarf}-NN.png, NN in range(count)).
ANIM_COUNTS = {"idle": 8, "run": 8, "jump": 5, "fall": 5, "double_jump": 5, "dash": 3, "land": 3}

# Body value curve: scale(V) = 1 - BODY_K*(1 - V/255). At V=255 scale=1 (no-op,
# protecting highlights/skin/face); at V=0 the pixel is already black so the factor
# doesn't matter. Calibrated against every technique-B body frame's alpha>128 pixels,
# including the warm rim below: pooled median luminance across all 74 frames lands at
# ~86, inside rounds.md round 5's 80-90 target, against the #808080 backdrop (round-05's
# own measurement, grade_b.py's module test).
BODY_K = 0.53

# Warm rim: blended (not stroked) into a narrow band inside the body's own alpha edge --
# an exact linear falloff over RIM_LEVELS raw px (chessboard-distance erosion rings,
# smoothed by one small Gaussian to soften the staircase), never touching pixels more
# than RIM_LEVELS px from the edge. At the full-size sheet's own canvas_scale
# (shoot.py's SCALE=0.22; raw px = final px / scale) this renders as roughly a 1-2 final
# px accent; at the in-game sheet's own, much smaller scale the same raw band renders
# under a px, so the rim is a full-size flourish and the value darkening (scale-
# invariant, a color property) is what carries separation at gameplay size.
BODY_CLOSE_PX = 3
RIM_LEVELS = 6
RIM_STRENGTH = 0.30
RIM_COLOR = (255, 205, 140)  # warm amber, within the reference's "warm skin tones" family

# Scarf alpha solidify: SCARF_CLOSE_PX closes small interior alpha speckles
# (morphological close: dilate then erode); the closed silhouette is then blurred with a
# small sigma so only SCARF_EDGE_PX raw px of soft transition survive around the true
# edge (~1.5 final px at the full-size sheet's canvas_scale=0.22) -- "the outer 1-2 px
# stay soft" from round 5's own brief. A Gaussian's 1%-99% transition spans about
# 4.65*sigma, so sigma = SCARF_EDGE_PX / 4.65.
SCARF_CLOSE_PX = 3
SCARF_EDGE_PX = 7


def _odd(n: float) -> int:
    n = max(1, int(round(n)))
    return n if n % 2 == 1 else n + 1


def _close(mask_img: Image.Image, radius_px: int) -> Image.Image:
    size = _odd(2 * radius_px + 1)
    return mask_img.filter(ImageFilter.MaxFilter(size)).filter(ImageFilter.MinFilter(size))


def _erosion_levels(mask_img: Image.Image, levels: int) -> list[np.ndarray]:
    """Boolean arrays at chessboard-erosion depths 0..levels: depth 0 is the mask
    itself, depth k is eroded by k raw px (k applications of a 3x3 min filter)."""
    out = [np.array(mask_img) > 127]
    cur = mask_img
    for _ in range(levels):
        cur = cur.filter(ImageFilter.MinFilter(3))
        out.append(np.array(cur) > 127)
    return out


def _rim_weight(closed: Image.Image) -> np.ndarray:
    """A per-pixel weight in [0, 1], 1 at the true edge fading linearly to 0 at
    RIM_LEVELS px inward, 0 beyond -- smoothed once to soften the erosion staircase."""
    depths = _erosion_levels(closed, RIM_LEVELS)
    weight = np.zeros(depths[0].shape, dtype=np.float64)
    for r in range(RIM_LEVELS):
        ring = depths[r] & ~depths[r + 1]
        weight[ring] = 1.0 - r / RIM_LEVELS
    smoothed = Image.fromarray((weight * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(1.0))
    return np.array(smoothed).astype(np.float64) / 255.0


def frame_path(anim: str, kind: str, i: int, *, frozen: bool) -> Path:
    suffix = ".round-04.png" if frozen else ".png"
    return FRAMES_DIR / f"{anim}-{kind}-{i:02d}{suffix}"


def grade_body(im: Image.Image) -> Image.Image:
    arr = np.array(im.convert("RGBA")).astype(np.float64)
    rgb, a = arr[..., :3], arr[..., 3]
    opaque = a > 0

    v = rgb.max(axis=-1)
    scale = 1.0 - BODY_K * (1.0 - v / 255.0)
    graded = rgb * scale[..., None]

    binary = a > ALPHA_THRESH
    mask_img = Image.fromarray((binary * 255).astype(np.uint8), "L")
    closed = _close(mask_img, BODY_CLOSE_PX)
    weight = _rim_weight(closed) * RIM_STRENGTH
    weight = np.where(opaque, weight, 0.0)

    rim = np.array(RIM_COLOR, dtype=np.float64)
    graded = graded * (1 - weight[..., None]) + rim[None, None, :] * weight[..., None]

    out = np.zeros_like(arr)
    out[..., :3] = np.clip(graded, 0, 255)
    out[..., 3] = a
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def grade_scarf(im: Image.Image) -> Image.Image:
    arr = np.array(im.convert("RGBA"))
    a = arr[..., 3]

    binary = (a > ALPHA_THRESH).astype(np.uint8) * 255
    mask_img = Image.fromarray(binary, "L")
    closed = _close(mask_img, SCARF_CLOSE_PX)
    sigma = SCARF_EDGE_PX / 4.65
    ramp = closed.filter(ImageFilter.GaussianBlur(sigma))

    new_alpha = np.array(ramp).astype(np.float64)
    new_alpha = np.where(new_alpha < 2.0, 0.0, new_alpha)
    new_alpha = np.where(new_alpha > 253.0, 255.0, new_alpha)

    out = arr.copy()
    out[..., 3] = np.clip(new_alpha, 0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def process_all() -> list[Path]:
    written = []
    for anim, n in ANIM_COUNTS.items():
        for i in range(n):
            body_in = frame_path(anim, "body", i, frozen=True)
            scarf_in = frame_path(anim, "scarf", i, frozen=True)
            if not body_in.is_file() or not scarf_in.is_file():
                raise FileNotFoundError(
                    f"missing frozen input for {anim} frame {i}: expected {body_in} and {scarf_in} "
                    "(freeze the live frame as <name>.round-04.png first; see rounds.md's 'Frozen inputs')"
                )
            body_out = frame_path(anim, "body", i, frozen=False)
            scarf_out = frame_path(anim, "scarf", i, frozen=False)
            grade_body(Image.open(body_in)).save(body_out)
            grade_scarf(Image.open(scarf_in)).save(scarf_out)
            written += [body_out, scarf_out]
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args(argv)
    written = process_all()
    print(f"graded {len(written)} frame layer(s) from their frozen round-04 copies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
