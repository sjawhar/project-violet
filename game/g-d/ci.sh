#!/usr/bin/env bash
# THROWAWAY (Phase 1 bake-off, lane G-D): the lane's CI checks; writes bakeoff/g-d/reports/ (read by tools/bakeoff gallery).
set -euo pipefail; cd "$(dirname "$0")"; lane=g-d; rep="../../bakeoff/$lane/reports"; mkdir -p "$rep" "../../out/$lane"
cmp ../../docs/bakeoff/level01.greybox.json levels/level01.greybox.json
../../scripts/godot-fetch.sh .
godot --headless --path . --import
run() { godot --headless --fixed-fps 60 --path . "$@"; }
run res://tests/replay_runner.tscn -- --replay=res://replays/level01.replay.json > "$rep/replay.json"
if run res://tests/replay_runner.tscn -- --replay=res://replays/level01.replay.json --disable=dash > "$rep/replay-no-dash.json"; then echo "ci.sh: replay without dash reached the goal" >&2; exit 1; fi
if run res://tests/replay_runner.tscn -- --replay=res://replays/level01.replay.json --disable=double_jump > "$rep/replay-no-double-jump.json"; then echo "ci.sh: replay without double jump reached the goal" >&2; exit 1; fi
run res://tests/validate_tags.tscn > "$rep/tags.txt" 2>&1
if run res://tests/validate_tags.tscn -- --mutate > "$rep/tags-mutated.txt" 2>&1; then echo "ci.sh: tag validator passed a mutated level" >&2; exit 1; fi
run res://tests/rig_test.tscn  # the rig reader (tests/rig_test.gd); its log stays in the CI output, not in reports/
godot --headless --path . --export-release Linux "../../out/$lane/violet-$lane.x86_64" > "$rep/export.log" 2>&1
test -x "../../out/$lane/violet-$lane.x86_64"
# The exported game exits 0 even when its scripts fail to compile, so its log decides: Godot 4.7.2 prints compile and
# runtime script errors as "SCRIPT ERROR: ...", and engine errors, push_error and failed script loads as "ERROR: ...".
smoke="$(timeout 90 "../../out/$lane/violet-$lane.x86_64" --headless --quit-after 120 2>&1)" || { printf '%s\n' "$smoke" >&2; echo "ci.sh: the exported game failed" >&2; exit 1; }
if grep -E '^(SCRIPT ERROR|ERROR):' <<< "$smoke" >&2; then echo "ci.sh: the exported game logged the errors above" >&2; exit 1; fi
ls -l "../../out/$lane/violet-$lane.x86_64" > "$rep/build.txt"
