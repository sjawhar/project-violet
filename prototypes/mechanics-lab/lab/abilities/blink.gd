# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# Blue ability: on an `ability` press, teleports up to BLINK_MAX_DIST_T
# tiles in the held 8-way direction (defaulting to facing when neutral),
# landing at the farthest free spot along that line even if solid geometry
# is in the way (it tunnels through, unlike dash, which stops at the first
# obstruction). A short freeze sells the impact; one air blink per airborne
# period, same pattern as DashAbility's one-air-dash (ground blinks are
# unlimited). Instantaneous, like DoubleJumpAbility: it never implements
# physics_tick, so Ability's default (returns false) hands movement back
# the very next tick.
class_name BlinkAbility
extends Ability

const BLINK_MAX_DIST_T := 3.5
const BLINK_FREEZE_TICKS := 3
const BLINK_STEP_PX := 2.0

var _air_used := false

func _init() -> void:
	color = "blue"

func try_start(player: LabPlayer, input: Dictionary) -> bool:
	if not input.get("ability_pressed", false):
		return false
	if not player.resonance_model.can_use(color):
		return false
	if not player.on_floor and _air_used:
		return false
	var dir := Vector2(input.get("move_x", 0), input.get("move_y", 0))
	if dir.length() < 0.01:
		dir = Vector2(player.facing, 0.0)
	dir = dir.normalized()
	var from := player.position
	var max_dist_px: float = BLINK_MAX_DIST_T * LabConstants.TILE_SIZE_PX
	var to := _farthest_free(player, dir, max_dist_px)
	if not player.on_floor:
		_air_used = true
	player.position = to
	player.velocity = Vector2.ZERO
	player.facing = 1 if dir.x > 0.01 else (-1 if dir.x < -0.01 else player.facing)
	player.reset_physics_interpolation()
	player.freeze(BLINK_FREEZE_TICKS)
	player.blinked.emit(from, to)
	player.ability_used.emit(&"blink", color)
	player.resonance_model.on_ability_used(color)
	return true

func on_landed() -> void:
	_air_used = false

## Marches from `max_dist_px` down to 0 along `dir` and returns the first
## (i.e. farthest) point whose AABB doesn't overlap solid geometry, so the
## blink can tunnel through walls thinner than its range.
func _farthest_free(player: LabPlayer, dir: Vector2, max_dist_px: float) -> Vector2:
	var steps := int(ceil(max_dist_px / BLINK_STEP_PX))
	for i in range(steps, -1, -1):
		var dist: float = minf(float(i) * BLINK_STEP_PX, max_dist_px)
		var candidate: Vector2 = player.position + dir * dist
		if _fits_at(player, candidate):
			return candidate
	return player.position

## Local AABB-vs-grid overlap check (duplicates the shape of
## LabPlayer._fits()/_aabb_at(), which are private); needed here because an
## ability doesn't otherwise get to ask "is this arbitrary point free".
func _fits_at(player: LabPlayer, pos: Vector2) -> bool:
	var room: RoomData = player.room
	var size: Vector2 = player.box_size_px
	var top_left := pos - Vector2(size.x * 0.5, size.y)
	var ts: float = room.tile_size_px
	var c0 := int(floor(top_left.x / ts))
	var c1 := int(floor((top_left.x + size.x - 0.01) / ts))
	var r0 := int(floor(top_left.y / ts))
	var r1 := int(floor((top_left.y + size.y - 0.01) / ts))
	var resonating: Array = player.resonance_model.resonating_colors()
	for r in range(r0, r1 + 1):
		for c in range(c0, c1 + 1):
			if room.is_solid(c, r, resonating):
				return false
	return true
