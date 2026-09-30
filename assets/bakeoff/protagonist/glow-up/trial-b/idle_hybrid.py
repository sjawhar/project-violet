"""THROWAWAY (Phase 1 bake-off, Violet glow-up, round 8). Rebuilds `idle`'s 8 body and 8
scarf frames as a hybrid: ONE held painting per layer, animated by a deterministic
procedural warp instead of 8 separate from-scratch paintings -- fixing round 7's (the
kept round's) gap 1, "boiling" (`round-07/critic.md`: "every frame is redrawn from
scratch, so the character flickers... 60-90% of the idle figure's pixels change every
frame even though she is standing still... hood outline, hair strands, robe hem, face
and scarf shape are all different each frame").

Both source paintings are chosen from the 8 that already exist, not repainted, and both
are ALREADY graded -- this script only geometrically warps already-correct pixels, so it
never re-runs `grade_b.py`'s value/alpha grading (rounds.md's "start from already-graded
frames, so they match"):

- **Body: `idle-body-00.png`** (frame 0, the rig's own "neutral rest" pose -- both feet
  flat, arms loose, torso upright, head level, per `idle.md`'s pose table). Chosen over
  the other 7 because it is the one pose that is already what our own procedural
  breathing is about to animate FROM -- starting the hold from an already-leaned-back
  breathing extreme (e.g. frame 4) would double up with the warp below -- and, by eye
  (`/tmp/vr8-backup/idle-body-00-head.png` at 3x zoom during this round's own review),
  it is on-model with a cleanly readable profile face (eye, brow, nose, mouth all
  distinct), same as every other frame; there was no defect to avoid. It has carried
  round 5's `grade_b.py` body grading (darkened value + warm rim) since round 5 and
  hasn't changed since.
- **Scarf: `idle-scarf-00.png`** (frame 0 of round 6's repaint). Of the 8 existing scarf
  paintings, this one has the cleanest single knot and the longest, most elongated
  single-direction drape (by eye, `/tmp/vr8-backup/idle-scarf-tops-montage.png` during
  this round's review: frames 4-6 bunch into a fatter, shorter knot, closer to the
  critic's later "knotted sack" read of round 6's scarf as a whole). It is also the
  scarf frame that was originally paired with `idle-body-00.png` at generation time
  (`idle.md`: each scarf frame was generated using that same index's body frame as its
  own pose/framing reference), so its own `scarf_offset_final` (from
  `idle-finalize-record.json`'s frame "0") is already correctly calibrated to
  `idle-body-00.png` specifically, with no cross-frame realignment guesswork needed.

## The two procedural motions

**Breathing (body).** A piecewise vertical stretch above a fixed waist line
(`WAIST_Y_FRAC` of the body's own raw height -- the sash/belt band, verified by eye on a
percentage-gridded render of `idle-body-00.png` during this round's review): every pixel
at or below the waist, including both feet and the entire skirt/hem, is resampled with
`frac=0` (an exact identity copy, not merely "close"), so it is bit-for-bit identical in
every one of the 8 output frames; only the torso/shoulders/hood/head above the waist
stretch, by a peak factor `1 + BREATH_AMPLITUDE` (2%, the top of rounds.md's own "1-2%"
brief) at the loop's midpoint. The stretch factor follows a raised cosine, `breath(t) =
(1 - cos(2*pi*t/DURATION)) / 2`: 0 at `t=0`, 1 (peak) at `t=DURATION/2`, back to 0 at
`t=DURATION` -- the same rise-then-return shape as the rig's own three keyframes
(`t=0, 0.5, 1.0`) that `idle.md`'s original 8 paintings were each hand-posed to.

**Sway (scarf).** A piecewise horizontal shear below a fixed pivot near the neck (a
weighted alpha centroid of the scarf's own topmost `PIVOT_ROW_BAND` px -- the knot):
every row at or above the pivot doesn't move at all; every row below it shifts sideways
by `(row - pivot_y) * tan(angle(t))`, so the tail drifts like a hanging cloth pinned at
the collar while the knot stays anchored. `angle(t) = SCARF_SWAY_DEG * sin(2*pi*t/
DURATION)` (a plain sine, one full side-to-side cycle per loop, `SCARF_SWAY_DEG=3`,
"a few degrees"). Because the shear only ever moves pixels horizontally, and the pivot
row itself never moves, the scarf's own placement offset (`scarf_offset_final`) is one
constant vector for all 8 frames -- the drift is carried entirely by the warped pixels,
not by nudging the paste position frame to frame.

Both curves are sampled at `idle`'s own established 8-frame convention, `t = i *
DURATION/8` for `i = 0..7` (`idle.md`: "8 fps-equivalent hold time").

## Anchors

Every output frame's `sole_y` (the lowest alpha>`ALPHA_THRESH` row) lands at the exact
same value, because the identity zone below the waist is copied verbatim in every frame
-- round 7's critic measured a 21 px sole_y range across the old 8 paintings; this
hybrid's is 0. `torso_x` (the body's own whole-mask alpha centroid) and `head_x` (the
top-18%-band centroid, `finalize_idle.py`'s own convention) are re-measured fresh on
each frame's actual output pixels rather than assumed constant, though the warp is
purely vertical so they only drift by hundredths of a px. `place_dy_offset` is 0 for
every frame -- this hybrid's `sole_y` is accurate enough on its own that it needs none of
round 6's old per-frame manual correction.

## Padding

Both warps need transparent margin the source paintings don't have, sized once from the
peak amplitude actually used (not from the theoretical bound of `docs/bakeoff/
character-rig.md`'s "1-2%" brief), so every frame's canvas is the same size:
`PAD_TOP = ceil(waist_y * BREATH_AMPLITUDE) + 4` px added above the body (the chest
lifts into it at the breath's peak); `PAD_H = ceil(max shear distance) + 4` px added on
both sides of the scarf (the tail swings into it at the sway's peak). Padding is never
retrimmed away afterward -- transparent PNG margin costs nothing at render time and
keeps every frame's own coordinate system identical, which is what keeps
`scarf_offset_final` a single constant instead of a per-frame value.

## Idempotent and frozen inputs

Always reads the FROZEN `idle-body-00.round-07.png` / `idle-scarf-00.round-07.png`
copies (never the live `idle-body-00.png` / `idle-scarf-00.png`, which this same run
overwrites), so re-running this script twice in a row produces byte-identical output
both times. Before its first write in a given working copy, it freezes whatever is currently
live at `idle-{body,scarf}-NN.png` (all 8 indices each) and `idle-finalize-record.json`
as `<name>.round-07.<ext>` beside each (rounds.md's "Frozen inputs" convention: round 8
is about to overwrite the state round 7 left behind), skipping any freeze whose target
already exists so a second run is a no-op on that front too. This script does not touch
any `.provenance.json` sidecar; that is a separate step (rounds.md's own established
split -- `grade_b.py` and `finalize_idle.py` don't either).

Run from the repository root:
    uv run --project tools/spinerig python assets/bakeoff/protagonist/glow-up/trial-b/idle_hybrid.py
"""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

