#!/usr/bin/env bash
# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# Imports the project, runs every replay in replays/, and for each
# must_fail_without entry re-runs with that ability disabled and requires
# the run to fail. Exits non-zero on any problem.
set -u
cd "$(dirname "${BASH_SOURCE[0]}")"

GODOT="${GODOT_BIN:-/home/sami/.local/share/mise/installs/godot/4.7.2-stable/Godot_v4.7.2-stable_linux.x86_64}"
IMPORT_LOG="$(mktemp)"

echo "== importing project =="
"$GODOT" --headless --editor --path . --quit >"$IMPORT_LOG" 2>&1
fail=0
if grep -q "SCRIPT ERROR\|Parse Error" "$IMPORT_LOG"; then
	echo "SCRIPT ERROR during import:"
	grep "SCRIPT ERROR\|Parse Error" "$IMPORT_LOG"
	fail=1
fi
rm -f "$IMPORT_LOG"

run_replay() {
	"$GODOT" --headless --fixed-fps 60 --path . res://tests/replay_runner.tscn -- "--replay=res://replays/$1.replay.json" "${2:-}"
}

pass_count=0
fail_count=0

echo "== replays =="
for f in replays/*.replay.json; do
	id="$(basename "$f" .replay.json)"
	out="$(run_replay "$id")"
	rc=$?
	report="$(printf '%s\n' "$out" | tail -n1)"
	if [ $rc -eq 0 ]; then
		echo "PASS  $id  $report"
		pass_count=$((pass_count + 1))
	else
		echo "FAIL  $id  $report"
		fail_count=$((fail_count + 1))
		fail=1
	fi

	must_fail="$(python3 -c "import json; d=json.load(open('$f')); print(','.join(d.get('must_fail_without', [])))")"
	if [ -n "$must_fail" ]; then
		IFS=',' read -ra abilities <<<"$must_fail"
		for a in "${abilities[@]}"; do
			nout="$(run_replay "$id" "--disable=$a")"
			nrc=$?
			nreport="$(printf '%s\n' "$nout" | tail -n1)"
			if [ $nrc -ne 0 ]; then
				echo "PASS  $id --disable=$a (correctly failed)  $nreport"
				pass_count=$((pass_count + 1))
			else
				echo "FAIL  $id --disable=$a (should have failed, but succeeded)  $nreport"
				fail_count=$((fail_count + 1))
				fail=1
			fi
		done
	fi
done

echo ""
echo "== summary: $pass_count passed, $fail_count failed =="
exit $fail
