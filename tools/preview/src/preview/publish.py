"""Publish a built gallery to the gh-pages branch under review/pr-<n>/, and the PR-description snippet.

Publishing never touches the caller's checkout or jj store. It works in a private bare clone under
$PREVIEW_CACHE_DIR (default ~/.cache/preview): it builds the new gh-pages tree in a temporary index from blobs
hashed with --no-filters (so files are plain blobs whatever .gitattributes says, which Pages and
raw.githubusercontent.com need), commits it on top of the fetched gh-pages, and pushes without force. If gh-pages
moved in the meantime, the push is rejected and the whole step is redone on the new tip.
"""

import fcntl
import hashlib
import json
import os
import re
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

from preview.media import PreviewError

PAGES_FIX = "set Settings > Pages > Build and deployment to 'Deploy from a branch', branch gh-pages, folder / (root)"
BRANCH = "gh-pages"
ATTEMPTS = 5


def pages_problem(pages: dict | None) -> str | None:
    """Why GitHub Pages would not serve review/ from the gh-pages branch, or None when it will."""
    if pages is None:
        return f"GitHub Pages is not enabled for this repository; {PAGES_FIX}"
    if pages.get("build_type") != "legacy":
        return f"GitHub Pages builds with {pages.get('build_type')!r}, not from a branch; {PAGES_FIX}"
    source = pages.get("source") or {}
    if source.get("branch") != BRANCH or source.get("path") != "/":
        return f"GitHub Pages serves {source.get('branch')}:{source.get('path')}, not {BRANCH}:/; {PAGES_FIX}"
    return None


def gallery_url(repo: str, pr: str) -> str:
    owner, name = repo.split("/")
    return f"https://{owner.lower()}.github.io/{name}/review/pr-{pr}/"


def snippet(manifest: dict, repo: str, commit: str) -> str:
    """Markdown for the PR description: the gallery link and inline PNG/GIF thumbnails pinned to the gh-pages
    commit that holds them, so they keep showing exactly what was reviewed after a republish or cleanup."""
    pr = manifest["pr"]
    raw = f"https://raw.githubusercontent.com/{repo}/{commit}/review/pr-{pr}/"
    lines = [f"**Review gallery:** {gallery_url(repo, pr)}", ""]
    if manifest["contact_sheet"]:
        lines.append(f"![contact sheet]({raw}{manifest['contact_sheet']})")
    for item in manifest["items"]:
        alt = re.sub(r"[\[\]()<>]", "", item["name"])
        for key in ("gif", "waveform"):
            if key in item["media"]:
                lines.append(f"![{alt}]({raw}{item['media'][key]})")
    return "\n".join(lines) + "\n"


