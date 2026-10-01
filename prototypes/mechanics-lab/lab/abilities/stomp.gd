# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# Yellow ability: pressing `down` while airborne drops the player straight
# down at STOMP_SPEED_T_S (no horizontal movement, gravity suspended),
# breaking any `cracked` cells in the fall path before the normal collision
# pass runs (RoomData.is_solid() treats an unbroken cracked cell as solid;
# room.break_cracked() clears that bit, so the stomp tunnels through
# instead of stopping) and continuing to fall. Ends, emitting stomp_impact,
# the tick after landing on solid ground (a non-cracked cell, or a wall or
# platform of a color that isn't currently resonating). Uses
# LabPlayer.is_down_just_pressed() (wave 2 addition) to tell a fresh air-dive
# press apart from merely holding down to fast-fall.
class_name StompAbility
extends Ability

const STOMP_SPEED_T_S := 30.0

func _init() -> void:
	color = "yellow"

func try_start(player: LabPlayer, _input: Dictionary) -> bool:
	if player.on_floor:
		return false
	if not player.is_down_just_pressed():
		return false
	if not player.resonance_model.can_use(color):
		return false
	player.velocity = Vector2(0.0, STOMP_SPEED_T_S * LabConstants.TILE_SIZE_PX)
	player.state = &"stomp"
	player.ability_used.emit(&"stomp", color)
	player.resonance_model.on_ability_used(color)
	_break_cracked_in_path(player)
	return true

func physics_tick(player: LabPlayer) -> bool:
	if player.on_floor:
		player.stomp_impact.emit()
		return false
	player.velocity = Vector2(0.0, STOMP_SPEED_T_S * LabConstants.TILE_SIZE_PX)
	_break_cracked_in_path(player)
	return true

## Breaks any `cracked` cell this tick's fall is about to sweep through, so
## the move it causes (LabPlayer._move_and_collide(), called right after
## this ability's tick) finds it already non-solid.
func _break_cracked_in_path(player: LabPlayer) -> void:
	var room: RoomData = player.room
	var ts: float = room.tile_size_px
	var hw: float = player.box_size_px.x * 0.5
	var h: float = player.box_size_px.y
	var y0: float = player.position.y
	var y1: float = y0 + player.velocity.y * LabPlayer.TICK_DT
	var c0 := int(floor((player.position.x - hw) / ts))
	var c1 := int(floor((player.position.x + hw - 0.01) / ts))
	var r0 := int(floor((minf(y0, y1) - h) / ts))
	var r1 := int(floor((maxf(y0, y1) - 0.01) / ts))
	for r in range(r0, r1 + 1):
		for c in range(c0, c1 + 1):
			if room.kind_at(c, r) == "cracked":
				room.break_cracked(c, r)
