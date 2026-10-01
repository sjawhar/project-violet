# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# Scene flow: menu -> experiment rooms -> menu. Owns the death/respawn and
# profile-compare timing (tick-based, per DESIGN.md's determinism
# requirement); the menu/HUD/camera/room-view nodes are drop-in mount
# points for the presentation agent's polished replacements (see each
# placeholder script's header).
extends Node

const PlayerScene := preload("res://lab/player.tscn")
const RoomViewScript := preload("res://lab/room_view.gd")
const PlayerJuiceScript := preload("res://lab/juice/player_juice.gd")

const RESPAWN_TICKS := 21  # 0.35s @ 60 ticks/s
# A darker shade of room_view.gd's own background (#1F2430), so a room
# smaller than the 1920x1080 viewport sits in a dark frame instead of
# Godot's default mid-gray clear color (project.godot's
# default_clear_color setting alone doesn't reach this 2D-only
# GL-Compatibility viewport, confirmed against the actual web export).
const BACKDROP_COLOR := Color8(0x15, 0x18, 0x1F)

@onready var world: Node2D = $World
@onready var camera: Camera2D = $Camera
@onready var menu: Control = $MenuLayer/MenuRoot
@onready var hud: CanvasLayer = $HudLayer
@onready var tuning_panel: CanvasLayer = $TuningLayer

var _experiments: Array = []
var _done: Dictionary = {}
var _tuned_profile: PhysicsProfile = load("res://lab/profiles/tuned.tres")
var _bakeoff_profile: PhysicsProfile = load("res://lab/profiles/bakeoff.tres")
var _using_bakeoff := false

var _player: LabPlayer
var _player_juice: Node2D
var _room: RoomData
var _room_view: Node2D
var _current_experiment: Dictionary
var _room_index := 0
var _deaths := 0
var _room_ticks := 0
var _respawn_ticks_left := 0
var _in_room := false

func _ready() -> void:
	_setup_backdrop()
	_experiments = ExperimentsData.load_all()
	menu.chosen.connect(_on_experiment_chosen)
	tuning_panel.changed.connect(func(): _player.set_profile(_player.profile) if _player != null else null)
	_goto_menu()

## A CanvasLayer behind every other layer (World's Node2D content is
## implicitly CanvasLayer 0; negative layers draw before/under it), filling
## the whole screen regardless of camera position or room size.
func _setup_backdrop() -> void:
	var layer := CanvasLayer.new()
	layer.layer = -10
	add_child(layer)
	var rect := ColorRect.new()
	rect.color = BACKDROP_COLOR
	rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(rect)

func _goto_menu() -> void:
	_in_room = false
	if _player != null:
		_player.queue_free()
		_player = null
	if _room_view != null:
		_room_view.queue_free()
		_room_view = null
	hud.visible = false
	menu.visible = true
	menu.show_experiments(_experiments, _done)

func _on_experiment_chosen(experiment_id: String) -> void:
	var exp := ExperimentsData.find(_experiments, experiment_id)
	if exp.is_empty():
		return
	_current_experiment = exp
	_room_index = 0
	_deaths = 0
	_enter_room()

func _enter_room() -> void:
	var rooms: Array = _current_experiment.get("rooms", [])
	if _room_index >= rooms.size():
		_done[str(_current_experiment.get("id", ""))] = true
		_goto_menu()
		return

	var room_id := str(rooms[_room_index])
	_room = RoomLoader.load_room(room_id)
	if _room == null:
		push_error("main: could not load room '%s', returning to menu" % room_id)
		_goto_menu()
		return

	menu.visible = false
	hud.visible = true
	_in_room = true

	if _room_view != null:
		_room_view.queue_free()
	_room_view = RoomViewScript.new()
	world.add_child(_room_view)
	# add_child() always appends to the end of World's children, but World
	# never reorders player/player_juice across room transitions (the "else"
	# branch below reuses them instead of re-adding them) — the second room
	# in an experiment would otherwise put this fresh room_view LAST in
	# sibling order, drawing its background/tiles (default z_index 0, tied
	# with the player's) on top of and hiding the player. Pinning it first
	# keeps the room under the player on every room entry, not just the
	# first.
	world.move_child(_room_view, 0)

	var ability_names: Array = _current_experiment.get("abilities", [])
	var resonance := ResonanceFactory.create(str(_current_experiment.get("model", "none")))
	var profile := _bakeoff_profile if _using_bakeoff else _tuned_profile

	if _player == null:
		_player = PlayerScene.instantiate()
		world.add_child(_player)
		for c in _current_experiment.get("acquired", []):
			_player.acquire_color(str(c))
		_player.died.connect(_on_player_died)
		_player.reached_goal.connect(_on_player_reached_goal)
		_player.stomp_impact.connect(func(): camera.shake(6.0, 0.15))
		_player.landed.connect(func(impact: float): camera.shake(4.0, 0.1) if absf(impact) > 10.0 * LabConstants.TILE_SIZE_PX else null)
		# configure() BEFORE bind(): PlayerJuice snapshots box_size_px once at bind
		# time (it doesn't track it live), so it must already reflect the real
		# profile, not the pre-configure() zero default.
		_player.configure(profile, resonance, _room, ability_names)
		_player_juice = PlayerJuiceScript.new()
		world.add_child(_player_juice)
		_player_juice.bind(_player)
	else:
		_player.configure(profile, resonance, _room, ability_names)

	_spawn_player()
	tuning_panel.bind(profile)
	_room_view.setup(_room, func() -> Array: return _player.resonance_model.resonating_colors() if _player.resonance_model else [])

	camera.follow(_player)
	camera.set_room_rect(_room.world_rect_px())
	camera.snap()

	_room_ticks = 0
	_respawn_ticks_left = 0
	hud.show_room(_current_experiment, {"title": _room.title, "hint": _room.hint, "id": _room.id})

func _spawn_player() -> void:
	_player.position = Vector2(
		_room.cell_center_px(_room.start_cell.x, _room.start_cell.y).x,
		float(_room.start_cell.y + 1) * _room.tile_size_px
	)
	_player.velocity = Vector2.ZERO
	_player.facing = 1
	_player.state = &"idle"
	_player.reset_physics_interpolation()

func _on_player_died() -> void:
	_deaths += 1
	_respawn_ticks_left = RESPAWN_TICKS

func _on_player_reached_goal() -> void:
	_room_index += 1
	_enter_room()

func _physics_process(_delta: float) -> void:
	if not _in_room:
		return
	_room_ticks += 1

	if Input.is_action_just_pressed("menu"):
		_goto_menu()
		return
	if Input.is_action_just_pressed("restart"):
		_spawn_player()
		camera.snap()
		_respawn_ticks_left = 0
	if Input.is_action_just_pressed("compare"):
		_using_bakeoff = not _using_bakeoff
		var profile := _bakeoff_profile if _using_bakeoff else _tuned_profile
		_player.set_profile(profile)
		tuning_panel.bind(profile)
		hud.show_profile_toast("bakeoff" if _using_bakeoff else "tuned")

	if _respawn_ticks_left > 0:
		_respawn_ticks_left -= 1
		if _respawn_ticks_left == 0:
			_spawn_player()
			camera.snap()
			_player.respawned.emit()

	var model_state: Dictionary = _player.resonance_model.hud_state() if _player.resonance_model else {}
	model_state["profile_name"] = "bakeoff" if _using_bakeoff else "tuned"
	model_state["experiment_title"] = str(_current_experiment.get("title", ""))
	hud.update_state(_player, model_state, _deaths, _room_ticks / 60.0)
