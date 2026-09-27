#!/usr/bin/env bash
# THROWAWAY (bake-off lane G-A, plan Task 7 Step 18): the manual edit on freshly generated backdrops, recorded with
# `provenance edit`. Run once, from the repository root, right after bakeoff/g-a/gen-art.sh (re-running it edits again).
#   bash bakeoff/g-a/edit-art.sh [PIECE...]   # default: the three backdrops
set -euo pipefail
art=game/g-a/art
pieces=("$@"); [ ${#pieces[@]} -gt 0 ] || pieces=(backdrop-far backdrop-mid backdrop-near)
for p in "${pieces[@]}"; do
  case "$p" in
    backdrop-far|backdrop-mid|backdrop-near) ;;
    *) echo "edit-art.sh: no edit for $p" >&2; exit 1 ;;
  esac
  uv run --no-project --quiet --with pillow --with numpy python bakeoff/g-a/art_edit.py seam "$art/$p.png"
  uv run --project tools/provenance --quiet provenance edit "$art/$p.png" --by "claude (lane G-A agent)" \
    --description "bakeoff/g-a/art_edit.py seam: cropped to the best-matching edge bands and crossfaded 48 px so it repeats side by side"
done
