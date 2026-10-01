# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# All numeric movement tuning in one place, in tiles/seconds/ticks (60 ticks/s).
# lab/player.gd converts to px using Constants.TILE_SIZE_PX. TUNABLES lists every
# field below so a generic tuning panel (lab/ui/tuning_panel.gd, presentation-owned)
# can build sliders without hardcoding field names.
class_name PhysicsProfile
extends Resource

const TUNABLES: Array[Dictionary] = [
	{"name": "run_speed", "label": "Run speed", "min": 2.0, "max": 16.0, "step": 0.1, "unit": "t/s"},
	{"name": "ground_accel_time", "label": "Ground accel time", "min": 0.0, "max": 0.5, "step": 0.01, "unit": "s"},
	{"name": "ground_decel_time", "label": "Ground decel time", "min": 0.0, "max": 0.5, "step": 0.01, "unit": "s"},
	{"name": "air_accel_mult", "label": "Air accel mult", "min": 0.1, "max": 2.0, "step": 0.05, "unit": "x"},
	{"name": "turn_accel_mult", "label": "Turn accel mult", "min": 1.0, "max": 4.0, "step": 0.1, "unit": "x"},
	{"name": "jump_height", "label": "Jump height", "min": 1.0, "max": 6.0, "step": 0.05, "unit": "t"},
	{"name": "jump_time_to_apex", "label": "Jump time to apex", "min": 0.1, "max": 0.8, "step": 0.005, "unit": "s"},
	{"name": "min_jump_height", "label": "Min jump height", "min": 0.2, "max": 6.0, "step": 0.05, "unit": "t"},
	{"name": "fall_gravity_mult", "label": "Fall gravity mult", "min": 1.0, "max": 3.0, "step": 0.05, "unit": "x"},
	{"name": "apex_hang_speed", "label": "Apex hang speed", "min": 0.0, "max": 6.0, "step": 0.1, "unit": "t/s"},
	{"name": "apex_hang_mult", "label": "Apex hang mult", "min": 0.1, "max": 1.0, "step": 0.05, "unit": "x"},
	{"name": "max_fall_speed", "label": "Max fall speed", "min": 10.0, "max": 1000.0, "step": 1.0, "unit": "t/s"},
	{"name": "fast_fall_speed", "label": "Fast fall speed", "min": 10.0, "max": 1000.0, "step": 1.0, "unit": "t/s"},
	{"name": "coyote_ticks", "label": "Coyote ticks", "min": 0, "max": 20, "step": 1, "unit": "ticks"},
	{"name": "buffer_ticks", "label": "Buffer ticks", "min": 0, "max": 20, "step": 1, "unit": "ticks"},
	{"name": "corner_correct_px", "label": "Corner correct", "min": 0, "max": 32, "step": 1, "unit": "px"},
	{"name": "box_w", "label": "Box width", "min": 0.3, "max": 1.5, "step": 0.05, "unit": "t"},
	{"name": "box_h", "label": "Box height", "min": 0.5, "max": 2.5, "step": 0.05, "unit": "t"},
	{"name": "dash_speed", "label": "Dash speed", "min": 5.0, "max": 40.0, "step": 0.5, "unit": "t/s"},
	{"name": "dash_ticks", "label": "Dash ticks", "min": 1, "max": 30, "step": 1, "unit": "ticks"},
	{"name": "dash_freeze_ticks", "label": "Dash freeze ticks", "min": 0, "max": 10, "step": 1, "unit": "ticks"},
	{"name": "dash_end_speed", "label": "Dash end speed", "min": 0.0, "max": 20.0, "step": 0.5, "unit": "t/s"},
	{"name": "dash_eight_way", "label": "Dash 8-way", "min": 0, "max": 1, "step": 1, "unit": "bool"},
	{"name": "double_jump_height", "label": "Double jump height", "min": 0.5, "max": 6.0, "step": 0.05, "unit": "t"},
	{"name": "wall_jump", "label": "Wall jump enabled", "min": 0, "max": 1, "step": 1, "unit": "bool"},
	{"name": "wall_slide_speed", "label": "Wall slide speed", "min": 0.0, "max": 10.0, "step": 0.1, "unit": "t/s"},
	{"name": "wall_jump_push", "label": "Wall jump push", "min": 0.0, "max": 20.0, "step": 0.5, "unit": "t/s"},
	{"name": "resonance_ticks", "label": "Resonance ticks", "min": 10, "max": 300, "step": 1, "unit": "ticks"},
	{"name": "breath_ticks", "label": "Breath ticks", "min": 10, "max": 300, "step": 1, "unit": "ticks"},
]

@export var run_speed := 9.0
@export var ground_accel_time := 0.09
@export var ground_decel_time := 0.06
@export var air_accel_mult := 0.7
@export var turn_accel_mult := 1.6
@export var jump_height := 3.25
@export var jump_time_to_apex := 0.38
@export var min_jump_height := 1.1
@export var fall_gravity_mult := 1.7
@export var apex_hang_speed := 2.5
@export var apex_hang_mult := 0.5
@export var max_fall_speed := 18.0
@export var fast_fall_speed := 26.0
@export var coyote_ticks := 6
@export var buffer_ticks := 7
@export var corner_correct_px := 14
@export var box_w := 0.7
@export var box_h := 1.45
@export var dash_speed := 24.0
@export var dash_ticks := 10
@export var dash_freeze_ticks := 3
@export var dash_end_speed := 9.0
@export var dash_eight_way := 0
@export var double_jump_height := 2.4
@export var wall_jump := 0
@export var wall_slide_speed := 5.0
@export var wall_jump_push := 9.0
@export var resonance_ticks := 90
@export var breath_ticks := 120

## Gravity magnitude in tiles/s^2, derived from jump_height and jump_time_to_apex: g = 2h/t^2.
func gravity() -> float:
	return 2.0 * jump_height / (jump_time_to_apex * jump_time_to_apex)

## Initial upward jump speed magnitude, tiles/s: v = 2h/t.
func jump_speed() -> float:
	return 2.0 * jump_height / jump_time_to_apex

## Upward speed to cut to on early jump release, so the jump peaks near min_jump_height.
func min_jump_cutoff_speed() -> float:
	return sqrt(2.0 * gravity() * min_jump_height)

## Double jump's own upward speed (independent of the main jump's height).
func double_jump_speed() -> float:
	return sqrt(2.0 * gravity() * double_jump_height)

func to_dict() -> Dictionary:
	var d := {}
	for t: Dictionary in TUNABLES:
		d[t.name] = get(t.name)
	return d

func apply_dict(d: Dictionary) -> void:
	for t: Dictionary in TUNABLES:
		if d.has(t.name):
			set(t.name, d[t.name])
