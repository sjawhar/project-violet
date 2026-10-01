## THROWAWAY — sandbox-only demo wiring. Not part of the presentation
## contract; glues PlayerJuice/Scarf/CameraRig/Sfx/LabHud/LabMenu/TuningPanel
## to the scripted LabPlayer stand-in so the components can be seen running
## together, and the menu + tuning panel are reachable. Not copied by the
## integrator.
extends Node2D

const ROOM_RECT := Rect2(-300, -1400, 4500, 2000)
const RESONANCE_WINDOW_S := 40.0 / 60.0
const MENU_AUTO_ADVANCE_S := 0.8
const DEBUG_OPEN_TUNING_AT_S := 11.0

const EXPERIMENTS := [
	{
		"id": "feel",
		"title": "Movement feel",
		"question": "Does this feel right as the baseline? Tab compares with the bake-off's movement; F1 tunes it live.",
		"profile": "tuned",
	},
]
const ROOM := {
	"title": "Juice sandbox",
	"hint": "Watch the scripted loop: run, jump, double jump, dash, stomp, blink, swing.",
}

@onready var _player := $LabPlayer
@onready var _camera := $CameraRig
@onready var _juice := $PlayerJuice
@onready var _hud := $LabHud
@onready var _menu := $MenuLayer/LabMenu
@onready var _tuning := $TuningPanel

var _profile := PhysicsProfile.new()
var _done: Dictionary = {}
var _deaths := 0
var _room_time := 0.0
var _model_state := {"model": "ability_window", "colors": [], "selected": null, "timer_frac": -1.0, "breath_frac": -1.0}
var _menu_timer := 0.0
var _elapsed := 0.0
var _debug_tuning_opened := false


func _ready() -> void:
	_camera.set_room_rect(ROOM_RECT)
	_camera.follow(_player)
	_juice.bind(_player)
	_tuning.bind(_profile)
	_menu.show_experiments(EXPERIMENTS, _done)
	_menu.chosen.connect(_on_experiment_chosen)

	_player.jumped.connect(func(kind): Sfx.play(&"double_jump" if kind == &"double" else &"jump"))
	_player.landed.connect(_on_landed)
	_player.dash_started.connect(func(_dir): Sfx.play(&"dash"))
	_player.dash_ended.connect(func(): pass)
	_player.ability_used.connect(func(_ability, _color): pass)
	_player.resonance_changed.connect(_on_resonance_changed)
	_player.died.connect(_on_died)
	_player.respawned.connect(func(): _room_time = 0.0)
	_player.reached_goal.connect(func(): Sfx.play(&"goal"))
	_player.blinked.connect(func(_a, _b): Sfx.play(&"blink"))
	_player.stomp_impact.connect(func(): Sfx.play(&"stomp"); _camera.shake(10.0, 0.2))
	_player.swing_attached.connect(func(_a): Sfx.play(&"swing_attach"))


func _on_experiment_chosen(_experiment_id) -> void:
	_menu.visible = false
	_hud.show_room(EXPERIMENTS[0], ROOM)


func _on_landed(impact_speed: float) -> void:
	var hard: bool = absf(impact_speed) > 1200.0
	Sfx.play(&"land_hard" if hard else &"land_soft")
	if hard:
		_camera.shake(6.0, 0.15)


func _on_died() -> void:
	_deaths += 1
	Sfx.play(&"death")


func _on_resonance_changed(colors: Array) -> void:
	_model_state.colors = colors
	_model_state.selected = colors[0] if colors.size() > 0 else null
	_model_state.timer_frac = 1.0 if colors.size() > 0 else -1.0
	Sfx.play(&"resonate_on" if colors.size() > 0 else &"resonate_off")


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(&"ui_cancel"):
		_menu.visible = true


func _physics_process(delta: float) -> void:
	_room_time += delta
	if _model_state.timer_frac >= 0.0:
		_model_state.timer_frac = clampf(_model_state.timer_frac - delta / RESONANCE_WINDOW_S, 0.0, 1.0)
	_hud.update_state(_player, _model_state, _deaths, _room_time)

	if _menu.visible:
		_menu_timer += delta
		if _menu_timer >= MENU_AUTO_ADVANCE_S:
			_on_experiment_chosen("feel")

	_elapsed += delta
	if not _debug_tuning_opened and _elapsed >= DEBUG_OPEN_TUNING_AT_S:
		_debug_tuning_opened = true
		var ev := InputEventAction.new()
		ev.action = &"tune"
		ev.pressed = true
		Input.parse_input_event(ev)