def _git(repo: Path | None, *args: str, stdin: str | None = None, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    command = ["git", *(["-C", str(repo)] if repo else []), *args]
    result = subprocess.run(command, input=stdin, capture_output=True, text=True, env={**os.environ, **(env or {})})
    if check and result.returncode != 0:
        raise PreviewError(f"`git {args[0]}` failed: {result.stderr.strip() or result.stdout.strip()}")
    return result


def cache_dir() -> Path:
    return Path(os.environ.get("PREVIEW_CACHE_DIR") or Path.home() / ".cache" / "preview")


@contextmanager
def _locked(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def _clone(remote: str) -> Path:
    repo = cache_dir() / (hashlib.sha256(remote.encode()).hexdigest()[:16] + ".git")
    if not repo.exists():
        _git(None, "init", "-q", "--bare", str(repo))
        _git(repo, "remote", "add", "origin", remote)
        # A blobless partial clone: building the new tree needs only trees, plus the blobs this build creates.
        _git(repo, "config", "remote.origin.promisor", "true")
        _git(repo, "config", "remote.origin.partialclonefilter", "blob:none")
    return repo


def _fetch(repo: Path) -> str:
    _git(repo, "fetch", "-q", "--no-tags", "--filter=blob:none", "origin", f"+refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}")
    return _git(repo, "rev-parse", f"refs/remotes/origin/{BRANCH}").stdout.strip()


def _push(repo: Path, remote: str, commit: str) -> bool:
    """Push without force; False when gh-pages moved since the fetch (retry), an error for anything else."""
    result = _git(repo, "push", "-q", "origin", f"{commit}:refs/heads/{BRANCH}", check=False)
    if result.returncode == 0:
        return True
    if "non-fast-forward" in result.stderr or "fetch first" in result.stderr or "stale info" in result.stderr:
        return False
    raise PreviewError(f"pushing gh-pages to {remote} failed: {result.stderr.strip()}")


def _files(build: Path | None) -> dict[str, Path]:
    return {p.relative_to(build).as_posix(): p for p in sorted(build.rglob("*")) if p.is_file()} if build else {}


def _commit(repo: Path, base: str, pr: str, files: dict[str, Path], identity: tuple[str, str]) -> str | None:
    """A commit on base whose review/pr-<pr>/ holds exactly files; None when base already does."""
    prefix = f"review/pr-{pr}/"
    with tempfile.TemporaryDirectory() as scratch:
        # update-index wants a work tree even for index-only changes; an empty one is never read or written.
        (Path(scratch) / "tree").mkdir()
        env = {"GIT_INDEX_FILE": str(Path(scratch) / "index"), "GIT_WORK_TREE": str(Path(scratch) / "tree")}
        _git(repo, "read-tree", base, env=env)
        stale = _git(repo, "ls-tree", "-r", "-z", "--name-only", base, "--", prefix).stdout
        if stale:
            _git(repo, "update-index", "-z", "--force-remove", "--stdin", stdin=stale, env=env)
        if files:
            blobs = _git(repo, "hash-object", "-w", "--no-filters", "--stdin-paths", stdin="\n".join(str(p) for p in files.values()) + "\n").stdout.split()
            index_info = "".join(f"100644 {blob}\t{prefix}{path}\n" for path, blob in zip(files, blobs, strict=True))
            _git(repo, "update-index", "--add", "--index-info", stdin=index_info, env=env)
        tree = _git(repo, "write-tree", env=env).stdout.strip()
    if tree == _git(repo, "rev-parse", f"{base}^{{tree}}").stdout.strip():
        return None
    changed = _git(repo, "diff-tree", "-r", "--name-only", "--no-renames", base, tree).stdout.split("\n")
    stray = [path for path in changed if path and not path.startswith(prefix)]
    if stray:
        raise PreviewError(f"refusing to publish: the gh-pages change would touch {', '.join(stray)}")
    published = {line.split("\t")[1].removeprefix(prefix): int(line.split()[3])
                 for line in _git(repo, "ls-tree", "-r", "-l", tree, "--", prefix).stdout.splitlines()}
    expected = {path: file.stat().st_size for path, file in files.items()}
    if published != expected:
        raise PreviewError(f"refusing to publish: the new tree's {prefix} does not match the build")
    name, email = identity
    people = {"GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email}
    message = f"review: {'publish' if files else 'remove'} the pr-{pr} gallery"
    return _git(repo, "commit-tree", tree, "-p", base, "-m", message, env=people).stdout.strip()


def update_gh_pages(pr: str, build: Path | None, *, remote: str, identity: tuple[str, str]) -> str | None:
    """Make review/pr-<pr>/ on the remote's gh-pages equal the build (or remove it when build is None) and push;
    return the pushed commit, or None when gh-pages already matched."""
    files = _files(build)
    with _locked(cache_dir() / "publish.lock"):
        repo = _clone(remote)
        for _ in range(ATTEMPTS):
            base = _fetch(repo)
            commit = _commit(repo, base, pr, files, identity)
            if commit is None:
                return None
            if _push(repo, remote, commit):
                return commit
    raise PreviewError(f"gh-pages on {remote} kept moving; gave up after {ATTEMPTS} attempts")


def current_commit(remote: str) -> str:
    """The gh-pages commit on the remote right now."""
    with _locked(cache_dir() / "publish.lock"):
        return _fetch(_clone(remote))


def repository() -> str:
    result = subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"], capture_output=True, text=True)
    if result.returncode != 0:
        raise PreviewError(f"`gh repo view` failed: {result.stderr.strip()}")
    return result.stdout.strip()


def require_pages(repo: str) -> None:
    result = subprocess.run(["gh", "api", f"repos/{repo}/pages"], capture_output=True, text=True)
    if result.returncode != 0 and "Not Found" not in result.stderr + result.stdout:
        raise PreviewError(f"could not read the GitHub Pages settings for {repo}: {result.stderr.strip()}")
    problem = pages_problem(json.loads(result.stdout) if result.returncode == 0 else None)
    if problem:
        raise PreviewError(problem)
