# shellcheck shell=bash
# THROWAWAY (Phase 1 bake-off). Shared by capture-godot.sh and capture-unity.sh: source it, don't run it.
# Both run from the repository root under `set -euo pipefail`.

# render CMD...: runs CMD on the display; with $DISPLAY empty, in software (Mesa llvmpipe and lavapipe under Xvfb).
render() {
  if [ -n "${DISPLAY:-}" ]; then
    "$@"
    return
  fi
  local lavapipe
  lavapipe=$(compgen -G '/usr/share/vulkan/icd.d/lvp_icd*.json' | head -n 1) || true
  [ -n "$lavapipe" ] || { echo "$(basename "$0"): no DISPLAY and no lavapipe ICD (install mesa-vulkan-drivers)" >&2; return 1; }
  command -v xvfb-run >/dev/null || { echo "$(basename "$0"): no DISPLAY and no xvfb-run (install xvfb)" >&2; return 1; }
  LIBGL_ALWAYS_SOFTWARE=1 VK_ICD_FILENAMES="$lavapipe" xvfb-run -a -s "-screen 0 1920x1080x24" "$@"
}

# encode LANE FFMPEG_INPUT...: encodes out/LANE/capture/capture.mp4 from the given ffmpeg input, checks it is
# 60-90 s at 1920x1080, and cuts its four stills there (at 5, 20, 40 and 60 s, the last one just before the end of
# a 60.0 s capture). Only when all of that succeeds does it replace bakeoff/LANE/capture/; otherwise the lane's
# last good capture stays and the rejected one is left in out/LANE/capture/ to look at.
encode() {
  local lane=$1
  shift
  local staged="out/$lane/capture" out="bakeoff/$lane/capture" dur size t at still
  rm -rf "$staged"
  mkdir -p "$staged"
  ffmpeg -v error -y "$@" -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart "$staged/capture.mp4"
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$staged/capture.mp4")
  size=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$staged/capture.mp4")
  awk -v d="$dur" 'BEGIN { exit !(d >= 60 && d <= 90) }' || { echo "$(basename "$0"): $staged/capture.mp4 is ${dur}s, outside 60-90 s" >&2; return 1; }
  [ "$size" = 1920x1080 ] || {
    echo "$(basename "$0"): $staged/capture.mp4 is $size, not 1920x1080 (a Godot lane sets display/window/size/viewport_width and viewport_height to 1920x1080 in project.godot)" >&2
    return 1
  }
  for t in 05 20 40 60; do
    at=$(awk -v t="$t" -v d="$dur" 'BEGIN { print (t + 0 < d - 0.1 ? t + 0 : d - 0.1) }')
    still="$staged/still-$t.png"
    ffmpeg -v error -y -ss "$at" -i "$staged/capture.mp4" -frames:v 1 "$still"
    [ -s "$still" ] || { echo "$(basename "$0"): ffmpeg wrote no frame at ${at}s for $still" >&2; return 1; }
  done
  rm -rf "$out"
  mkdir -p "$(dirname "$out")"
  mv "$staged" "$out"
  echo "$(basename "$0"): wrote $out/capture.mp4 (${dur}s, $size) and $out/still-{05,20,40,60}.png"
}
