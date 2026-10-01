# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# Blue ability: holding `ability` within SWING_RANGE_T tiles of an `anchor`
# cell attaches a fixed-length rope to the nearest one in range and turns
# the player into a simple gravity pendulum (theta'' = -(g/len) sin theta),
# plus a pump from left/right input, integrated one tick at a time.
# Releasing `ability` (or landing) detaches, keeping the swing's tangential
# velocity with a RELEASE_BOOST bonus. physics_tick expresses the
# pendulum's per-tick target position as a velocity ((target - position) /
# TICK_DT) rather than writing player.position directly, so the move still
# goes through LabPlayer._move_and_collide()'s normal collision handling
# (e.g. a platform_blue the swing arcs through while blue resonates), same
# as every other ability here. Uses LabPlayer.is_ability_held() (wave 2
# addition) for the continuous "hold near an anchor" trigger, as opposed to
# the just-pressed edge blink/dash use.
class_name SwingAbility
extends Ability

const SWING_RANGE_T := 4.5
const PUMP_ANGULAR_ACCEL := 10.0
const MAX_ANGULAR_SPEED := 6.0
const ANGLE_LIMIT := 2.3
const RELEASE_BOOST := 1.1

var _anchor_px := Vector2.ZERO
var _rope_len_px := 0.0
var _angle := 0.0
var _angular_vel := 0.0

func _init() -> void:
	color = "blue"

func try_start(player: LabPlayer, _input: Dictionary) -> bool:
	if not player.is_ability_held():
		return false
	if not player.resonance_model.can_use(color):
		return false
	var anchor_px = _nearest_anchor(player)
	if anchor_px == null:
		return false
	_attach(player, anchor_px)
	return true

func physics_tick(player: LabPlayer) -> bool:
	if player.on_floor or not player.is_ability_held():
		_release(player)
		return false
	var g_px: float = player.profile.gravity() * LabConstants.TILE_SIZE_PX
	var angular_accel: float = -(g_px / _rope_len_px) * sin(_angle)
	var move_x := 0
	if Input.is_action_pressed("left"):
		move_x -= 1
	if Input.is_action_pressed("right"):
		move_x += 1
	if move_x != 0:
		angular_accel += float(move_x) * PUMP_ANGULAR_ACCEL
	_angular_vel = clampf(_angular_vel + angular_accel * LabPlayer.TICK_DT, -MAX_ANGULAR_SPEED, MAX_ANGULAR_SPEED)
	_angle += _angular_vel * LabPlayer.TICK_DT
	if _angle > ANGLE_LIMIT:
		_angle = ANGLE_LIMIT
		_angular_vel = 0.0
	elif _angle < -ANGLE_LIMIT:
		_angle = -ANGLE_LIMIT
		_angular_vel = 0.0
	var target: Vector2 = _anchor_px + Vector2(sin(_angle), cos(_angle)) * _rope_len_px
	player.velocity = (target - player.position) / LabPlayer.TICK_DT
	if absf(player.velocity.x) > 1.0:
		player.facing = 1 if player.velocity.x > 0.0 else -1
	player.state = &"swing"
	return true

func _attach(player: LabPlayer, anchor_px: Vector2) -> void:
	_anchor_px = anchor_px
	var to_player: Vector2 = player.position - anchor_px
	_rope_len_px = maxf(to_player.length(), 1.0)
	_angle = atan2(to_player.x, to_player.y)
	var tangent := Vector2(cos(_angle), -sin(_angle))
	_angular_vel = player.velocity.dot(tangent) / _rope_len_px
	player.state = &"swing"
	player.swing_attached.emit(anchor_px)
	player.ability_used.emit(&"swing", color)
	player.resonance_model.on_ability_used(color)

func _release(player: LabPlayer) -> void:
	var tangent := Vector2(cos(_angle), -sin(_angle))
	var speed: float = _angular_vel * _rope_len_px
	player.velocity = tangent * speed * RELEASE_BOOST
	player.swing_released.emit()

## Returns the nearest anchor cell's center in px within SWING_RANGE_T, or
## null if none are in range. Untyped return (not `-> Vector2`) so it can
## carry that "none found" case.
func _nearest_anchor(player: LabPlayer):
	var room: RoomData = player.room
	var max_dist_px: float = SWING_RANGE_T * LabConstants.TILE_SIZE_PX
	var best := Vector2.ZERO
	var best_dist := INF
	var found := false
	for cell: Vector2i in room.anchor_cells:
		var p: Vector2 = room.cell_center_px(cell.x, cell.y)
		var d: float = player.position.distance_to(p)
		if d <= max_dist_px and d < best_dist:
			best_dist = d
			best = p
			found = true
	if not found:
		return null
	return best
