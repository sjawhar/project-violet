## THROWAWAY — Violet mechanics lab, presentation component.
## Follows a target with facing lookahead and a vertical deadzone, clamps to
## the room, and supports a decaying shake. Drop into
## `prototypes/mechanics-lab/lab/juice/camera_rig.gd` unchanged.
class_name CameraRig
extends Camera2D

const LOOKAHEAD_PX := 128.0
const DEADZONE_HALF_HEIGHT := 60.0
const FOLLOW_RATE := 10.0
const RNG_SEED := 20261003

var _target: Node2D
var _room_rect: Rect2 = Rect2()
var _has_room_rect := false
var _base_position := Vector2.ZERO
var _deadzone_center_y := 0.0
var _initialized := false

var _shake_strength := 0.0
var _shake_duration := 0.0
var _shake_time_left := 0.0
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	_rng.seed = RNG_SEED


func follow(target: Node2D) -> void:
	_target = target
	if not _initialized:
		snap()


func set_room_rect(r: Rect2) -> void:
	_room_rect = r
	_has_room_rect = r.size.x > 0.0 and r.size.y > 0.0


func shake(strength_px: float, duration_s: float) -> void:
	_shake_strength = strength_px
	_shake_duration = duration_s
	_shake_time_left = duration_s


func snap() -> void:
	_initialized = true
	_shake_time_left = 0.0
	if _target == null:
		return
	_base_position = _target.global_position
	_deadzone_center_y = _base_position.y
	global_position = _clamp_to_room(_base_position)
	reset_physics_interpolation()


func _physics_process(delta: float) -> void:
	if _target == null:
		return
	var facing: int = _target.get("facing") if _target.get("facing") != null else 1
	var target_pos: Vector2 = _target.global_position

	var dy: float = target_pos.y - _deadzone_center_y
	if dy > DEADZONE_HALF_HEIGHT:
		_deadzone_center_y += dy - DEADZONE_HALF_HEIGHT
	elif dy < -DEADZONE_HALF_HEIGHT:
		_deadzone_center_y += dy + DEADZONE_HALF_HEIGHT

	var desired := Vector2(target_pos.x + facing * LOOKAHEAD_PX, _deadzone_center_y)
	_base_position = _base_position.lerp(desired, clampf(delta * FOLLOW_RATE, 0.0, 1.0))

	var clamped := _clamp_to_room(_base_position)
	var shake_offset := Vector2.ZERO
	if _shake_time_left > 0.0:
		_shake_time_left = maxf(_shake_time_left - delta, 0.0)
		var falloff: float = _shake_time_left / maxf(_shake_duration, 0.0001)
		shake_offset = Vector2(_rng.randf_range(-1.0, 1.0), _rng.randf_range(-1.0, 1.0)) * _shake_strength * falloff
	global_position = clamped + shake_offset


func _clamp_to_room(p: Vector2) -> Vector2:
	if not _has_room_rect:
		return p
	var half: Vector2 = get_viewport_rect().size * 0.5 / maxf(zoom.x, 0.0001)
	var min_pos := _room_rect.position + half
	var max_pos := _room_rect.position + _room_rect.size - half
	var x: float = p.x
	var y: float = p.y
	if min_pos.x <= max_pos.x:
		x = clampf(p.x, min_pos.x, max_pos.x)
	else:
		x = _room_rect.position.x + _room_rect.size.x * 0.5
	if min_pos.y <= max_pos.y:
		y = clampf(p.y, min_pos.y, max_pos.y)
	else:
		y = _room_rect.position.y + _room_rect.size.y * 0.5
	return Vector2(x, y)
