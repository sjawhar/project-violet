#!/usr/bin/env bash
# THROWAWAY (Phase 1 bake-off, lane Control): the lane's CI checks. Blender renders on oryx, not in CI, so this checks
# what the lane committed: bakeoff/control/reports/render.json and that capture/capture.mp4 decodes (plan Task 11).
set -euo pipefail; cd "$(dirname "$0")"; lane=control; report="../../bakeoff/$lane/reports/render.json"; capture="../../bakeoff/$lane/capture/capture.mp4"
[ -f "$report" ] || { echo "ci.sh: $report is missing: nothing has been rendered (bakeoff/$lane/LOG.md lists the blockers)" >&2; exit 1; }
python3 - "$report" <<'EOF'
import json, sys
clips = {"idle", "run", "jump", "fall", "double_jump", "dash", "land"}
render = json.load(open(sys.argv[1]))
names = {clip["name"] if isinstance(clip, dict) else clip for clip in render["clips"]}
problems = [f"clips missing {', '.join(sorted(clips - names))}"] if clips - names else []
if not isinstance(render["frames"], int) or isinstance(render["frames"], bool) or render["frames"] <= 0:
    problems.append(f"frames {render['frames']!r} is not a positive integer")
if render["device"] not in ("CUDA", "CPU"):
    problems.append(f"device {render['device']!r} is not CUDA or CPU")
if not 60 <= render["seconds"] <= 90:
    problems.append(f"seconds {render['seconds']!r} is not 60-90")
if problems:
    sys.exit("ci.sh: render.json: " + "; ".join(problems))
EOF
[ -f "$capture" ] || { echo "ci.sh: $capture is missing" >&2; exit 1; }
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$capture"
