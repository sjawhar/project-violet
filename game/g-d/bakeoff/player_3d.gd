class_name Player3D
extends CharacterBody3D
## The test mechanic's player in metres, 1 tile = 1 m (docs/bakeoff/mechanic.md, Tuning). Origin at the feet;
## movement stays on the z = 0 plane. THROWAWAY.
const GRAVITY := 40.0
const RUN_SPEED := 8.0
const JUMP_SPEED := 15.5
const DASH_SPEED := 30.0
const DASH_TICKS := 12
signal reached_goal
signal touched_hazard
var facing := 1
var dash_ticks_left := 0
var air_dash_used := false
var double_jump_used := false
var died := false
## Rows in the level, so cell() can turn y-up metres back into greybox rows.
var level_height := 16

func _ready() -> void:
	collision_layer = 2; collision_mask = 1; axis_lock_linear_z = true
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new(); box.size = Vector3(0.8, 1.6, 0.8); shape.shape = box
	shape.position.y = 0.8
	add_child(shape)

func _physics_process(delta: float) -> void:
	var dir := int(Input.is_action_pressed("right")) - int(Input.is_action_pressed("left"))
	if dir != 0: facing = dir
	if Input.is_action_just_pressed("switch"): Resonance.cycle()
	if is_on_floor(): air_dash_used = false; double_jump_used = false
	if dash_ticks_left > 0:
		dash_ticks_left -= 1; velocity = Vector3(facing * DASH_SPEED, 0, 0)
	else:
		velocity.x = dir * RUN_SPEED
		velocity.y = maxf(velocity.y - GRAVITY * delta, -3.0 * JUMP_SPEED)
		if Input.is_action_just_pressed("jump"):
			if is_on_floor(): velocity.y = JUMP_SPEED
			elif Resonance.can_double_jump() and not double_jump_used: double_jump_used = true; velocity.y = JUMP_SPEED
		if Input.is_action_just_pressed("dash") and Resonance.can_dash() and (is_on_floor() or not air_dash_used):
			if not is_on_floor(): air_dash_used = true
			dash_ticks_left = DASH_TICKS; velocity = Vector3(facing * DASH_SPEED, 0, 0)
	move_and_slide()

## The level cell the feet stand in (feet exactly on a floor read as the cell above it). Same signature as Player2D.cell().
func cell() -> Vector2i:
	return Vector2i(floori(global_position.x), level_height - 1 - floori(global_position.y + 0.01))

func on_area(area: Area3D) -> void:
	match String(area.get_meta("kind")):
		"orb_red": Resonance.acquire("red"); area.queue_free()
		"orb_green": Resonance.acquire("green"); area.queue_free()
		"goal": reached_goal.emit()
		"hazard": died = true; touched_hazard.emit()
