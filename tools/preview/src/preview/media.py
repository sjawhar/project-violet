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


class PreviewError(Exception):
    """A failure whose message is shown to the user as-is."""


def run(asset: Path, *args: str) -> str:
    """Run a tool for an asset; a missing tool or a non-zero exit is an error naming the asset."""
    if shutil.which(args[0]) is None:
        raise PreviewError(f"{asset}: `{args[0]}` is not on PATH; run `mise install` in the repository")
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        detail = "\n  ".join((result.stderr or result.stdout).strip().splitlines()[-8:])
        raise PreviewError(f"{asset}: {args[0]} failed:\n  {detail}")
    return result.stdout


def scale_image(asset: Path, dst: Path) -> None:
    """A PNG of the image (first frame or layer), no larger than IMAGE_MAX_PX on its long side."""
    run(asset, "magick", f"{asset}[0]", "-auto-orient", "-resize", f"{IMAGE_MAX_PX}x{IMAGE_MAX_PX}>", "-depth", "8", str(dst))


def contact_sheet(images: list[tuple[str, Path]], dst: Path) -> None:
    """A labelled grid of the (already scaled) images."""
    args = ["magick", "montage"]
    for label, path in images:
        args += ["-label", label, str(path)]
    args += ["-tile", "4x", "-geometry", "320x320+8+8", "-background", "#1b1b22", "-fill", "#e5e5ea", "-depth", "8", str(dst)]
    run(dst, *args)


def _gif_filter(fps: int | None) -> str:
    rate = f"fps={fps}," if fps else ""
    return f"{rate}scale='min({GIF_MAX_PX},iw)':-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse"


def _encode_frames(asset: Path, pattern: Path, fps: int, video: Path, gif: Path, *, gif_fps: int | None) -> None:
    """An MP4 of the numbered frames, and a GIF at gif_fps (None keeps every frame)."""
    source = ["-framerate", str(fps), "-start_number", "1", "-i", str(pattern)]
    run(asset, "ffmpeg", "-v", "error", "-y", *source, "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video))
    run(asset, "ffmpeg", "-v", "error", "-y", *source, "-filter_complex", _gif_filter(gif_fps), str(gif))


def animation_from_frames(asset: Path, frames: list[Path], fps: int, video: Path, gif: Path) -> None:
    """An MP4 and a GIF from a sequence of image files, in the order given."""
    extensions = {frame.suffix.lower() for frame in frames}
    if len(extensions) != 1:
        raise PreviewError(f"{asset}: frames must share one file type, found {', '.join(sorted(extensions))}")
    [extension] = extensions
    with tempfile.TemporaryDirectory() as scratch:
        for number, frame in enumerate(frames, 1):
            (Path(scratch) / f"{number:06d}{extension}").symlink_to(frame.resolve())
        # Every frame of an animation matters in review, so its GIF keeps them all.
        _encode_frames(asset, Path(scratch) / f"%06d{extension}", fps, video, gif, gif_fps=None)


def animation_from_video(asset: Path, video: Path, gif: Path) -> None:
    """The video as an MP4 (copied when it already is one) and a GIF."""
    run(asset, "ffmpeg", "-v", "error", "-y", "-i", str(asset), "-filter_complex", _gif_filter(GIF_FPS), str(gif))
    if asset.suffix.lower() == ".mp4":
        shutil.copyfile(asset, video)
    else:
        run(asset, "ffmpeg", "-v", "error", "-y", "-i", str(asset), "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", "-an", str(video))


def audio(asset: Path, copy: Path, waveform: Path) -> None:
    """The audio file as-is for an HTML5 player, and a waveform PNG."""
    run(asset, "ffmpeg", "-v", "error", "-y", "-i", str(asset), "-filter_complex",
        "aformat=channel_layouts=mono,showwavespic=s=1200x200:colors=#a78bfa", "-frames:v", "1", str(waveform))
    shutil.copyfile(asset, copy)


def turntable(asset: Path, video: Path, gif: Path, *, seconds: float, fps: int, size: int, samples: int, device: str) -> str:
    """A turntable MP4 and GIF of a 3D model rendered headless with Blender; returns the render device used."""
    with tempfile.TemporaryDirectory() as scratch, as_file(files("preview").joinpath("turntable.py")) as script:
        output = run(asset, "blender", "-b", "--factory-startup", "--python-exit-code", "1", "--python", str(script), "--",
                     str(asset), scratch, str(seconds), str(fps), str(size), str(samples), device)
        rendered = sorted(Path(scratch).glob("*.png"))
        if len(rendered) != round(seconds * fps):
            raise PreviewError(f"{asset}: Blender wrote {len(rendered)} frames, expected {round(seconds * fps)}")
        _encode_frames(asset, Path(scratch) / "%06d.png", fps, video, gif, gif_fps=min(fps, GIF_FPS))
    device_lines = [line for line in output.splitlines() if line.startswith("preview: ")]
    return device_lines[-1].removeprefix("preview: ") if device_lines else "unknown device"
