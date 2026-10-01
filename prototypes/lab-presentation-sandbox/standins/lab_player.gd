## THROWAWAY STAND-IN — NOT DELIVERED.
## Reproduces the `LabPlayer` API from the mechanics-lab design contract
## (signals, properties, `freeze()`) with a tiny scripted physics loop —
## run, jump, double jump, dash, land, stomp, blink, swing, death/respawn,
## goal — so the presentation components (`lab/juice/`, `lab/ui/`) can be
## built and verified against something that behaves like the real player
## without importing the core agent's actual implementation. Lives under
## standins/ so the integrator does not copy it.
class_name LabPlayer
extends Node2D

signal jumped(kind: StringName)
signal landed(impact_speed: float)
signal dash_started(dir: Vector2)
signal dash_ended()
signal ability_used(ability: StringName, color: StringName)
signal resonance_changed(colors: Array)
signal died()
signal respawned()
signal reached_goal()
signal blinked(from: Vector2, to: Vector2)
signal stomp_impact()
signal swing_attached(anchor: Vector2)
signal swing_released()

const TILE := 64.0
const GRAVITY := 2600.0
const JUMP_SPEED := 1150.0
const DOUBLE_JUMP_SPEED := 950.0
const RUN_SPEED := 560.0
const DASH_SPEED := 1500.0
const DASH_END_SPEED := 550.0
const DASH_TICKS := 10
const STOMP_SPEED := 1900.0
const BLINK_DISTANCE := 220.0
const GROUND_Y := 0.0
const CLEAR_RESONANCE_TICKS := 40
const DEATH_TICKS := 21

var velocity: Vector2 = Vector2.ZERO
var facing: int = 1
var on_floor: bool = true
var box_size_px: Vector2
var neck_offset: Vector2
var state: StringName = &"idle"
var visual_root: Node2D

var _freeze_ticks: int = 0
var _start_position: Vector2
var _phase: StringName = &"idle"
var _phase_tick: int = 0
var _double_jump_fired := false
var _air_dash_used := false
var _swing_anchor := Vector2.ZERO
var _run_origin_cache := {}


func _ready() -> void:
	box_size_px = Vector2(0.7, 1.45) * TILE
	neck_offset = Vector2(0.0, -box_size_px.y * 0.42)
	_start_position = position
	visual_root = Node2D.new()
	visual_root.name = "visual_root"
	add_child(visual_root)
	var placeholder := _PlaceholderBody.new()
	placeholder.box_size_px = box_size_px
	visual_root.add_child(placeholder)
	_enter_phase(&"idle")


## Pauses gameplay simulation for N physics ticks (mirrors the contract's
## dash hitstop / freeze behaviour).
func freeze(ticks: int) -> void:
	_freeze_ticks = max(_freeze_ticks, ticks)


func _physics_process(delta: float) -> void:
	if _freeze_ticks > 0:
		_freeze_ticks -= 1
		return
	_phase_tick += 1
	match _phase:
		&"idle":
			_tick_idle()
		&"run":
			_tick_run(delta)
		&"jump_double":
			_tick_jump_double(delta)
		&"clear_a":
			_tick_clear(&"run2")
		&"run2":
			_tick_run(delta)
		&"jump_dash":
			_tick_jump_dash(delta)
		&"dash":
			_tick_dash(delta)
		&"jump_dash_fall":
			_tick_fall(delta, &"clear_dash")
		&"clear_dash":
			_tick_clear(&"run3")
		&"run3":
			_tick_run(delta)
		&"jump_stomp":
			_tick_jump_stomp(delta)
		&"stomp":
			_tick_stomp(delta)
		&"clear_stomp":
			_tick_clear(&"run4")
		&"run4":
			_tick_run(delta)
		&"blink":
			_tick_blink()
		&"clear_blink":
			_tick_clear(&"swing")
		&"swing":
			_tick_swing(delta)
		&"swing_fall":
			_tick_fall(delta, &"death")
		&"death":
			_tick_death()
		&"goal":
			_tick_goal(delta)


func _enter_phase(next: StringName) -> void:
	_phase = next
	_phase_tick = 0
	match next:
		&"idle":
			state = &"idle"
			velocity = Vector2.ZERO
			on_floor = true
		&"run", &"run2", &"run3", &"run4":
			state = &"run"
			velocity = Vector2(facing * RUN_SPEED, 0.0)
			on_floor = true
		&"jump_double":
			_start_jump(&"jump_double")
			_double_jump_fired = false
		&"jump_dash":
			_start_jump(&"jump_dash")
			_air_dash_used = false
		&"jump_stomp":
			_start_jump(&"jump_stomp", 0.7)
		&"blink":
			var from := position
			var to := position + Vector2(facing * BLINK_DISTANCE, 0.0)
			ability_used.emit(&"blink", &"blue")
			resonance_changed.emit([&"blue"])
			position = to
			reset_physics_interpolation()
			blinked.emit(from, to)
			freeze(3)
			velocity = Vector2.ZERO
			state = &"idle"
		&"swing":
			_swing_anchor = position + Vector2(facing * 120.0, -220.0)
			swing_attached.emit(_swing_anchor)
			state = &"swing"
			on_floor = false
		&"death":
			died.emit()
			state = &"dead"
			velocity = Vector2.ZERO
		&"goal":
			state = &"run"
			velocity = Vector2(facing * RUN_SPEED, 0.0)


func _start_jump(next: StringName, impulse_mult: float = 1.0) -> void:
	_phase = next
	_phase_tick = 0
	jumped.emit(&"ground")
	velocity = Vector2(facing * RUN_SPEED, -JUMP_SPEED * impulse_mult)
	on_floor = false
	state = &"jump"


