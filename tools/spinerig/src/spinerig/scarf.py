"""Delayed, damped follow-through rotate keyframes for a chain of scarf bones.

Reimplements the technique `spine-animation-ai` (PolyForm Noncommercial) uses, from
scratch: for bone *i* of the chain (0-indexed from the root end of the scarf),

    angle_i(t) = -gain_i * trail_deg + gain_i * flutter_deg * sin(2*pi*flutter_hz*(t - i*lag_frames/FPS))

`trail_deg` sets how far the segment trails the torso for this animation; `flutter_deg`
and `flutter_hz` add a sinusoidal wobble; `lag_frames` delays each successive bone's
wobble by that many frames, so amplitude (set by `gain`) decreases and phase lag
increases along the chain. Keyframes are sampled every `FRAME_STEP` frames at `FPS`
frames per second, always including t=0 and t=duration; for a looping animation the
final keyframe's rotation is forced to match the first so the loop doesn't pop. Emits
Spine 4.x's own `value` field for a rotate keyframe (not the 3.8-era `angle`; see
`generate.py`'s module docstring), since this timeline is entirely generated, not
translated from an authored one.
"""

from __future__ import annotations

import math

FPS = 30.0
FRAME_STEP = 2


def _sample_times(duration: float) -> list[float]:
    step_s = FRAME_STEP / FPS
    times = []
    t = 0.0
    while t < duration - 1e-9:
        times.append(t)
        t += step_s
    times.append(duration)
    return times


def _angle(
    t: float,
    *,
    gain: float,
    trail_deg: float,
    flutter_deg: float,
    flutter_hz: float,
    lag_frames: float,
    chain_index: int,
) -> float:
    lag_s = chain_index * lag_frames / FPS
    return -gain * trail_deg + gain * flutter_deg * math.sin(2 * math.pi * flutter_hz * (t - lag_s))


def rotate_keys(
    *,
    duration: float,
    loop: bool,
    gain: float,
    trail_deg: float,
    flutter_deg: float,
    flutter_hz: float,
    lag_frames: float,
    chain_index: int,
) -> list[dict]:
    """Spine `rotate` timeline keyframes (`{"time": t, "value": deg}`, ascending time) for one scarf bone."""
    times = _sample_times(duration)
    keys = [
        {
            "time": round(t, 6),
            "value": _angle(
                t,
                gain=gain,
                trail_deg=trail_deg,
                flutter_deg=flutter_deg,
                flutter_hz=flutter_hz,
                lag_frames=lag_frames,
                chain_index=chain_index,
            ),
        }
        for t in times
    ]
    if loop and len(keys) > 1:
        keys[-1]["value"] = keys[0]["value"]
    return keys
