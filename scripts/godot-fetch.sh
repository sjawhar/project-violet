#!/usr/bin/env bash
# THROWAWAY (Phase 1 bake-off). Installs what a Godot bake-off lane needs beyond mise's godot 4.7.2: the
# export templates, checked against the SHA512-SUMS.txt Godot publishes with the release.
# Idempotent: a second run downloads nothing and prints only the summary line.
set -euo pipefail
GODOT=4.7.2
TEMPLATES_SHA512=ca4d71c4d7b81dfc15d1a98baa07534aa95b03fdda78a0075b06672e1648d2e5f40980c9adc28d23e1b92e732ee7bf3461997aa804af74ec2fcd7a93ccb84079
project="${1:?usage: godot-fetch.sh PROJECT_DIR}"
[ -f "$project/project.godot" ] || { echo "godot-fetch: $project/project.godot not found" >&2; exit 1; }
tpl="$HOME/.local/share/godot/export_templates/$GODOT.stable"

if [ ! -f "$tpl/linux_release.x86_64" ]; then
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' EXIT  # a failed download or checksum leaves nothing behind
  curl -fsSL -o "$tmp/t.tpz" "https://github.com/godotengine/godot/releases/download/$GODOT-stable/Godot_v$GODOT-stable_export_templates.tpz"
  echo "$TEMPLATES_SHA512  $tmp/t.tpz" | sha512sum -c --quiet
  mkdir -p "$tpl"
  unzip -q -o -j "$tmp/t.tpz" 'templates/*' -d "$tpl"
fi

echo "godot-fetch: export templates in $tpl for $project"
