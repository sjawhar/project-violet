#!/usr/bin/env bash
# THROWAWAY (bake-off lane G-A, plan Task 7 Step 18): the manual edits on freshly generated art, each recorded with
# `provenance edit`. Run once, from the repository root, right after bakeoff/g-a/gen-art.sh (re-running it edits again).
#   bash bakeoff/g-a/edit-art.sh PIECE...   # default: every piece below
set -euo pipefail
art=game/g-a/art
edit() { uv run --no-project --quiet --with pillow --with numpy python bakeoff/g-a/art_edit.py "$@"; }
record() { uv run --project tools/provenance --quiet provenance edit "$art/$1.png" --by "claude (lane G-A agent)" --description "$2"; }
pieces=("$@"); [ ${#pieces[@]} -gt 0 ] || pieces=(orb goal-gate backdrop-far backdrop-mid backdrop-near)
for p in "${pieces[@]}"; do
  case "$p" in
    orb|goal-gate)
      edit key "$art/$p.png"
      record "$p" "bakeoff/g-a/art_edit.py key: flat magenta background keyed to transparency (gen has no transparent-background option)" ;;
    backdrop-far)
      edit seam "$art/$p.png"
      record "$p" "bakeoff/g-a/art_edit.py seam: cropped to the best-matching edge columns and crossfaded 48 px so it repeats side by side" ;;
    backdrop-mid|backdrop-near)
      edit key "$art/$p.png"
      edit seam "$art/$p.png"
      record "$p" "bakeoff/g-a/art_edit.py key then seam: magenta sky keyed to transparency, then cropped to the best-matching edge columns and crossfaded 48 px so it repeats side by side" ;;
    *) echo "edit-art.sh: no edit for $p" >&2; exit 1 ;;
  esac
done
