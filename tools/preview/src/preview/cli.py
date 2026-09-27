"""Review previews for Violet's assets: build a gallery for a PR, publish it to GitHub Pages, and print
the Markdown for the PR description. Run from the repository root; output goes to out/review/pr-<n>/."""

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

from preview import media
from preview.gallery import page
from preview.media import PreviewError
from preview.publish import gallery_url, load_manifest, repository, require_pages, snippet, update_gh_pages

OUT = Path("out/review")
IMAGES = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".psd"}
VIDEOS = {".mp4", ".webm", ".mov", ".gif"}
AUDIO = {".wav", ".ogg", ".mp3", ".flac"}
MODELS = {".glb", ".gltf", ".fbx", ".blend"}
FRAMES = {".png", ".jpg", ".jpeg", ".webp"}


def classify(path: Path) -> str:
    if path.is_dir():
        return "frames"
    if not path.is_file():
        raise PreviewError(f"{path}: no such file or directory")
    extension = path.suffix.lower()
    for kind, extensions in (("image", IMAGES), ("video", VIDEOS), ("audio", AUDIO), ("model", MODELS)):
        if extension in extensions:
            return kind
    raise PreviewError(f"{path}: unsupported file type '{extension}'")


def provenance(path: Path) -> dict | None:
    """The provenance summary shown beside an asset: origin plus provider, model and prompt, or authors."""
    sidecar = path.with_name(path.name + ".provenance.json")
    if path.is_dir() and not sidecar.exists():
        frames = _frames(path)
        sidecar = frames[0].with_name(frames[0].name + ".provenance.json")
    if not sidecar.exists():
        return None
    try:
        record = json.loads(sidecar.read_text(encoding="utf-8"))
        if record["origin"] == "human":
            return {"origin": "human", "authors": record["authors"]}
        generator = record["generator"]
        return {"origin": record["origin"], **{key: generator.get(key) for key in ("tool", "provider", "model", "prompt")}}
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise PreviewError(f"{sidecar}: malformed provenance record ({type(error).__name__}: {error})") from error


def _frames(directory: Path) -> list[Path]:
    frames = sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in FRAMES)
    if not frames:
        raise PreviewError(f"{directory}: a frame-sequence directory needs image files ({', '.join(sorted(FRAMES))})")
    return frames


def render(path: Path, kind: str, index: int, staging: Path, args: argparse.Namespace) -> dict:
    stem = f"items/{index:02d}-{re.sub(r'[^A-Za-z0-9._-]', '-', path.name)}"
    summary = provenance(path)
    if kind == "image":
        item_media = {"image": f"{stem}.png"}
        media.scale_image(path, staging / item_media["image"])
    elif kind == "frames":
        item_media = {"gif": f"{stem}.gif", "video": f"{stem}.mp4"}
        media.animation_from_frames(path, _frames(path), args.frame_rate, staging / item_media["video"], staging / item_media["gif"])
        kind = "animation"
    elif kind == "video":
        item_media = {"gif": f"{stem}.gif", "video": f"{stem}.mp4"}
        media.animation_from_video(path, staging / item_media["video"], staging / item_media["gif"])
        kind = "animation"
    elif kind == "audio":
        item_media = {"audio": f"{stem}{path.suffix.lower()}", "waveform": f"{stem}.waveform.png"}
        media.audio(path, staging / item_media["audio"], staging / item_media["waveform"])
    else:
        item_media = {"gif": f"{stem}.gif", "video": f"{stem}.mp4"}
        device = media.turntable(
            path, staging / item_media["video"], staging / item_media["gif"],
            seconds=6, fps=args.turntable_fps, size=args.turntable_size, samples=args.turntable_samples, device=args.render_device,
        )
        print(f"{path}: {device}", file=sys.stderr)
    return {"name": path.name, "kind": kind, "media": item_media, "provenance": summary}


