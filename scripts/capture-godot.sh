#!/usr/bin/env bash
# THROWAWAY (Phase 1 bake-off). Records a lane's replay with Godot's Movie Maker (offline, frame-exact),
# encodes bakeoff/<lane>/capture/capture.mp4 and cuts four stills. Run from the repository root on a
# machine with a display; with $DISPLAY empty it renders in software (Mesa llvmpipe and lavapipe under Xvfb).
set -euo pipefail
# shellcheck source=scripts/capture-lib.sh
source "$(dirname "$0")/capture-lib.sh"
lane="${1:?usage: capture-godot.sh LANE [ART_TRES]}"
art="${2:-res://art/lane_art.tres}"
proj="game/$lane"
mkdir -p "out/$lane"
rm -f "out/$lane/capture.avi"

# Movie Maker records at the project's own window size (Godot 4.7.2 ignores `--resolution` for the movie), so
# every Godot lane sets its viewport to 1920x1080 in project.godot; encode rejects any other size.

# Godot changes into --path before opening the movie file, so the path is relative to the project.
render godot --path "$proj" --write-movie "../../out/$lane/capture.avi" --fixed-fps 60 \
  res://tests/replay_runner.tscn -- "--replay=res://replays/level01.replay.json" --capture "--art=$art"
encode "$lane" -i "out/$lane/capture.avi"
