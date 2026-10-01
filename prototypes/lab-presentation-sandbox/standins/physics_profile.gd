## THROWAWAY STAND-IN — NOT DELIVERED.
## Mirrors `lab/physics_profile.gd` from the mechanics-lab design contract
## (prototypes/mechanics-lab) closely enough that `TuningPanel` can bind to a
## real `PhysicsProfile` and drive its generic `TUNABLES`-based sliders. Lives
## under standins/ so the integrator does not copy it; the core agent's real
## resource replaces it unchanged from the presentation components' point of
## view (same class_name, same field names, same to_dict/apply_dict shape).
class_name PhysicsProfile
extends Resource

## [{name, label, min, max, step, unit}, ...] — one entry per field below,
## values transcribed from the design contract's physics-profile table.
const TUNABLES := [
	{"name": "run_speed", "label": "Run speed", "min": 2.0, "max": 16.0, "step": 0.1, "unit": "t/s"},
	{"name": "ground_accel_time", "label": "Ground accel time", "min": 0.0, "max": 0.5, "step": 0.01, "unit": "s"},
	{"name": "ground_decel_time", "label": "Ground decel time", "min": 0.0, "max": 0.5, "step": 0.01, "unit": "s"},
	{"name": "air_accel_mult", "label": "Air accel mult", "min": 0.1, "max": 2.0, "step": 0.05, "unit": ""},
	{"name": "turn_accel_mult", "label": "Turn accel mult", "min": 0.5, "max": 3.0, "step": 0.05, "unit": ""},
	{"name": "jump_height", "label": "Jump height", "min": 1.0, "max": 6.0, "step": 0.05, "unit": "t"},
	{"name": "jump_time_to_apex", "label": "Jump time to apex", "min": 0.1, "max": 0.8, "step": 0.005, "unit": "s"},
	{"name": "min_jump_height", "label": "Min jump height", "min": 0.2, "max": 6.0, "step": 0.05, "unit": "t"},
	{"name": "fall_gravity_mult", "label": "Fall gravity mult", "min": 0.5, "max": 3.0, "step": 0.05, "unit": ""},
	{"name": "apex_hang_speed", "label": "Apex hang speed", "min": 0.0, "max": 6.0, "step": 0.1, "unit": "t/s"},
	{"name": "apex_hang_mult", "label": "Apex hang mult", "min": 0.1, "max": 1.0, "step": 0.05, "unit": ""},
	{"name": "max_fall_speed", "label": "Max fall speed", "min": 5.0, "max": 1000.0, "step": 1.0, "unit": "t/s"},
	{"name": "fast_fall_speed", "label": "Fast fall speed", "min": 5.0, "max": 1000.0, "step": 1.0, "unit": "t/s"},
	{"name": "coyote_ticks", "label": "Coyote ticks", "min": 0.0, "max": 15.0, "step": 1.0, "unit": "ticks"},
	{"name": "buffer_ticks", "label": "Buffer ticks", "min": 0.0, "max": 15.0, "step": 1.0, "unit": "ticks"},
	{"name": "corner_correct_px", "label": "Corner correct", "min": 0.0, "max": 32.0, "step": 1.0, "unit": "px"},
	{"name": "box_w", "label": "Box width", "min": 0.3, "max": 1.5, "step": 0.05, "unit": "t"},
	{"name": "box_h", "label": "Box height", "min": 0.5, "max": 2.5, "step": 0.05, "unit": "t"},
	{"name": "dash_speed", "label": "Dash speed", "min": 5.0, "max": 40.0, "step": 0.5, "unit": "t/s"},
	{"name": "dash_ticks", "label": "Dash ticks", "min": 1.0, "max": 30.0, "step": 1.0, "unit": "ticks"},
	{"name": "dash_freeze_ticks", "label": "Dash freeze ticks", "min": 0.0, "max": 10.0, "step": 1.0, "unit": "ticks"},
	{"name": "dash_end_speed", "label": "Dash end speed", "min": 0.0, "max": 20.0, "step": 0.5, "unit": "t/s"},
	{"name": "dash_eight_way", "label": "Dash 8-way", "min": 0.0, "max": 1.0, "step": 1.0, "unit": ""},
	{"name": "double_jump_height", "label": "Double jump height", "min": 1.0, "max": 6.0, "step": 0.05, "unit": "t"},
	{"name": "wall_jump", "label": "Wall jump enabled", "min": 0.0, "max": 1.0, "step": 1.0, "unit": ""},
	{"name": "wall_slide_speed", "label": "Wall slide speed", "min": 0.0, "max": 15.0, "step": 0.5, "unit": "t/s"},
	{"name": "wall_jump_push", "label": "Wall jump push", "min": 0.0, "max": 20.0, "step": 0.5, "unit": "t/s"},
	{"name": "resonance_ticks", "label": "Resonance ticks", "min": 10.0, "max": 300.0, "step": 1.0, "unit": "ticks"},
	{"name": "breath_ticks", "label": "Breath ticks", "min": 10.0, "max": 300.0, "step": 1.0, "unit": "ticks"},
]

@export var run_speed: float = 9.0
@export var ground_accel_time: float = 0.09
@export var ground_decel_time: float = 0.06
@export var air_accel_mult: float = 0.7
@export var turn_accel_mult: float = 1.6
@export var jump_height: float = 3.25
@export var jump_time_to_apex: float = 0.38
@export var min_jump_height: float = 1.1
@export var fall_gravity_mult: float = 1.7
@export var apex_hang_speed: float = 2.5
@export var apex_hang_mult: float = 0.5
@export var max_fall_speed: float = 18.0
@export var fast_fall_speed: float = 26.0
@export var coyote_ticks: float = 6
@export var buffer_ticks: float = 7
@export var corner_correct_px: float = 14
@export var box_w: float = 0.7
@export var box_h: float = 1.45
@export var dash_speed: float = 24.0
@export var dash_ticks: float = 10
@export var dash_freeze_ticks: float = 3
@export var dash_end_speed: float = 9.0
@export var dash_eight_way: float = 0
@export var double_jump_height: float = 2.4
@export var wall_jump: float = 0
@export var wall_slide_speed: float = 5.0
@export var wall_jump_push: float = 9.0
@export var resonance_ticks: float = 90
@export var breath_ticks: float = 120


func to_dict() -> Dictionary:
	var d := {}
	for tunable in TUNABLES:
		d[tunable.name] = get(tunable.name)
	return d


func apply_dict(d: Dictionary) -> void:
	for tunable in TUNABLES:
		if d.has(tunable.name):
			set(tunable.name, d[tunable.name])