FRAMES_DIR = Path(__file__).resolve().parent / "frames"
ANIM = "idle"
NFRAMES = 8
ALPHA_THRESH = 8  # matches grade_b.py's / finalize_idle.py's own convention
DURATION = 1.0  # rig-src/anims.py's A["idle"].duration

SOURCE_BODY_INDEX = 0
SOURCE_SCARF_INDEX = 0
FREEZE_TAG = "round-07"  # the latest kept round, about to be superseded by round 8

WAIST_Y_FRAC = 0.36  # the sash/belt band on idle-body-00.png, verified by eye
BREATH_AMPLITUDE = 0.02  # peak extra height above the waist (2%, rounds.md's "1-2%")

SCARF_SWAY_DEG = 3.0  # peak shear angle, "a few degrees"
PIVOT_ROW_BAND = 15  # rows 0..PIVOT_ROW_BAND-1 define the scarf's neck-knot pivot x
PIVOT_Y = 5.0  # the pivot row itself: high enough to sit inside the knot, not the tail

# frame 0's own original scarf_offset_final (idle-finalize-record.json, before this
# round): the calibrated body<->scarf alignment for this exact index-0 pair, reused
# verbatim as the base every hybrid frame's own offset is padding-adjusted from.
BASE_SCARF_OFFSET = [-5.641136906053374, 311.3907572141463]


