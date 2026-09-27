#!/usr/bin/env bash
# THROWAWAY (lane G-A): regenerates the rig tests' fixture from placeholder.violet-rig.json, with flat part images drawn
# at run time (never committed): placeholder.rig.json and placeholder.rig.meta.json (spinerig generate's output) and
# placeholder.reference.json (every slot's placement per frame from spinerig render's own code).
# SPINERIG=<spinerig project, default tools/spinerig; needs render.py> bash game/g-c/tests/rig/make-fixture.sh [PARTS_DIR]
# PARTS_DIR also gets the part images, to look at the rig in a throwaway copy of the project.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; parts_out="${1:+$(realpath -m "$1")}"
cd "$here/../../../.."
spinerig="$(realpath "${SPINERIG:-tools/spinerig}")"
work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT
cp "$here/placeholder.violet-rig.json" "$work/rig.json"
uv run --project "$spinerig" python "$here/placeholder_parts.py" "$work/parts"
uv run --project "$spinerig" spinerig generate "$work/rig.json" --out "$work/placeholder.rig.json"
uv run --project "$spinerig" python "$here/reference_poses.py" "$work/placeholder.rig.json" "$work/placeholder.reference.json"
cp "$work/placeholder.rig.json" "$work/placeholder.rig.meta.json" "$work/placeholder.reference.json" "$here/"
if [ -n "$parts_out" ]; then mkdir -p "$parts_out"; cp "$work"/parts/*.png "$parts_out/"; fi