def cmd_build(args: argparse.Namespace) -> int:
    paths = [Path(p) for p in args.paths]
    kinds = [classify(path) for path in paths]
    for path in paths:
        provenance(path)
    OUT.mkdir(parents=True, exist_ok=True)
    final = OUT / f"pr-{args.pr}"
    staging = Path(tempfile.mkdtemp(prefix=f".pr-{args.pr}-", dir=OUT))
    try:
        (staging / "items").mkdir()
        items = [render(path, kind, index, staging, args) for index, (path, kind) in enumerate(zip(paths, kinds), 1)]
        images = [(item["name"], staging / item["media"]["image"]) for item in items if item["kind"] == "image"]
        if images:
            media.contact_sheet(images, staging / "contact-sheet.png")
        manifest = {"pr": args.pr, "contact_sheet": "contact-sheet.png" if images else None, "items": items}
        (staging / "index.html").write_text(page(manifest), encoding="utf-8")
        (staging / "preview.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    if final.exists():
        previous = Path(tempfile.mkdtemp(prefix=f".pr-{args.pr}-previous-", dir=OUT))
        final.rename(previous / "gallery")
        staging.rename(final)
        shutil.rmtree(previous)
    else:
        staging.rename(final)
    print(f"built {final / 'index.html'} ({len(items)} item(s))")
    return 0


def cmd_publish(args: argparse.Namespace) -> int:
    build = OUT / f"pr-{args.pr}"
    manifest = load_manifest(build, args.pr)
    repo = repository()
    require_pages(repo)
    commit = update_gh_pages(args.pr, build)
    status = f"pushed gh-pages {commit[:12]}" if commit else "gh-pages already has this gallery"
    print(f"{status}; the gallery goes live at {gallery_url(repo, args.pr)} once Pages rebuilds", file=sys.stderr)
    print(snippet(manifest, repo), end="")
    return 0


def cmd_unpublish(args: argparse.Namespace) -> int:
    commit = update_gh_pages(args.pr, None)
    print(f"removed review/pr-{args.pr}/ from gh-pages ({commit[:12]})" if commit else f"gh-pages has no review/pr-{args.pr}/")
    return 0


def _pr(text: str) -> str:
    if not re.fullmatch(r"[0-9]+(-[a-z0-9]+)*", text):
        raise argparse.ArgumentTypeError(f"expected a PR number such as 12 or 0-smoke, got {text!r}")
    return text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="preview", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build", help="render a PR's assets into out/review/pr-<n>/")
    build.add_argument("pr", type=_pr, metavar="PR_NUMBER")
    build.add_argument("paths", nargs="+", metavar="PATH", help="asset files; a directory is a frame sequence")
    build.add_argument("--frame-rate", type=int, default=12, help="frame-sequence playback rate (default 12)")
    build.add_argument("--turntable-fps", type=int, default=24, help="turntable frame rate (default 24)")
    build.add_argument("--turntable-size", type=int, default=720, help="turntable width and height in pixels (default 720)")
    build.add_argument("--turntable-samples", type=int, default=32, help="Cycles samples per turntable frame (default 32)")
    build.add_argument("--render-device", choices=["auto", "optix", "cuda", "cpu"], default="auto",
                       help="Cycles device; auto tries OptiX, then CUDA, then CPU (default auto)")
    build.set_defaults(handler=cmd_build)

    publish = commands.add_parser("publish", help="copy out/review/pr-<n>/ to gh-pages under review/pr-<n>/, push, print the PR snippet")
    publish.add_argument("pr", type=_pr, metavar="PR_NUMBER")
    publish.set_defaults(handler=cmd_publish)

    unpublish = commands.add_parser("unpublish", help="remove review/pr-<n>/ from gh-pages and push")
    unpublish.add_argument("pr", type=_pr, metavar="PR_NUMBER")
    unpublish.set_defaults(handler=cmd_unpublish)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except PreviewError as error:
        print(f"preview: error: {error}", file=sys.stderr)
        return 2
