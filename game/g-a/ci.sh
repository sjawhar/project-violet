#!/usr/bin/env bash
# THROWAWAY (Phase 1 bake-off, lane G-A): the lane's CI checks; writes bakeoff/g-a/reports/ (read by tools/bakeoff gallery).
set -euo pipefail; cd "$(dirname "$0")"; lane=g-a; rep="../../bakeoff/$lane/reports"; mkdir -p "$rep" "../../out/$lane"
cmp ../../docs/bakeoff/level01.greybox.json levels/level01.greybox.json
../../scripts/godot-fetch.sh .
godot --headless --path . --import
run() { godot --headless --fixed-fps 60 --path . "$@"; }
run res://tests/replay_runner.tscn -- --replay=res://replays/level01.replay.json > "$rep/replay.json"
if run res://tests/replay_runner.tscn -- --replay=res://replays/level01.replay.json --disable=dash > "$rep/replay-no-dash.json"; then echo "ci.sh: replay without dash reached the goal" >&2; exit 1; fi
if run res://tests/replay_runner.tscn -- --replay=res://replays/level01.replay.json --disable=double_jump > "$rep/replay-no-double-jump.json"; then echo "ci.sh: replay without double jump reached the goal" >&2; exit 1; fi
run res://tests/validate_tags.tscn > "$rep/tags.txt" 2>&1
if run res://tests/validate_tags.tscn -- --mutate > "$rep/tags-mutated.txt" 2>&1; then echo "ci.sh: tag validator passed a mutated level" >&2; exit 1; fi
godot --headless --path . --export-release Linux "../../out/$lane/violet-$lane.x86_64" > "$rep/export.log" 2>&1
test -x "../../out/$lane/violet-$lane.x86_64" && timeout 90 "../../out/$lane/violet-$lane.x86_64" --headless --quit-after 120 && ls -l "../../out/$lane/violet-$lane.x86_64" > "$rep/build.txt"
