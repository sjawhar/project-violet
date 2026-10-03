# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# godot --headless --fixed-fps 60 --path prototypes/mechanics-lab \
#   res://tests/replay_runner.tscn -- --replay=res://replays/<id>.replay.json \
#   [--disable=dash,double_jump,...]
# Exit 0 iff the goal is reached by expect.goal_by_tick with no death.
# Last stdout line is a JSON report (violet-lab-replay v1, see DESIGN.md).
extends Node

const PlayerScene := preload("res://lab/player.tscn")
const ACTIONS: Array[String] = ["left", "right", "up", "down", "jump", "dash", "ability", "switch", "resonate"]

var _player: LabPlayer
var _room: RoomData
var _replay: Dictionary
var _disabled: Array[String] = []
var _trace := false
var _tick := 0
var _max_tick := 0
var _goal_by_tick := 0
var _inputs_by_tick: Dictionary = {}
var _died := false
var _goal_reached := false
var _finished := false
var _setup_ok := false
var _watchdog_frames := 0
const WATCHDOG_MAX_FRAMES := 7200

func _ready() -> void:
	process_physics_priority = -100
	var replay_path := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--replay="):
			replay_path = arg.substr(9)
		elif arg.begins_with("--disable="):
			var raw := arg.substr(10)
			if raw != "":
				for a in raw.split(","):
					_disabled.append(a)
		elif arg == "--trace":
			_trace = true
	if replay_path == "":
		_die_setup("no --replay= argument given")
		return
	if not FileAccess.file_exists(replay_path):
		_die_setup("replay file not found: %s" % replay_path)
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(replay_path))
	if typeof(parsed) != TYPE_DICTIONARY:
		_die_setup("replay did not parse as an object: %s" % replay_path)
		return
	_replay = parsed
	if _replay.get("format", "") != "violet-lab-replay":
		_die_setup("wrong replay format in %s" % replay_path)
		return

	var experiments := ExperimentsData.load_all()
	var exp_id: String = _replay.get("experiment", "")
	var exp := ExperimentsData.find(experiments, exp_id)
	if exp.is_empty():
		_die_setup("unknown experiment '%s'" % exp_id)
		return

	var room_id: String = _replay.get("room", "")
	_room = RoomLoader.load_room(room_id)
	if _room == null:
		_die_setup("could not load room '%s'" % room_id)
		return

	var profile_name: String = _replay.get("profile", exp.get("profile", "tuned"))
	var profile: PhysicsProfile = load("res://lab/profiles/%s.tres" % profile_name)
	if profile == null:
		_die_setup("could not load profile '%s'" % profile_name)
		return
	# Round 2 extension: "wall_jump" isn't an Ability (it's a profile flag, not
	# a lab/abilities/*.gd entry), so it can't be filtered via the
	# `ability_names` list below like dash/double_jump/stomp/blink/swing are.
	# --disable=wall_jump instead clones the loaded profile (never mutate the
	# shared cached .tres resource) with wall_jump forced to 0, matching
	# must_fail_without's "run with that ability disabled" contract for the
	# wall-jump trial's rooms.
	if _disabled.has("wall_jump"):
		profile = profile.duplicate()
		profile.wall_jump = 0

	var resonance := ResonanceFactory.create(exp.get("model", "none"))
	if resonance == null:
		_die_setup("could not create resonance model '%s'" % exp.get("model", ""))
		return

	_player = PlayerScene.instantiate()
	add_child(_player)
	# Round 2 extension: a replay may override the experiment's default
	# `acquired` list (e.g. a chapter room reached mid-chapter, where the
	# interactive player already picked up an earlier room's orb that this
	# room's own grid doesn't contain). Missing "acquired" in the replay
	# falls back to the experiment's, exactly round 1's behavior.
	for c in _replay.get("acquired", exp.get("acquired", [])):
		_player.acquire_color(c)
	var ability_names: Array = []
	for a in exp.get("abilities", []):
		if not _disabled.has(a):
			ability_names.append(a)
	_player.configure(profile, resonance, _room, ability_names)
	_player.position = Vector2(
		_room.cell_center_px(_room.start_cell.x, _room.start_cell.y).x,
		float(_room.start_cell.y + 1) * _room.tile_size_px
	)
	_player.reset_physics_interpolation()
	_player.reached_goal.connect(func(_to: String) -> void: _goal_reached = true)
	_player.died.connect(func() -> void: _died = true)

	_build_input_schedule()
	var expect: Dictionary = _replay.get("expect", {})
	_goal_by_tick = int(expect.get("goal_by_tick", 0))
	_max_tick = _goal_by_tick
	for seg: Dictionary in _replay.get("inputs", []):
		if seg.has("to"):
			_max_tick = maxi(_max_tick, int(seg["to"]))
		elif seg.has("at"):
			_max_tick = maxi(_max_tick, int(seg["at"]))
	_setup_ok = true

func _build_input_schedule() -> void:
	for seg: Dictionary in _replay.get("inputs", []):
		if seg.has("hold"):
			for t in range(int(seg["from"]), int(seg["to"]) + 1):
				var d: Dictionary = _inputs_by_tick.get(t, {})
				for a in seg["hold"]:
					d[a] = true
				_inputs_by_tick[t] = d
		elif seg.has("press"):
			var t := int(seg["at"])
			var d: Dictionary = _inputs_by_tick.get(t, {})
			for a in seg["press"]:
				d[a] = true
			_inputs_by_tick[t] = d

func _apply_tick_input() -> void:
	var active: Dictionary = _inputs_by_tick.get(_tick, {})
	for action in ACTIONS:
		var want: bool = active.get(action, false)
		if want and not Input.is_action_pressed(action):
			Input.action_press(action)
		elif not want and Input.is_action_pressed(action):
			Input.action_release(action)

func _physics_process(_delta: float) -> void:
	_watchdog_frames += 1
	if _watchdog_frames > WATCHDOG_MAX_FRAMES:
		print(JSON.stringify({"result": "error", "message": "watchdog: setup never completed or test never terminated"}))
		get_tree().quit(1)
		return
	if not _setup_ok or _finished:
		return
	if _trace:
		printerr("tick=%d pos=%s vel=%s on_floor=%s state=%s resonating=%s" % [
			_tick, _player.position, _player.velocity, _player.on_floor, _player.state,
			_player.resonance_model.resonating_colors() if _player.resonance_model else [],
		])
	if _died:
		_finish("died")
		return
	if _goal_reached:
		_finish("ok" if _tick <= _goal_by_tick else "too_slow")
		return
	if _tick > _max_tick + 10:
		_finish("timeout")
		return
	_apply_tick_input()
	_tick += 1

func _finish(result: String) -> void:
	_finished = true
	var report := {
		"experiment": _replay.get("experiment", ""),
		"room": _replay.get("room", ""),
		"profile": _replay.get("profile", ""),
		"disabled": _disabled,
		"result": result,
		"tick": _tick,
	}
	print(JSON.stringify(report))
	get_tree().quit(0 if result == "ok" else 1)

func _die_setup(msg: String) -> void:
	print(JSON.stringify({"result": "error", "message": msg}))
	get_tree().quit(1)
