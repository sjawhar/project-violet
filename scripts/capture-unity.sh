#!/usr/bin/env bash
# THROWAWAY (Phase 1 bake-off). Runs the U-D lane's exported player on its replay with frame capture
# (the --replay/--capture flags are the lane's own, defined in its Task 9 plan), encodes
# bakeoff/u-d/capture/capture.mp4 at 60 fps and cuts four stills. Run from the repository root after the
# lane's build; with $DISPLAY empty the player renders in software (Mesa llvmpipe and lavapipe under Xvfb).
set -euo pipefail
# shellcheck source=scripts/capture-lib.sh
source "$(dirname "$0")/capture-lib.sh"
lane=u-d
player="out/$lane/violet-$lane.x86_64"
frames="out/$lane/frames"
[ -x "$player" ] || { echo "capture-unity: $player is missing; build the lane first" >&2; exit 1; }
rm -rf "$frames"
mkdir -p "$frames"

render "$player" --replay "$PWD/game/$lane/Assets/StreamingAssets/bakeoff/level01.replay.json" \
  --capture "$PWD/$frames" -screen-width 1920 -screen-height 1080
encode "$lane" "the player's --capture frames must be 1920x1080, the size -screen-width/-screen-height ask for" -framerate 60 -i "$frames/frame_%06d.png"
