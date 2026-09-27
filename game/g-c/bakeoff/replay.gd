class_name Replay
extends RefCounted
## A violet-replay v1 input recording (docs/bakeoff/replay-format.md). THROWAWAY bake-off code; dimension-agnostic.
const ACTIONS := ["left", "right", "jump", "dash", "switch"]
var tick_hz: int
var level_path: String
var goal_by_tick: int
## pressed[t] = the actions held on tick t (the union of every segment covering t).
var pressed: Array[PackedStringArray] = []
var asserts: Array[Dictionary] = []

static func load_file(path: String) -> Replay:
	var text := FileAccess.get_file_as_string(path)
	assert(text != "", "%s: cannot read (%s)" % [path, error_string(FileAccess.get_open_error())])
	var data: Variant = JSON.parse_string(text)
	assert(data is Dictionary, "%s: not a JSON object" % path)
	assert(data.get("format") == "violet-replay" and int(data.get("version", 0)) == 1, "%s: not a violet-replay v1 file" % path)
	var replay := Replay.new()
	replay.tick_hz = int(data["tick_hz"]); assert(replay.tick_hz == 60, "%s: tick_hz must be 60" % path)
	replay.level_path = data["level"]; replay.goal_by_tick = int(data["expect"]["goal_by_tick"])
	var last := replay.goal_by_tick
	for seg: Dictionary in data["inputs"]:
		last = maxi(last, int(seg["to"]) if seg.has("to") else int(seg["at"]))
	replay.pressed.resize(last + 1)
	for t in replay.pressed.size(): replay.pressed[t] = PackedStringArray()
	for seg: Dictionary in data["inputs"]:
		var from := int(seg["from"]) if seg.has("from") else int(seg["at"])
		var to := int(seg["to"]) if seg.has("to") else from
		var actions: Array = seg["hold"] if seg.has("hold") else seg["press"]
		assert(from >= 0 and from <= to, "%s: bad tick range %d..%d" % [path, from, to])
		for a: String in actions:
			assert(a in ACTIONS, "%s: unknown action %s" % [path, a])
			for t in range(from, to + 1): if not replay.pressed[t].has(a): replay.pressed[t].append(a)
	for a: Dictionary in data.get("asserts", []): replay.asserts.append(a)
	return replay
