"""THROWAWAY: deterministic idle breathing, weight shift, arm sway and head tilt.

Uses the already-graded round-07 source paintings. Lower-body registration is
measured from the unchanged skirt/feet region, so upper-body motion cannot move
the planted feet. Eight frames cover the one-second idle loop. The body rises
14 source pixels (about 3 rendered pixels); the scarf retains its 3-degree sway.
Regenerate from the repository root:
    uv run --project tools/spinerig --with numpy python assets/bakeoff/protagonist/glow-up/trial-b/idle_hybrid.py
Freeze outgoing frame files and update provenance before running; the renderer
writes live frames and their placement record, never provenance sidecars.
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

FRAMES_DIR = Path(__file__).resolve().parent / "frames"
OUT_DIR = FRAMES_DIR

NFRAMES = 8
ALPHA_THRESH = 8
DURATION = 1.0

WAIST_Y_FRAC = 0.36
REACH1_BAND = 120.0
BREATH_RISE_PX = 14.0
SHIFT_X_PX = 5.0
SETTLE_Y_PX = 6.0
WEIGHT_PHASE_LAG = 0.28

NECK_Y = 270.0
TILT_PEAK_DEG = 1.5

ARM_PIVOT_Y = 385.0
ARM_SWAY_PEAK_DEG = 2.5
ARM_LAG = 0.12
ARM_MASK_Y0 = 355.0
ARM_FEATHER_Y0 = 30.0
ARM_MASK_Y1 = 585.0
ARM_FEATHER_Y1 = 30.0
ARM_MASK_X1 = 230.0
ARM_FEATHER_X1 = 45.0
STABLE_Y0 = 620.0  # comfortably below ARM_MASK_Y1's own fade-out -- torso_x's own anchor band

SCARF_SWAY_DEG = 3.0
PIVOT_ROW_BAND = 15
PIVOT_Y = 5.0
BASE_SCARF_OFFSET = [-5.641136906053374, 311.3907572141463]


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def breath_fraction(t):
    return (1 - math.cos(2 * math.pi * t / DURATION)) / 2


def weight_ease(t, lag):
    return (1 - math.cos(2 * math.pi * (t - lag) / DURATION)) / 2


def x_ease(t, lag):
    return math.sin(2 * math.pi * (t - lag) / DURATION)


def sway_fraction(t):
    return math.sin(2 * math.pi * t / DURATION)


def _premultiply(arr):
    a = arr[..., 3:4] / 255.0
    rgb = arr[..., :3] * a
    return np.concatenate([rgb, arr[..., 3:4].astype(np.float64)], axis=-1)


def _unpremultiply(arr):
    a = arr[..., 3:4]
    rgb = np.where(a > 0, arr[..., :3] / np.where(a > 0, a, 1.0) * 255.0, 0.0)
    return np.clip(np.concatenate([rgb, a], axis=-1), 0, 255)


def reach1_row(y_local, waist_y, band):
    frac = (waist_y - y_local) / band
    return smoothstep(frac)


def reach2_row(y_local, neck_y):
    frac = (neck_y - y_local) / neck_y
    return smoothstep(frac)


def body_pass1(im, waist_y, pad_top, pad_side, rise_px, shift_x_px, tilt_px_at_top):
    """Combined breath-rise + weight-shift(x,y) + head-tilt-shear, all a function of
    y_local only (uniform across each row). Returns a padded RGBA uint8 array."""
    arr = np.array(im.convert("RGBA")).astype(np.float64)
    h, w, _ = arr.shape
    pm = _premultiply(arr)
    hd = h + pad_top
    wd = w + 2 * pad_side

    y_dst = np.arange(hd, dtype=np.float64) - pad_top  # local y (0 = original row 0)
    r1 = reach1_row(y_dst, waist_y, REACH1_BAND)  # (hd,)
    r2 = reach2_row(y_dst, NECK_Y)  # (hd,)

    y_src_row = y_dst + rise_px * r1  # (hd,)
    x_shift_row = shift_x_px * r1 + tilt_px_at_top * r2  # (hd,) raw px, + = content moves right

    x_dst = np.arange(wd, dtype=np.float64) - pad_side  # local x (0 = original col 0)
    x_src = x_dst[None, :] - x_shift_row[:, None]  # (hd, wd)
    y_src = np.broadcast_to(y_src_row[:, None], (hd, wd))

    valid = (y_src >= -1e-9) & (y_src <= h - 1 + 1e-9) & (x_src >= -1e-9) & (x_src <= w - 1 + 1e-9)
    y_src_c = np.clip(y_src, 0, h - 1)
    x_src_c = np.clip(x_src, 0, w - 1)
    y0 = np.floor(y_src_c).astype(np.int64)
    y1 = np.minimum(y0 + 1, h - 1)
    x0 = np.floor(x_src_c).astype(np.int64)
    x1 = np.minimum(x0 + 1, w - 1)
    fy = (y_src_c - y0)[..., None]
    fx = (x_src_c - x0)[..., None]

    v00 = pm[y0, x0]
    v01 = pm[y0, x1]
    v10 = pm[y1, x0]
    v11 = pm[y1, x1]
    blended = v00 * (1 - fy) * (1 - fx) + v01 * (1 - fy) * fx + v10 * fy * (1 - fx) + v11 * fy * fx
    blended[~valid] = 0.0
    out = np.clip(np.round(_unpremultiply(blended)), 0, 255).astype(np.uint8)
    return out


def arm_mask(y_local, x_local):
    ymask = smoothstep((y_local - ARM_MASK_Y0) / ARM_FEATHER_Y0) * smoothstep((ARM_MASK_Y1 - y_local) / ARM_FEATHER_Y1)
    xmask = smoothstep((ARM_MASK_X1 - x_local) / ARM_FEATHER_X1)
    return ymask * xmask


def arm_sway_pass(arr_u8, pivot_y, angle_deg):
    """2D-masked horizontal shear, operating on the pass-1 output (already padded, so
    y_local/x_local below match pass-1's own local frame directly -- no extra pad)."""
    arr = arr_u8.astype(np.float64)
    h, w, _ = arr.shape
    pm = _premultiply(arr)
    y_local = np.arange(h, dtype=np.float64)
    x_local = np.arange(w, dtype=np.float64)
    yy, xx = np.meshgrid(y_local, x_local, indexing="ij")
    depth = np.clip(yy - pivot_y, 0, None)
    shift = depth * math.tan(math.radians(angle_deg))
    m = arm_mask(yy, xx)
    x_src = xx - shift * m
    valid = (x_src >= -1e-9) & (x_src <= w - 1 + 1e-9)
    x_src_c = np.clip(x_src, 0, w - 1)
    x0 = np.floor(x_src_c).astype(np.int64)
    x1 = np.minimum(x0 + 1, w - 1)
    fx = (x_src_c - x0)[..., None]
    row_idx = np.broadcast_to(np.arange(h)[:, None], (h, w))
    blended = pm[row_idx, x0] * (1 - fx) + pm[row_idx, x1] * fx
    blended[~valid] = 0.0
    out = np.clip(np.round(_unpremultiply(blended)), 0, 255).astype(np.uint8)
    return out


def shear_scarf(im, pivot_x, pivot_y, pad_h, angle_deg):
    arr = np.array(im.convert("RGBA")).astype(np.float64)
    h, w, _ = arr.shape
    pm = _premultiply(arr)
    wd = w + 2 * pad_h
    depth = np.clip(np.arange(h, dtype=np.float64) - pivot_y, 0, None)
    shift = depth * math.tan(math.radians(angle_deg))
    x_dst = np.arange(wd, dtype=np.float64)
    x_src = (x_dst[None, :] - pad_h) - shift[:, None]
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


def centroid_x_band(arr, y0, y1):
    band = arr[y0:y1]
    a = band[..., 3].astype(np.float64)
    xs = np.arange(band.shape[1])
    return float((a.sum(axis=0) * xs).sum() / a.sum())


def measure_stable_torso_x(body_arr, stable_y0_padded):
    """Alpha centroid of rows well below the arm-sway mask's own fade-out (not just the
    waist -- the arm sway extends below it too), identical across all 8 frames by
    construction, so it never introduces sway into the horizontal placement anchor."""
    y0 = int(math.ceil(stable_y0_padded))
    band = body_arr[y0:]
    a = band[..., 3].astype(np.float64)
    xs = np.arange(band.shape[1])
    return float((a.sum(axis=0) * xs).sum() / a.sum())


def measure_anchors(body_arr, stable_y0_padded):
    mask = body_arr[..., 3] > ALPHA_THRESH
    ys, xs = np.where(mask)
    sole_y = float(ys.max())
    torso_x = measure_stable_torso_x(body_arr, stable_y0_padded)
    top18 = max(1, int(body_arr.shape[0] * 0.18))
    head_x = centroid_x_band(body_arr, 0, top18)
    return sole_y, torso_x, head_x


def main():
    body_im = Image.open(FRAMES_DIR / "idle-body-00.round-07.png").convert("RGBA")
    scarf_im = Image.open(FRAMES_DIR / "idle-scarf-00.round-07.png").convert("RGBA")
    body_h = np.array(body_im).shape[0]
    scarf_h = np.array(scarf_im).shape[0]
    waist_y = WAIST_Y_FRAC * body_h

    pad_top = math.ceil(BREATH_RISE_PX) + 4
    tilt_lateral_max = NECK_Y * math.tan(math.radians(TILT_PEAK_DEG))
    x_disp_bound = abs(SHIFT_X_PX) + abs(tilt_lateral_max)
    arm_depth_max = ARM_MASK_Y1 - ARM_PIVOT_Y
    arm_shift_max = arm_depth_max * math.tan(math.radians(ARM_SWAY_PEAK_DEG))
    pad_side = math.ceil(max(x_disp_bound, arm_shift_max)) + 4

    print(f"body_h={body_h} waist_y={waist_y:.2f} pad_top={pad_top} pad_side={pad_side}")
    print(f"tilt_lateral_max={tilt_lateral_max:.2f} arm_shift_max={arm_shift_max:.2f}")

    scarf_arr0 = np.array(scarf_im)
    pivot_x = centroid_x_band(scarf_arr0, 0, PIVOT_ROW_BAND)
    shift_max_scarf = (scarf_h - 1 - PIVOT_Y) * math.tan(math.radians(SCARF_SWAY_DEG))
    pad_h_scarf = math.ceil(shift_max_scarf) + 4

    stable_y0_padded = STABLE_Y0 + pad_top

    records = {}
    for i in range(NFRAMES):
        t = i * DURATION / NFRAMES

        rise_px = BREATH_RISE_PX * breath_fraction(t)
        settle_px = SETTLE_Y_PX * weight_ease(t, WEIGHT_PHASE_LAG)
        shift_x_px = SHIFT_X_PX * x_ease(t, WEIGHT_PHASE_LAG)
        tilt_deg = TILT_PEAK_DEG * x_ease(t, WEIGHT_PHASE_LAG)
        tilt_px_at_top = NECK_Y * math.tan(math.radians(tilt_deg))

        combined_rise = rise_px - settle_px
        pass1 = body_pass1(body_im, waist_y, pad_top, pad_side, combined_rise, shift_x_px, tilt_px_at_top)

        arm_angle = ARM_SWAY_PEAK_DEG * x_ease(t, ARM_LAG)
        pass2 = arm_sway_pass(pass1, ARM_PIVOT_Y + pad_top, arm_angle)

        body_out = Image.fromarray(pass2, "RGBA")
        body_out.save(OUT_DIR / f"idle-body-{i:02d}.png")

        angle = SCARF_SWAY_DEG * sway_fraction(t)
        scarf_out = shear_scarf(scarf_im, pivot_x, PIVOT_Y, pad_h_scarf, angle)
        scarf_out.save(OUT_DIR / f"idle-scarf-{i:02d}.png")

        sole_y, torso_x, head_x = measure_anchors(pass2, stable_y0_padded)
        scarf_offset = [
            BASE_SCARF_OFFSET[0] - pad_h_scarf + pad_side + shift_x_px,
            BASE_SCARF_OFFSET[1] - combined_rise,
        ]
        records[str(i)] = {
            "sole_y": sole_y, "torso_x": torso_x, "head_x": head_x, "place_dy_offset": 0.0,
            "scarf_offset_final": scarf_offset,
        }
        print(i, f"t={t:.3f} rise={rise_px:.2f} settle={settle_px:.2f} shift_x={shift_x_px:.2f} "
              f"tilt_deg={tilt_deg:.2f} arm_deg={arm_angle:.2f} sole_y={sole_y:.3f} torso_x={torso_x:.3f}")

    with open(OUT_DIR / "idle-finalize-record.json", "w") as f:
        json.dump(records, f, indent=2)
    print("done")


if __name__ == "__main__":
    main()
