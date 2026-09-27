class_name Player2D
extends CharacterBody2D
## The test mechanic's player (docs/bakeoff/mechanic.md, Tuning). Origin at the feet. THROWAWAY.
const TILE := 64.0
const GRAVITY := 40.0 * TILE
const RUN_SPEED := 8.0 * TILE
const JUMP_SPEED := 15.5 * TILE
const DASH_SPEED := 30.0 * TILE
const DASH_TICKS := 12
signal reached_goal
signal touched_hazard
var facing := 1
var dash_ticks_left := 0
var air_dash_used := false
var double_jump_used := false
var died := false

func _ready() -> void:
	collision_layer = 2; collision_mask = 1
	var shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new(); rect.size = Vector2(0.8 * TILE, 1.6 * TILE); shape.shape = rect
	shape.position = Vector2(0, -0.8 * TILE)
	add_child(shape)

func _physics_process(delta: float) -> void:
	var dir := int(Input.is_action_pressed("right")) - int(Input.is_action_pressed("left"))
	if dir != 0: facing = dir
	if Input.is_action_just_pressed("switch"): Resonance.cycle()
	if is_on_floor(): air_dash_used = false; double_jump_used = false
	if dash_ticks_left > 0:
		dash_ticks_left -= 1; velocity = Vector2(facing * DASH_SPEED, 0)
	else:
		velocity.x = dir * RUN_SPEED
		velocity.y = minf(velocity.y + GRAVITY * delta, 3.0 * JUMP_SPEED)
		if Input.is_action_just_pressed("jump"):
			if is_on_floor(): velocity.y = -JUMP_SPEED
			elif Resonance.can_double_jump() and not double_jump_used: double_jump_used = true; velocity.y = -JUMP_SPEED
		if Input.is_action_just_pressed("dash") and Resonance.can_dash() and (is_on_floor() or not air_dash_used):
			if not is_on_floor(): air_dash_used = true
			dash_ticks_left = DASH_TICKS; velocity = Vector2(facing * DASH_SPEED, 0)
	move_and_slide()

## The level cell the feet stand in (feet exactly on a floor read as the cell above it).
func cell() -> Vector2i:
	return Vector2i(floori(global_position.x / TILE), floori((global_position.y - 1.0) / TILE))

func on_area(area: Area2D) -> void:
	match String(area.get_meta("kind")):
		"orb_red": Resonance.acquire("red"); area.queue_free()
		"orb_green": Resonance.acquire("green"); area.queue_free()
		"goal": reached_goal.emit()
		"hazard": died = true; touched_hazard.emit()
