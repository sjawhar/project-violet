#!/usr/bin/env bash
# THROWAWAY (mechanics lab). Publishes SRC_DIR (the output of build_site.py) to review/pr-0-prelim/mechanics-lab/ on the
# gh-pages branch without disturbing anything else there (glow-up/, bakeoff.html, items/, ...).
#
# This reuses tools/preview/src/preview/publish.py's own primitives unmodified: the same
# read-tree/update-index/write-tree scoped-prefix commit, the "no stray path touched" check, the
# no-force push with fetch-and-retry on a race, and the shared blobless bare clone under
# $PREVIEW_CACHE_DIR (default ~/.cache/preview) that `preview publish <PR>` already uses. The only
# difference from that tool is the prefix: `update_gh_pages()` builds it as `review/pr-{pr}/`, and
# passing "0-prelim/mechanics-lab" as `pr` naturally yields `review/pr-0-prelim/mechanics-lab/`
# without any changes to tools/preview (which is shared infra owned elsewhere).
#
# --dry-run stops before the push: it still clones/fetches the real gh-pages tip and builds the
# candidate commit locally (so the stray-path safety check actually runs against current reality),
# but never calls `git push`, so gh-pages on GitHub is never touched. Local git objects end up in
# the shared cache's bare clone either way; that clone has no ref pointing at them until a real
# push, so they are inert and get garbage-collected eventually like any unreferenced git object.
#
# Usage: publish.sh SRC_DIR [--dry-run]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PR="0-prelim/mechanics-lab" # -> gh-pages review/pr-0-prelim/mechanics-lab/

dry_run=0
src=""
for arg in "$@"; do
  case "$arg" in
  --dry-run) dry_run=1 ;;
  -*)
    echo "publish.sh: unknown flag $arg" >&2
    exit 1
    ;;
  *) src="$arg" ;;
  esac
done
[ -n "$src" ] || { echo "usage: publish.sh SRC_DIR [--dry-run]" >&2; exit 1; }
[ -d "$src" ] || { echo "publish.sh: $src is not a directory" >&2; exit 1; }
src="$(cd "$src" && pwd)"

PYTHONPATH="$REPO_ROOT/tools/preview/src" SRC_DIR="$src" REPO_ROOT="$REPO_ROOT" PR="$PR" DRY_RUN="$dry_run" \
  python3 - <<'PY'
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.environ["PYTHONPATH"])
from preview.publish import (  # noqa: E402  (sys.path must be set first)
    _clone, _commit, _fetch, _files, cache_dir, _locked,
    gallery_url, repository, require_pages, update_gh_pages,
)

repo_root = Path(os.environ["REPO_ROOT"])
build = Path(os.environ["SRC_DIR"])
pr = os.environ["PR"]
dry_run = os.environ["DRY_RUN"] == "1"
prefix = f"review/pr-{pr}/"


def git_setting(*args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo_root), *args], capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        sys.exit(f"publish.sh: `git {' '.join(args)}` failed: {result.stderr.strip()}")
    return result.stdout.strip()


remote = git_setting("remote", "get-url", "origin")
identity = (git_setting("config", "user.name"), git_setting("config", "user.email"))
repo_name = repository()
require_pages(repo_name)  # raises PreviewError if Pages would not serve review/ from gh-pages

if not dry_run:
    commit = update_gh_pages(pr, build, remote=remote, identity=identity)
    if commit is None:
        print(f"gh-pages {prefix} already matches {build}; nothing pushed")
    else:
        print(f"pushed gh-pages {commit[:12]}; live at {gallery_url(repo_name, pr)} once Pages rebuilds")
    sys.exit(0)

# Dry run: same clone/fetch/commit-tree computation `update_gh_pages` does, but stop before `_push`.
files_map = _files(build)
with _locked(cache_dir() / "publish.lock"):
    repo = _clone(remote)
    base = _fetch(repo)
    commit = _commit(repo, base, pr, files_map, identity)

if commit is None:
    print(f"[dry-run] gh-pages {prefix} already matches {build}; nothing would change")
    sys.exit(0)

diff = subprocess.run(
    ["git", "-C", str(repo), "diff-tree", "-r", "--name-status", "--no-renames", base, commit],
    capture_output=True, text=True, check=True,
).stdout
print(f"[dry-run] would write {len(files_map)} file(s) from {build} to {prefix} on gh-pages:")
verbs = {"A": "ADD", "M": "MODIFY", "D": "REMOVE"}
for line in diff.splitlines():
    status, path = line.split("\t", 1)
    print(f"  {verbs.get(status[0], status):6} {path}")
print(f"[dry-run] gh-pages NOT pushed (candidate commit {commit[:12]} built locally only).")
print(f"[dry-run] would go live at {gallery_url(repo_name, pr)} once Pages rebuilds, once run for real.")
PY
