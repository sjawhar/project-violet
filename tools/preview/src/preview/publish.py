"""Publish a built gallery to the gh-pages branch under review/pr-<n>/, and the PR-description snippet."""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from preview.media import PreviewError

PAGES_FIX = "set Settings > Pages > Build and deployment to 'Deploy from a branch', branch gh-pages, folder / (root)"


def pages_problem(pages: dict | None) -> str | None:
    """Why GitHub Pages would not serve review/ from the gh-pages branch, or None when it will."""
    if pages is None:
        return f"GitHub Pages is not enabled for this repository; {PAGES_FIX}"
    if pages.get("build_type") != "legacy":
        return f"GitHub Pages builds with {pages.get('build_type')!r}, not from a branch; {PAGES_FIX}"
    source = pages.get("source") or {}
    if source.get("branch") != "gh-pages" or source.get("path") != "/":
        return f"GitHub Pages serves {source.get('branch')}:{source.get('path')}, not gh-pages:/; {PAGES_FIX}"
    return None


def gallery_url(repo: str, pr: str) -> str:
    owner, name = repo.split("/")
    return f"https://{owner.lower()}.github.io/{name}/review/pr-{pr}/"


def snippet(manifest: dict, repo: str) -> str:
    """Markdown for the PR description: the gallery link and inline PNG/GIF thumbnails."""
    pr = manifest["pr"]
    raw = f"https://raw.githubusercontent.com/{repo}/gh-pages/review/pr-{pr}/"
    lines = [f"**Review gallery:** {gallery_url(repo, pr)}", ""]
    if manifest["contact_sheet"]:
        lines.append(f"![contact sheet]({raw}{manifest['contact_sheet']})")
    for item in manifest["items"]:
        for key in ("gif", "waveform"):
            if key in item["media"]:
                lines.append(f"![{item['name']}]({raw}{item['media'][key]})")
    return "\n".join(lines) + "\n"


def _command(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        detail = "\n  ".join((result.stderr or result.stdout).strip().splitlines()[-8:])
        raise PreviewError(f"`{' '.join(args[:3])} ...` failed:\n  {detail}")
    return result.stdout


def repository() -> str:
    return _command("gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner").strip()


def require_pages(repo: str) -> None:
    result = subprocess.run(["gh", "api", f"repos/{repo}/pages"], capture_output=True, text=True)
    if result.returncode != 0 and "Not Found" not in result.stderr + result.stdout:
        raise PreviewError(f"could not read the GitHub Pages settings for {repo}: {result.stderr.strip()}")
    problem = pages_problem(json.loads(result.stdout) if result.returncode == 0 else None)
    if problem:
        raise PreviewError(problem)


def load_manifest(build: Path, pr: str) -> dict:
    manifest = build / "preview.json"
    if not manifest.is_file():
        raise PreviewError(f"{build} has no complete build; run `preview build {pr} PATH...` first")
    return json.loads(manifest.read_text())


def update_gh_pages(pr: str, build: Path | None) -> str | None:
    """Replace (build given) or delete (build None) review/pr-<pr>/ on gh-pages and push; return the new commit, or
    None when gh-pages already matched. Uses a temporary jj workspace so the caller's checkout is untouched."""
    root = Path(_command("jj", "root").strip())
    _command("jj", "git", "fetch", "--remote", "origin", "--branch", "gh-pages", cwd=root)
    _command("jj", "bookmark", "track", "gh-pages@origin", cwd=root)
    name = f"preview-publish-{os.getpid()}"
    scratch = Path(tempfile.mkdtemp(prefix="preview-publish-"))
    checkout = scratch / "gh-pages"
    _command("jj", "workspace", "add", "--name", name, "-r", "gh-pages@origin", str(checkout), cwd=root)
    try:
        target = checkout / "review" / f"pr-{pr}"
        if target.exists():
            shutil.rmtree(target)
        expected: set[str] = set()
        largest = 0
        if build is not None:
            shutil.copytree(build, target)
            files = [path for path in target.rglob("*") if path.is_file()]
            expected = {path.relative_to(checkout).as_posix() for path in files}
            largest = max((path.stat().st_size for path in files), default=0)
        # jj leaves new files above snapshot.max-new-file-size (1 MiB by default) out of the commit with only a warning.
        jj = ["jj", "--config", f"snapshot.max-new-file-size={max(largest + 1, 1 << 20)}"]
        changed = _command(*jj, "diff", "--name-only", cwd=checkout).splitlines()
        if not changed:
            return None
        stray = [path for path in changed if not path.startswith(f"review/pr-{pr}/")]
        if stray:
            raise PreviewError(f"refusing to publish: the gh-pages change would touch {', '.join(stray)}")
        committed = set(_command(*jj, "file", "list", "-r", "@", f"review/pr-{pr}", cwd=checkout).splitlines())
        if committed != expected:
            raise PreviewError(f"refusing to publish: the commit's review/pr-{pr}/ files differ from the build: {sorted(committed ^ expected)}")
        action = "publish" if build is not None else "remove"
        _command(*jj, "describe", "-m", f"review: {action} the pr-{pr} gallery", cwd=checkout)
        commit = _command(*jj, "log", "-r", "@", "--no-graph", "-T", "commit_id", cwd=checkout).strip()
        _command(*jj, "bookmark", "set", "gh-pages", "-r", "@", cwd=checkout)
        _command(*jj, "git", "push", "--remote", "origin", "--bookmark", "gh-pages", cwd=checkout)
        pushed = _command(*jj, "log", "-r", "gh-pages@origin", "--no-graph", "-T", "commit_id", cwd=checkout).strip()
        if pushed != commit:
            raise PreviewError(f"pushed gh-pages is at {pushed}, expected {commit}")
        return commit
    finally:
        _command("jj", "workspace", "forget", name, cwd=root)
        shutil.rmtree(scratch)
