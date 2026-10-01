# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# Red ability. profile.dash_speed for profile.dash_ticks ticks, gravity
# suspended; facing-direction only unless profile.dash_eight_way, in which
# case held-direction (defaulting to facing if neutral). One air dash per
# airborne period (resets on landing); ground dashes are unlimited.
class_name DashAbility
extends Ability

var _ticks_left := 0
var _dir := Vector2.ZERO
var _air_dash_used := false

func _init() -> void:
	color = "red"

func try_start(player: LabPlayer, input: Dictionary) -> bool:
	if not input.get("dash_pressed", false):
		return false
	if not player.resonance_model.can_use(color):
		return false
	if not player.on_floor and _air_dash_used:
		return false
	var profile := player.profile
	var dir := Vector2(player.facing, 0.0)
	if profile.dash_eight_way >= 1:
		var held := Vector2(input.get("move_x", 0), input.get("move_y", 0))
		if held.length() > 0.01:
			dir = held
	dir = dir.normalized()
	_dir = dir
	_ticks_left = profile.dash_ticks
	if not player.on_floor:
		_air_dash_used = true
	player.facing = 1 if dir.x > 0.01 else (-1 if dir.x < -0.01 else player.facing)
	player.velocity = dir * profile.dash_speed * LabConstants.TILE_SIZE_PX
	player.state = &"dash"
	if profile.dash_freeze_ticks > 0:
		player.freeze(profile.dash_freeze_ticks)
	player.dash_started.emit(dir)
	player.ability_used.emit(&"dash", color)
	player.resonance_model.on_ability_used(color)
	return true

func physics_tick(player: LabPlayer) -> bool:
	if _ticks_left <= 0:
		return false
	_ticks_left -= 1
	player.velocity = _dir * player.profile.dash_speed * LabConstants.TILE_SIZE_PX
	if _ticks_left <= 0:
		var end_speed_px := player.profile.dash_end_speed * LabConstants.TILE_SIZE_PX
		player.velocity = Vector2(sign(_dir.x) * end_speed_px, 0.0)
		player.dash_ended.emit()
		return false
	return true

func on_landed() -> void:
	_air_dash_used = false
