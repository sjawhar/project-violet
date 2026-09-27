extends Node2D
## THROWAWAY completability test.
## godot --headless --fixed-fps 60 --path game/g-a res://tests/replay_runner.tscn -- --replay=res://replays/level01.replay.json [--trace] [--disable=dash,double_jump] [--capture] [--art=res://art/lane_art.tres]
## Exit 0: goal reached by expect.goal_by_tick, no hazard, every assert fired and held. Exit 1 otherwise. Last stdout line is a JSON report.
var replay: Replay; var game: Game2D; var tick := 0; var goal_tick := -1
var failures: PackedStringArray = []; var fired := {}; var args := {}
func _ready() -> void:
	process_physics_priority = -100
	args = parse_args(OS.get_cmdline_user_args()); assert(args.has("replay"), "--replay=PATH is required")
	replay = Replay.load_file(args["replay"])
	game = Game2D.new(); game.level_path = replay.level_path
	if args.has("art"): game.art = load(args["art"])
	add_child(game)
	Resonance.abilities_disabled = PackedStringArray(String(args.get("disable", "")).split(",", false))
	game.player.reached_goal.connect(func(): if goal_tick < 0: goal_tick = tick)
	game.player.touched_hazard.connect(func(): failures.append("tick %d: touched a hazard at %s" % [tick, game.player.cell()]))
func _physics_process(_delta: float) -> void:
	var now := replay.pressed[tick] if tick < replay.pressed.size() else PackedStringArray()
	var before := replay.pressed[tick - 1] if tick > 0 and tick - 1 < replay.pressed.size() else PackedStringArray()
	for a in before: if not now.has(a): Input.action_release(a)
	for a in now: if not before.has(a): Input.action_press(a)
	_check_asserts()
	if args.has("trace") and tick % 10 == 0: print("tick %d cell %s active=%s acquired=%s floor=%s" % [tick, game.player.cell(), Resonance.active, Resonance.acquired, game.player.is_on_floor()])
	var done := (goal_tick >= 0 or tick > replay.goal_by_tick or not failures.is_empty()) if not args.has("capture") else tick >= replay.pressed.size() - 1
	if done: _finish()
	tick += 1
func _check_asserts() -> void:
	var cell := game.player.cell()
	for i in replay.asserts.size():
		var a: Dictionary = replay.asserts[i]
		if fired.has(i) or Vector2i(int(a["cell"][0]), int(a["cell"][1])) != cell: continue
		fired[i] = tick
		if a.has("active_color") and Resonance.active != a["active_color"]: failures.append("tick %d at %s: active %s, expected %s" % [tick, cell, Resonance.active, a["active_color"]])
		if a.has("passable"):
			# `passable` names a color through its kind: every body of that color passable, every other tagged body solid.
			for tag in get_tree().get_nodes_in_group("resonance"):
				var expect: bool = tag.color == String(a["passable"]).get_slice("_", 1)
				if bool(tag.get_parent().get_meta("resonance_passable")) != expect: failures.append("tick %d: %s passable should be %s" % [tick, tag.get_parent().name, expect])
func _finish() -> void:
	for i in replay.asserts.size(): if not fired.has(i): failures.append("assert %d at cell %s never fired" % [i, replay.asserts[i]["cell"]])
	if goal_tick < 0: failures.append("goal not reached by tick %d (player at %s)" % [replay.goal_by_tick, game.player.cell()])
	var ok := failures.is_empty()
	print(JSON.stringify({"ok": ok, "goal_tick": goal_tick, "ticks": tick, "disabled": Resonance.abilities_disabled, "failures": failures}))
	get_tree().quit(0 if ok else 1)
static func parse_args(list: PackedStringArray) -> Dictionary:
	var out := {}
	for arg in list:
		if arg.begins_with("--"): var kv := arg.substr(2).split("=", true, 1); out[kv[0]] = kv[1] if kv.size() > 1 else true
	return out
