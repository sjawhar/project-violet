"""Render review media by shelling out to ImageMagick (`magick`), ffmpeg, and Blender."""

import shutil
import subprocess
import tempfile
from importlib.resources import as_file, files
from pathlib import Path

IMAGE_MAX_PX = 1600
# GIFs are the inline PR thumbnails, often viewed on a phone; the gallery plays the full MP4.
GIF_MAX_PX = 360
GIF_FPS = 10
TOOL_TIMEOUT = 600
RENDER_TIMEOUT = 3600
GPU_PROBE_TIMEOUT = 60
EVEN = "scale=trunc(iw/2)*2:trunc(ih/2)*2"
H264 = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
# PNGs carry no timestamps, so rebuilding an unchanged asset yields byte-identical files.
PNG_OUT = ["-strip", "-define", "png:exclude-chunks=date,time", "-depth", "8"]


class PreviewError(Exception):
    """A failure whose message is shown to the user as-is."""


def _excerpt(output: str) -> str:
    lines = output.strip().splitlines()
    if len(lines) > 20:
        lines = [*lines[:6], "...", *lines[-10:]]
    return "\n  ".join(lines)


def run(asset: Path, *args: str, timeout: float = TOOL_TIMEOUT) -> str:
    """Run a tool for an asset; a missing tool, a non-zero exit, or a timeout is an error naming the asset."""
    if shutil.which(args[0]) is None:
        raise PreviewError(f"{asset}: `{args[0]}` is not on PATH; run `mise install` in the repository")
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise PreviewError(f"{asset}: {args[0]} did not finish within {timeout:g}s") from None
    if result.returncode != 0:
        output = result.stderr or result.stdout
        if "No version is set for shim" in output:
            raise PreviewError(f"{asset}: mise has no version of `{args[0]}` here; run `mise install` in the repository")
        raise PreviewError(f"{asset}: {args[0]} failed:\n  {_excerpt(output)}")
    return result.stdout


def scale_image(asset: Path, dst: Path) -> None:
    """A WebP of the image (first frame or layer), no larger than IMAGE_MAX_PX on its long side."""
    run(asset, "magick", f"{asset}[0]", "-auto-orient", "-resize", f"{IMAGE_MAX_PX}x{IMAGE_MAX_PX}>", "-strip", "-quality", "90", str(dst))


def contact_sheet(images: list[tuple[str, Path]], dst: Path) -> None:
    """A labelled PNG grid of the (already scaled) images."""
    args = ["magick", "montage"]
    for label, path in images:
        # A literal label: montage would otherwise expand %-escapes in file names.
        args += ["-label", label.replace("%", "%%"), str(path)]
    args += ["-tile", f"{min(4, len(images))}x", "-geometry", "320x320+8+8", "-background", "#1b1b22", "-fill", "#e5e5ea", *PNG_OUT, str(dst)]
    run(dst, *args)


def _gif_filter(fps: int | None) -> str:
    rate = f"fps={fps}," if fps else ""
    return f"{rate}format=rgba,scale='min({GIF_MAX_PX},iw)':-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse"


def _encode(asset: Path, source: list[str], video: Path, gif: Path, *, gif_fps: int | None) -> None:
    """An MP4 (H.264, yuv420p, even size), its first frame as a small WebP poster (the page shows it before
    playback), and a GIF at gif_fps (None keeps every frame), from an ffmpeg input."""
    run(asset, "ffmpeg", "-v", "error", "-y", *source, "-vf", EVEN, "-an", *H264, str(video))
    run(asset, "ffmpeg", "-v", "error", "-y", "-i", str(video), "-frames:v", "1", "-quality", "85", str(poster_for(video)))
    run(asset, "ffmpeg", "-v", "error", "-y", *source, "-filter_complex", _gif_filter(gif_fps), str(gif))


def poster_for(video: Path) -> Path:
    return video.with_suffix(".poster.webp")


def animation_from_frames(asset: Path, frames: list[Path], fps: int, video: Path, gif: Path) -> None:
    """An MP4 and a GIF from a sequence of same-size image files, in the order given, keeping every frame."""
    extensions = {frame.suffix.lower() for frame in frames}
    if len(extensions) != 1:
        raise PreviewError(f"{asset}: frames must share one file type, found {', '.join(sorted(extensions))}")
    sizes = set(run(asset, "magick", "identify", "-format", "%wx%h\n", *(f"{frame}[0]" for frame in frames)).split())
    if len(sizes) != 1:
        raise PreviewError(f"{asset}: frames must share one size, found {', '.join(sorted(sizes))}")
    [extension] = extensions
    with tempfile.TemporaryDirectory() as scratch:
        for number, frame in enumerate(frames, 1):
            (Path(scratch) / f"{number:06d}{extension}").symlink_to(frame.resolve())
        # -reinit_filter 0: frames of different pixel formats would otherwise restart the filter graph and drop frames.
        source = ["-framerate", str(fps), "-reinit_filter", "0", "-start_number", "1", "-i", str(Path(scratch) / f"%06d{extension}")]
        _encode(asset, source, video, gif, gif_fps=None)


def animation_from_video(asset: Path, video: Path, gif: Path) -> None:
    """The video as a phone-playable MP4 and a GIF; an animated GIF input keeps every frame."""
    _encode(asset, ["-i", str(asset)], video, gif, gif_fps=None if asset.suffix.lower() == ".gif" else GIF_FPS)


def audio(asset: Path, playable: Path, waveform: Path) -> None:
    """The audio as AAC for an HTML5 player on any browser, and a waveform PNG."""
    run(asset, "ffmpeg", "-v", "error", "-y", "-i", str(asset), "-filter_complex",
        "aformat=channel_layouts=mono,showwavespic=s=1200x200:colors=#a78bfa", "-frames:v", "1", str(waveform))
    run(asset, "ffmpeg", "-v", "error", "-y", "-i", str(asset), "-vn", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(playable))


def _blender(asset: Path, script: Path, *args: str, timeout: float) -> str:
    return run(asset, "blender", "-b", "--factory-startup", "--python-exit-code", "1", "--python", str(script), "--", *args, timeout=timeout)


def turntable(asset: Path, video: Path, gif: Path, *, seconds: float, fps: int, size: int, samples: int, device: str) -> str:
    """A turntable MP4 and GIF of a 3D model rendered headless with Blender; returns the render device used.

    `auto` first asks a short-lived Blender which GPU backend works; a probe that errors or hangs means CPU,
    and the returned description says so.
    """
    frames = round(seconds * fps)
    with tempfile.TemporaryDirectory() as scratch, as_file(files("preview").joinpath("turntable.py")) as script:
        note = ""
        if device == "auto":
            try:
                device = _blender(asset, script, "--probe", timeout=GPU_PROBE_TIMEOUT).strip().splitlines()[-1].removeprefix("preview-probe: ")
            except PreviewError as error:
                device, note = "cpu", f" (GPU probe failed, so the CPU was used: {error})"
        output = _blender(asset, script, str(asset), scratch, str(seconds), str(fps), str(size), str(samples), device, timeout=RENDER_TIMEOUT)
        rendered = sorted(Path(scratch).glob("*.png"))
        if len(rendered) != frames:
            raise PreviewError(f"{asset}: Blender wrote {len(rendered)} frames, expected {frames}")
        source = ["-framerate", str(fps), "-start_number", "1", "-i", str(Path(scratch) / "%06d.png")]
        _encode(asset, source, video, gif, gif_fps=min(fps, GIF_FPS))
    used = [line.removeprefix("preview: ") for line in output.splitlines() if line.startswith("preview: ")]
    return (used[-1] if used else device) + note
