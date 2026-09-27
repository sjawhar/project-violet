#!/usr/bin/env bash
# THROWAWAY (Phase 1 bake-off). Installs what a Godot bake-off lane needs beyond mise's godot 4.7.2:
# the export templates, checked against the SHA512-SUMS.txt Godot publishes with the release, and the
# spine-godot GDExtension (a rolling build of the 4.3 branch, so its sha256 is printed to show drift).
# It also registers the extension in PROJECT_DIR/.godot/extension_list.cfg: on a fresh project, the first
# headless `godot --import` finds the extension mid-scan and aborts (exit 134) at shutdown; with the extension
# already registered, Godot loads it at startup and the import exits 0 (measured on 4.7.2 + spine-godot 4.3).
# Idempotent: a second run downloads nothing and prints only the summary line.
set -euo pipefail
GODOT=4.7.2
SPINE=4.3
TEMPLATES_SHA512=ca4d71c4d7b81dfc15d1a98baa07534aa95b03fdda78a0075b06672e1648d2e5f40980c9adc28d23e1b92e732ee7bf3461997aa804af74ec2fcd7a93ccb84079
project="${1:?usage: godot-fetch.sh PROJECT_DIR}"
tpl="$HOME/.local/share/godot/export_templates/$GODOT.stable"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT  # a failed download or checksum leaves nothing behind

if [ ! -f "$tpl/linux_release.x86_64" ]; then
  curl -fsSL -o "$tmp/t.tpz" "https://github.com/godotengine/godot/releases/download/$GODOT-stable/Godot_v$GODOT-stable_export_templates.tpz"
  echo "$TEMPLATES_SHA512  $tmp/t.tpz" | sha512sum -c --quiet
  mkdir -p "$tpl"
  unzip -q -o -j "$tmp/t.tpz" 'templates/*' -d "$tpl"
fi

if [ ! -f "$project/bin/spine_godot_extension.gdextension" ]; then
  curl -fsSL -o "$tmp/s.zip" "https://spine-godot.s3.eu-central-1.amazonaws.com/$SPINE/$GODOT-stable/spine-godot-extension-$SPINE-$GODOT-stable.zip"
  unzip -q "$tmp/s.zip" -d "$tmp/s"
  mkdir -p "$project/bin"
  cp -r "$tmp"/s/bin/. "$project/bin/"
fi

registry="$project/.godot/extension_list.cfg"
entry=res://bin/spine_godot_extension.gdextension
mkdir -p "$project/.godot"
if ! grep -qxF "$entry" "$registry" 2>/dev/null; then
  # A hand-written registry may lack its final newline; appending straight onto it would corrupt both entries.
  if [ -s "$registry" ] && [ -n "$(tail -c 1 "$registry")" ]; then echo >> "$registry"; fi
  echo "$entry" >> "$registry"
fi

spine_sha=$(sha256sum "$project/bin/linux/libspine_godot.linux.template_release.x86_64.so" | cut -c1-12)
echo "godot-fetch: templates in $tpl; spine-godot in $project/bin (linux release .so sha256 $spine_sha)"