func _tick_idle() -> void:
	if _phase_tick >= 30:
		_enter_phase(&"run")


func _tick_run(delta: float) -> void:
	position += velocity * delta
	var distance := absf(position.x - _run_phase_origin())
	if distance >= 220.0:
		match _phase:
			&"run":
				_enter_phase(&"jump_double")
			&"run2":
				_enter_phase(&"jump_dash")
			&"run3":
				_enter_phase(&"jump_stomp")
			&"run4":
				_enter_phase(&"blink")


func _run_phase_origin() -> float:
	if not _run_origin_cache.has(_phase):
		_run_origin_cache[_phase] = position.x
	return _run_origin_cache[_phase]


func _tick_jump_double(delta: float) -> void:
	velocity.y += GRAVITY * delta
	position += velocity * delta
	if velocity.y >= 0.0 and not _double_jump_fired:
		_double_jump_fired = true
		velocity.y = -DOUBLE_JUMP_SPEED
		jumped.emit(&"double")
		ability_used.emit(&"double_jump", &"green")
		resonance_changed.emit([&"green"])
		state = &"jump"
		return
	state = &"jump" if velocity.y < 0.0 else &"fall"
	if _double_jump_fired and position.y >= GROUND_Y and velocity.y > 0.0:
		_land(GROUND_Y)
		_enter_phase(&"clear_a")


func _tick_jump_dash(delta: float) -> void:
	velocity.y += GRAVITY * delta
	position += velocity * delta
	state = &"jump" if velocity.y < 0.0 else &"fall"
	if velocity.y >= 0.0 and not _air_dash_used:
		_air_dash_used = true
		var dir := Vector2(facing, 0.0)
		dash_started.emit(dir)
		ability_used.emit(&"dash", &"red")
		resonance_changed.emit([&"red"])
		freeze(3)
		velocity = dir * DASH_SPEED
		state = &"dash"
		_phase = &"dash"
		_phase_tick = 0


func _tick_dash(delta: float) -> void:
	position += velocity * delta
	if _phase_tick >= DASH_TICKS:
		dash_ended.emit()
		velocity = Vector2(facing * DASH_END_SPEED, 0.0)
		state = &"fall"
		_phase = &"jump_dash_fall"
		_phase_tick = 0


func _tick_fall(delta: float, next_phase: StringName) -> void:
	velocity.y += GRAVITY * delta
	position += velocity * delta
	state = &"fall"
	if position.y >= GROUND_Y and velocity.y > 0.0:
		_land(GROUND_Y)
		_enter_phase(next_phase)


func _land(ground_y: float) -> void:
	var impact := velocity.y
	position.y = ground_y
	velocity = Vector2(facing * RUN_SPEED, 0.0)
	on_floor = true
	state = &"run"
	landed.emit(impact)


func _tick_clear(next_phase: StringName) -> void:
	if _phase_tick == 1:
		resonance_changed.emit([])
	if _phase_tick >= CLEAR_RESONANCE_TICKS:
		_run_origin_cache.erase(next_phase)
		_enter_phase(next_phase)


func _tick_jump_stomp(delta: float) -> void:
	velocity.y += GRAVITY * delta
	position += velocity * delta
	state = &"jump" if velocity.y < 0.0 else &"fall"
	if velocity.y >= 0.0:
		ability_used.emit(&"stomp", &"yellow")
		resonance_changed.emit([&"yellow"])
		velocity = Vector2(0.0, STOMP_SPEED)
		state = &"stomp"
		_phase = &"stomp"
		_phase_tick = 0


func _tick_stomp(delta: float) -> void:
	position += velocity * delta
	if position.y >= GROUND_Y:
		var impact := velocity.y
		position.y = GROUND_Y
		velocity = Vector2.ZERO
		on_floor = true
		state = &"idle"
		stomp_impact.emit()
		landed.emit(impact)
		_enter_phase(&"clear_stomp")


func _tick_blink() -> void:
	if _phase_tick >= 10:
		_enter_phase(&"clear_blink")


func _tick_swing(delta: float) -> void:
	var swing_duration := 40
	var t := float(_phase_tick) / float(swing_duration)
	var angle := lerp(-0.9, 0.9, t)
	var radius := 190.0
	var prev := position
	position = _swing_anchor + radius * Vector2(sin(angle), cos(angle))
	velocity = (position - prev) / delta
	if _phase_tick >= swing_duration:
		swing_released.emit()
		velocity = velocity * 1.1
		on_floor = false
		state = &"fall"
		_phase = &"swing_fall"
		_phase_tick = 0


func _tick_death() -> void:
	if _phase_tick >= DEATH_TICKS:
		respawned.emit()
		position = _start_position
		reset_physics_interpolation()
		facing = 1
		state = &"idle"
		_enter_phase(&"goal")


func _tick_goal(delta: float) -> void:
	position += velocity * delta
	if _phase_tick >= 20:
		reached_goal.emit()
		_run_origin_cache.clear()
		_enter_phase(&"idle")


## Plain placeholder rectangle — what core draws into `visual_root` until the
## presentation agent's `PlayerJuice.bind()` replaces it with the real body.
class _PlaceholderBody:
	extends Node2D

	var box_size_px: Vector2

	func _draw() -> void:
		var rect := Rect2(-box_size_px.x * 0.5, -box_size_px.y, box_size_px.x, box_size_px.y)
		draw_rect(rect, Color(0.6, 0.6, 0.6, 0.6), false, 2.0)
