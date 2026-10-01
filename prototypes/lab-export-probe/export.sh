#!/usr/bin/env bash
# THROWAWAY (lab-export-probe). Generic Godot 4.7.2 export: imports the project, exports the Web
# and Linux x86_64 presets from export_presets.cfg, and fails loudly if either export log contains
# a script/parse error or an expected output file is missing or empty. Reusable unmodified for
# prototypes/mechanics-lab (just point it at that project dir): PROJECT_DIR must have its own
# export_presets.cfg with presets literally named "Web" and "Linux".
set -euo pipefail

GODOT="${GODOT_BIN:-/home/sami/.local/share/mise/installs/godot/4.7.2-stable/Godot_v4.7.2-stable_linux.x86_64}"

project="${1:?usage: export.sh PROJECT_DIR OUT_DIR}"
out="${2:?usage: export.sh PROJECT_DIR OUT_DIR}"
project="$(cd "$project" && pwd)"
mkdir -p "$out"
out="$(cd "$out" && pwd)"

[ -f "$project/project.godot" ] || { echo "export.sh: $project/project.godot not found" >&2; exit 1; }
[ -f "$project/export_presets.cfg" ] || { echo "export.sh: $project/export_presets.cfg not found" >&2; exit 1; }
[ -x "$GODOT" ] || { echo "export.sh: Godot binary not found/executable at $GODOT" >&2; exit 1; }

log="$(mktemp)"
trap 'rm -f "$log"' EXIT

fail_on_errors() {
  local label="$1"
  if grep -qiE 'SCRIPT ERROR|PARSE ERROR' "$log"; then
    echo "export.sh: $label export log contains a script/parse error:" >&2
    grep -iE 'SCRIPT ERROR|PARSE ERROR' "$log" >&2
    exit 1
  fi
}

require_file() {
  local path="$1"
  [ -s "$path" ] || { echo "export.sh: expected output missing or empty: $path" >&2; exit 1; }
}

echo "export.sh: importing $project"
"$GODOT" --headless --quit --path "$project" >"$log" 2>&1 || { cat "$log" >&2; echo "export.sh: import failed" >&2; exit 1; }
fail_on_errors "import"

echo "export.sh: exporting Web -> $out/web/index.html"
mkdir -p "$out/web"
"$GODOT" --headless --export-release "Web" "$out/web/index.html" --path "$project" >"$log" 2>&1 || { cat "$log" >&2; echo "export.sh: Web export failed" >&2; exit 1; }
cat "$log"
fail_on_errors "Web"
require_file "$out/web/index.html"
require_file "$out/web/index.pck"
require_file "$out/web/index.wasm"
require_file "$out/web/index.js"

echo "export.sh: exporting Linux -> $out/linux/"
mkdir -p "$out/linux"
linux_bin="$out/linux/$(basename "$project").x86_64"
"$GODOT" --headless --export-release "Linux" "$linux_bin" --path "$project" >"$log" 2>&1 || { cat "$log" >&2; echo "export.sh: Linux export failed" >&2; exit 1; }
cat "$log"
fail_on_errors "Linux"
require_file "$linux_bin"
require_file "$out/linux/$(basename "$project").pck"
chmod +x "$linux_bin"

echo "export.sh: done"
echo "--- output sizes ---"
du -h "$out/web"/* "$out/linux"/* 2>/dev/null | sort -k2
