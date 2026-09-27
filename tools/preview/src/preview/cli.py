"""Review previews for Violet's assets: build a gallery for a PR, publish it to GitHub Pages, and print
the Markdown for the PR description. Output goes to out/review/pr-<n>/ at the repository root."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from provenance.config import Config, ProvenanceError, find_config, load_config
from provenance.records import check_asset, content_sha256, lfs_pointer_oid, load_record, sidecar_for

from preview import media
from preview.gallery import page
from preview.media import PreviewError
from preview.publish import current_commit, gallery_url, repository, require_pages, snippet, update_gh_pages

IMAGES = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".psd"}
VIDEOS = {".mp4", ".webm", ".mov", ".gif"}
AUDIO = {".wav", ".ogg", ".mp3", ".flac", ".m4a"}
MODELS = {".glb", ".gltf", ".fbx", ".blend"}
FRAMES = {".png", ".jpg", ".jpeg", ".webp"}


def frames_in(directory: Path) -> list[Path]:
    """The frame images in a directory, ordered by the numbers in their names (walk2 before walk10)."""
    frames = [p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in FRAMES]
    return sorted(frames, key=lambda p: [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", p.name)])


def classify(path: Path) -> str:
    if path.is_dir():
        if not frames_in(path):
            raise PreviewError(f"{path}: a frame-sequence directory needs image files ({', '.join(sorted(FRAMES))})")
        return "frames"
    if not path.is_file():
        raise PreviewError(f"{path}: no such file or directory")
    if lfs_pointer_oid(path) is not None:
        raise PreviewError(f"{path} is a Git LFS pointer, not the asset itself; run `git lfs pull` first")
    extension = path.suffix.lower()
    for kind, extensions in (("image", IMAGES), ("video", VIDEOS), ("audio", AUDIO), ("model", MODELS)):
        if extension in extensions:
            return kind
    raise PreviewError(f"{path}: unsupported file type '{extension}'")


def _summary(record: dict) -> dict:
    generator = record.get("generator") or {}
    return {
        "origin": record["origin"],
        "license": record["license"],
        "authors": record.get("authors", []),
        "human_edits": [{"by": e["by"], "description": e["description"]} for e in record["human_edits"]],
        **{key: generator[key] for key in ("tool", "tool_version", "provider", "model", "model_version", "prompt") if generator.get(key)},
        "inputs": [item["path"] for item in generator.get("inputs", [])],
    }


def provenance_of(config: Config, path: Path) -> dict:
    """What the gallery shows about an asset's record: status ok, stale (a record exists but disagrees with the
    file), or missing; the problems; and a summary of the (first frame's) record. An invalid record is an error."""
    targets = frames_in(path) if path.is_dir() else [path]
    problems: list[str] = []
    record = None
    missing = 0
    for target in targets:
        sidecar = sidecar_for(target)
        if not sidecar.is_file():
            missing += 1
            continue
        loaded, schema_problems = load_record(sidecar)
        if loaded is None:
            raise PreviewError(f"{sidecar}: invalid provenance record:\n  " + "\n  ".join(schema_problems))
        record = record or loaded
        problems += check_asset(config, target)[0]
    if missing and missing < len(targets):
        problems.append(f"{missing} of {len(targets)} frames have no provenance record")
    status = "missing" if missing == len(targets) else "stale" if problems else "ok"
    return {"status": status, "problems": problems, "record": _summary(record) if record else None}


def source_sha256(path: Path) -> str:
    if path.is_file():
        return content_sha256(path)
    listing = "".join(f"{frame.name} {content_sha256(frame)}\n" for frame in frames_in(path))
    return hashlib.sha256(listing.encode()).hexdigest()


def render(path: Path, kind: str, index: int, staging: Path, args: argparse.Namespace) -> dict:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", path.name if path.is_dir() else path.stem).strip("-.") or "item"
    stem = f"items/{index:02d}-{slug}"
    if kind == "image":
        item_media = {"image": f"{stem}.webp"}
        media.scale_image(path, staging / item_media["image"])
    elif kind == "frames":
        item_media = {"gif": f"{stem}.gif", "video": f"{stem}.mp4", "poster": f"{stem}.poster.webp"}
        media.animation_from_frames(path, frames_in(path), args.frame_rate, staging / item_media["video"], staging / item_media["gif"])
        kind = "animation"
    elif kind == "video":
        item_media = {"gif": f"{stem}.gif", "video": f"{stem}.mp4", "poster": f"{stem}.poster.webp"}
        media.animation_from_video(path, staging / item_media["video"], staging / item_media["gif"])
        kind = "animation"
    elif kind == "audio":
        item_media = {"audio": f"{stem}.m4a", "waveform": f"{stem}.waveform.png"}
        media.audio(path, staging / item_media["audio"], staging / item_media["waveform"])
    else:
        item_media = {"gif": f"{stem}.gif", "video": f"{stem}.mp4", "poster": f"{stem}.poster.webp"}
        device = media.turntable(
            path, staging / item_media["video"], staging / item_media["gif"],
            seconds=6, fps=args.turntable_fps, size=args.turntable_size, samples=args.turntable_samples, device=args.render_device,
        )
        print(f"{path}: {device}", file=sys.stderr)
    return {"name": path.name, "kind": kind, "media": item_media}


def cmd_build(config: Config, args: argparse.Namespace) -> int:
    paths = [Path(os.path.abspath(p)) for p in args.paths]
    kinds = [classify(path) for path in paths]
    records = [provenance_of(config, path) for path in paths]
    out = config.root / "out" / "review"
    out.mkdir(parents=True, exist_ok=True)
    for scratch in out.glob(f".pr-{args.pr}-*"):  # left behind by a build that was killed
        shutil.rmtree(scratch)
    final = out / f"pr-{args.pr}"
    staging = Path(tempfile.mkdtemp(prefix=f".pr-{args.pr}-", dir=out))
    try:
        (staging / "items").mkdir()
        items = []
        for index, (path, kind, record) in enumerate(zip(paths, kinds, records, strict=True), 1):
            item = render(path, kind, index, staging, args)
            items.append({**item, "sha256": source_sha256(path), "provenance": record})
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
        previous = Path(tempfile.mkdtemp(prefix=f".pr-{args.pr}-previous-", dir=out))
        final.rename(previous / "gallery")
        staging.rename(final)
        shutil.rmtree(previous)
    else:
        staging.rename(final)
    print(f"built {config.display(final / 'index.html')} ({len(items)} item(s))")
    return 0


def _git_setting(config: Config, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(config.root), *args], capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        raise PreviewError(f"`git {' '.join(args)}` gave nothing in {config.root}; publishing needs it")
    return result.stdout.strip()


def _publish_target(config: Config) -> tuple[str, tuple[str, str]]:
    remote = _git_setting(config, "remote", "get-url", "origin")
    identity = (_git_setting(config, "config", "user.name"), _git_setting(config, "config", "user.email"))
    return remote, identity


def load_manifest(build: Path, pr: str) -> dict:
    manifest = build / "preview.json"
    if not manifest.is_file():
        raise PreviewError(f"{build} has no complete build; run `preview build {pr} PATH...` first")
    return json.loads(manifest.read_text(encoding="utf-8"))


def cmd_publish(config: Config, args: argparse.Namespace) -> int:
    build = config.root / "out" / "review" / f"pr-{args.pr}"
    manifest = load_manifest(build, args.pr)
    repo = repository()
    require_pages(repo)
    remote, identity = _publish_target(config)
    commit = update_gh_pages(args.pr, build, remote=remote, identity=identity)
    status = f"pushed gh-pages {commit[:12]}" if commit else "gh-pages already has this gallery"
    print(f"{status}; the gallery goes live at {gallery_url(repo, args.pr)} once Pages rebuilds", file=sys.stderr)
    print(snippet(manifest, repo, commit or current_commit(remote)), end="")
    return 0


def cmd_unpublish(config: Config, args: argparse.Namespace) -> int:
    remote, identity = _publish_target(config)
    commit = update_gh_pages(args.pr, None, remote=remote, identity=identity)
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
                       help="Cycles device; auto probes for OptiX, then CUDA, and uses the CPU when neither works (default auto)")
    build.set_defaults(handler=cmd_build)

    publish = commands.add_parser("publish", help="put out/review/pr-<n>/ on gh-pages under review/pr-<n>/, push, print the PR snippet")
    publish.add_argument("pr", type=_pr, metavar="PR_NUMBER")
    publish.set_defaults(handler=cmd_publish)

    unpublish = commands.add_parser("unpublish", help="remove review/pr-<n>/ from gh-pages and push")
    unpublish.add_argument("pr", type=_pr, metavar="PR_NUMBER")
    unpublish.set_defaults(handler=cmd_unpublish)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(find_config(Path.cwd()))
        return args.handler(config, args)
    except (PreviewError, ProvenanceError) as error:
        print(f"preview: error: {error}", file=sys.stderr)
        return 2