def breath_fraction(t: float) -> float:
    """Raised cosine: 0 at t=0, 1 at t=DURATION/2, 0 at t=DURATION."""
    return (1 - math.cos(2 * math.pi * t / DURATION)) / 2


def sway_fraction(t: float) -> float:
    """Plain sine: 0 at t=0, +1 at t=DURATION/4, 0 at t=DURATION/2, -1 at 3*DURATION/4."""
    return math.sin(2 * math.pi * t / DURATION)


def _premultiply(arr: np.ndarray) -> np.ndarray:
    a = arr[..., 3:4] / 255.0
    rgb = arr[..., :3] * a
    return np.concatenate([rgb, arr[..., 3:4].astype(np.float64)], axis=-1)


def _unpremultiply(arr: np.ndarray) -> np.ndarray:
    a = arr[..., 3:4]
    rgb = np.where(a > 0, arr[..., :3] / np.where(a > 0, a, 1.0) * 255.0, 0.0)
    return np.clip(np.concatenate([rgb, a], axis=-1), 0, 255)


def warp_body(im: Image.Image, waist_y: float, pad_top: int, s: float) -> Image.Image:
    """Vertical stretch by factor `s` above `waist_y`, identity at/below it, with
    `pad_top` px of transparent headroom added above for the stretch to grow into."""
    arr = np.array(im.convert("RGBA")).astype(np.float64)
    h, w, _ = arr.shape
    pm = _premultiply(arr)
    hd = h + pad_top
    y_dst = np.arange(hd, dtype=np.float64)
    y_local = y_dst - pad_top
    y_src = np.where(y_local >= waist_y, y_local, waist_y - (waist_y - y_local) / s)
    valid = (y_src >= -1e-9) & (y_src <= h - 1 + 1e-9)
    y_src_c = np.clip(y_src, 0, h - 1)
    y0 = np.floor(y_src_c).astype(np.int64)
    y1 = np.minimum(y0 + 1, h - 1)
    frac = (y_src_c - y0)[:, None, None]
    blended = pm[y0] * (1 - frac) + pm[y1] * frac
    blended[~valid] = 0.0
    out = np.clip(np.round(_unpremultiply(blended)), 0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def shear_scarf(im: Image.Image, pivot_x: float, pivot_y: float, pad_h: int, angle_deg: float) -> Image.Image:
    """Horizontal shear below `pivot_y` (rows at/above it are untouched), `pad_h` px of
    transparent margin added on both sides for the shear to swing the tail into."""
    arr = np.array(im.convert("RGBA")).astype(np.float64)
    h, w, _ = arr.shape
    pm = _premultiply(arr)
    wd = w + 2 * pad_h
    depth = np.clip(np.arange(h, dtype=np.float64) - pivot_y, 0, None)
    shift = depth * math.tan(math.radians(angle_deg))  # (h,)
    x_dst = np.arange(wd, dtype=np.float64)
    x_src = (x_dst[None, :] - pad_h) - shift[:, None]  # (h, wd)
    valid = (x_src >= -1e-9) & (x_src <= w - 1 + 1e-9)
    x_src_c = np.clip(x_src, 0, w - 1)
    x0 = np.floor(x_src_c).astype(np.int64)
    x1 = np.minimum(x0 + 1, w - 1)
    frac = (x_src_c - x0)[..., None]
    row_idx = np.arange(h)[:, None]
    blended = pm[row_idx, x0] * (1 - frac) + pm[row_idx, x1] * frac
    blended[~valid] = 0.0
    out = np.clip(np.round(_unpremultiply(blended)), 0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def centroid_x_band(arr: np.ndarray, y0: int, y1: int) -> float:
    band = arr[y0:y1]
    a = band[..., 3].astype(np.float64)
    xs = np.arange(band.shape[1])
    return float((a.sum(axis=0) * xs).sum() / a.sum())


def measure_body_anchors(body_arr: np.ndarray) -> dict:
    mask = body_arr[..., 3] > ALPHA_THRESH
    ys, xs = np.where(mask)
    sole_y = float(ys.max())
    a = body_arr[..., 3].astype(np.float64)
    xs_all = np.arange(body_arr.shape[1])
    torso_x = float((a.sum(axis=0) * xs_all).sum() / a.sum())
    top18 = max(1, int(body_arr.shape[0] * 0.18))
    head_x = centroid_x_band(body_arr, 0, top18)
    return {"sole_y": sole_y, "torso_x": torso_x, "head_x": head_x, "place_dy_offset": 0.0}


def freeze(name: str) -> None:
    """Copy the currently-live `name` to `<stem>.FREEZE_TAG.<ext>` beside it, if that
    frozen path doesn't already exist (idempotent across re-runs)."""
    live = FRAMES_DIR / name
    stem, ext = name.rsplit(".", 1)
    frozen = FRAMES_DIR / f"{stem}.{FREEZE_TAG}.{ext}"
    if frozen.exists():
        return
    shutil.copyfile(live, frozen)
    print(f"froze {live.name} -> {frozen.name}")


def freeze_all_live_idle_files() -> None:
    for i in range(NFRAMES):
        freeze(f"{ANIM}-body-{i:02d}.png")
        freeze(f"{ANIM}-scarf-{i:02d}.png")
    freeze(f"{ANIM}-finalize-record.json")


def main() -> int:
    freeze_all_live_idle_files()

    body_im = Image.open(FRAMES_DIR / f"{ANIM}-body-{SOURCE_BODY_INDEX:02d}.{FREEZE_TAG}.png").convert("RGBA")
    scarf_im = Image.open(FRAMES_DIR / f"{ANIM}-scarf-{SOURCE_SCARF_INDEX:02d}.{FREEZE_TAG}.png").convert("RGBA")
    body_h = np.array(body_im).shape[0]
    scarf_h = np.array(scarf_im).shape[0]

    waist_y = WAIST_Y_FRAC * body_h
    pad_top = math.ceil(waist_y * BREATH_AMPLITUDE) + 4

    scarf_arr0 = np.array(scarf_im)
    pivot_x = centroid_x_band(scarf_arr0, 0, PIVOT_ROW_BAND)
    shift_max = (scarf_h - 1 - PIVOT_Y) * math.tan(math.radians(SCARF_SWAY_DEG))
    pad_h = math.ceil(shift_max) + 4
    new_scarf_offset = [BASE_SCARF_OFFSET[0] - pad_h, BASE_SCARF_OFFSET[1]]

    records: dict[str, dict] = {}
    for i in range(NFRAMES):
        t = i * DURATION / NFRAMES

        s = 1 + BREATH_AMPLITUDE * breath_fraction(t)
        body_out = warp_body(body_im, waist_y, pad_top, s)
        body_out.save(FRAMES_DIR / f"{ANIM}-body-{i:02d}.png")

        angle = SCARF_SWAY_DEG * sway_fraction(t)
        scarf_out = shear_scarf(scarf_im, pivot_x, PIVOT_Y, pad_h, angle)
        scarf_out.save(FRAMES_DIR / f"{ANIM}-scarf-{i:02d}.png")

        anchors = measure_body_anchors(np.array(body_out))
        anchors["scarf_offset_final"] = new_scarf_offset
        records[str(i)] = anchors
        print(i, f"t={t:.3f} s={s:.5f} angle={angle:.3f}deg sole_y={anchors['sole_y']:.3f} torso_x={anchors['torso_x']:.3f}")

    with open(FRAMES_DIR / f"{ANIM}-finalize-record.json", "w") as f:
        json.dump(records, f, indent=2)
    print(f"wrote 8 {ANIM} body frames, 8 scarf frames, and {ANIM}-finalize-record.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
