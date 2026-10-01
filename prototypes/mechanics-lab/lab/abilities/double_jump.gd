# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# Green ability: one extra jump per airborne period, at the profile's own
# double_jump_height (independent of the main jump's height). LabPlayer calls
# try_start() only on a jump press that didn't satisfy a normal/coyote jump,
# i.e. it is responsible for the mutual exclusion with ground/coyote jumping.
# It is an instantaneous impulse, not an ongoing physics_tick.
class_name DoubleJumpAbility
extends Ability

var _used := false

func _init() -> void:
	color = "green"

func try_start(player: LabPlayer, input: Dictionary) -> bool:
	if not input.get("jump_pressed", false):
		return false
	if player.on_floor or _used:
		return false
	if not player.resonance_model.can_use(color):
		return false
	_used = true
	player.velocity.y = -player.profile.double_jump_speed() * LabConstants.TILE_SIZE_PX
	player.state = &"jump"
	player.jumped.emit(&"double")
	player.ability_used.emit(&"double_jump", color)
	player.resonance_model.on_ability_used(color)
	return true

func on_landed() -> void:
	_used = false
