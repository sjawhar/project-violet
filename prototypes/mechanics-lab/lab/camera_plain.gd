# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# Minimal placeholder camera: follow + clamp to the room, no lookahead/
# deadzone/shake. lab/juice/camera_rig.gd (class_name CameraRig extends
# Camera2D, same follow/set_room_rect/shake/snap methods) replaces this
# script on the same "Camera" node later; main.gd's call sites don't change.
extends Camera2D

var _room_rect := Rect2()
var _target: Node2D

func follow(target: Node2D) -> void:
	_target = target

func set_room_rect(r: Rect2) -> void:
	_room_rect = r

func snap() -> void:
	_move(true)

func shake(_strength_px: float, _duration_s: float) -> void:
	pass  # presentation's CameraRig implements real screen shake.

func _process(_delta: float) -> void:
	_move(false)

func _move(instant: bool) -> void:
	if _target == null:
		return
	var half_vp: Vector2 = get_viewport_rect().size / zoom
	var cam_pos: Vector2 = _target.global_position
	if _room_rect.size.x > 0.0:
		cam_pos.x = _clamp_axis(cam_pos.x, _room_rect.position.x, _room_rect.size.x, half_vp.x)
		cam_pos.y = _clamp_axis(cam_pos.y, _room_rect.position.y, _room_rect.size.y, half_vp.y)
	if instant:
		global_position = cam_pos
		reset_physics_interpolation()
	else:
		global_position = global_position.lerp(cam_pos, 0.15)

func _clamp_axis(value: float, room_min: float, room_size: float, half_viewport: float) -> float:
	var lo: float = room_min + half_viewport * 0.5
	var hi: float = room_min + room_size - half_viewport * 0.5
	if hi < lo:
		return room_min + room_size * 0.5
	return clampf(value, lo, hi)
