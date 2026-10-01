# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# Custom AABB-vs-grid platformer controller. No Godot physics bodies: every
# tick moves X then Y in <= LabConstants.MAX_SUBSTEP_PX sub-steps against
# RoomData.is_solid(), so replays are bit-deterministic regardless of
# rendering frame rate. Runs entirely on a fixed 1/60s tick (TICK_DT), never
# the engine's variable `delta`, per DESIGN.md's determinism requirement.
class_name LabPlayer
extends Node2D

const TICK_DT := 1.0 / 60.0

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

var velocity := Vector2.ZERO
var facing := 1
var on_floor := false
var box_size_px := Vector2.ZERO
var neck_offset := Vector2.ZERO
var state: StringName = &"idle"
@onready var visual_root: Node2D = $VisualRoot

var profile: PhysicsProfile
var resonance_model: ResonanceModel
var room: RoomData
var abilities: Dictionary = {}
var acquired_colors: Dictionary = {}
var deaths := 0

var _active_ability: Ability
var _prev_on_floor := false
var _coyote_ticks_left := 0
var _jump_buffer_left := 0
var _cuttable_jump_active := false
var _freeze_ticks := 0
var _landing_impact_px_s := 0.0
var _prev_resonating: Array = []
var _cur_resonating: Array = []

func _ready() -> void:
	set_physics_process(true)

## Called once per room entry, before gameplay ticks.
func configure(p_profile: PhysicsProfile, p_resonance: ResonanceModel, p_room: RoomData, ability_names: Array) -> void:
	set_profile(p_profile)
	room = p_room
	abilities.clear()
	for n in ability_names:
		var a := AbilityRegistry.create(n)
		if a != null:
			abilities[n] = a
	# A previous room's ability can still be "owning movement" the instant
	# its goal is reached (e.g. reaching the goal cell mid-stomp, mid-dash,
	# or mid-swing) -- main.gd's _enter_room() does not free/recreate
	# LabPlayer between rooms of the same experiment, so without this reset
	# the stale Ability instance (now absent from the fresh `abilities`
	# dict above, but still referenced here) would resume driving velocity
	# on the very next tick of the new room, before any input and without
	# ever calling resonance_model.on_ability_used(). respawn_at() already
	# clears this for mid-room deaths; room entry needs the same clear.
	_active_ability = null
	resonance_model = p_resonance
	resonance_model.setup(self, profile)
	_prev_resonating = resonance_model.resonating_colors()
	_cur_resonating = _prev_resonating.duplicate()

## Live profile swap (Tab compare); keeps position/velocity/abilities/room.
func set_profile(p: PhysicsProfile) -> void:
	profile = p
	box_size_px = Vector2(p.box_w, p.box_h) * LabConstants.TILE_SIZE_PX
	# Negative X = the back of the neck when facing +1 (right); player_juice.gd
	# multiplies this by `facing`, so it flips to the other side when facing
	# flips, always landing behind rather than in front of the face.
	neck_offset = Vector2(-box_size_px.x * 0.3, -box_size_px.y * 0.85)

func has_color(c: String) -> bool:
	return acquired_colors.get(c, false)

func acquire_color(c: String) -> void:
	if not acquired_colors.get(c, false):
		acquired_colors[c] = true
		_play_sfx(&"orb")

func freeze(ticks: int) -> void:
	_freeze_ticks = maxi(_freeze_ticks, ticks)

func respawn_at(pos: Vector2) -> void:
	position = pos
	velocity = Vector2.ZERO
	facing = 1
	state = &"idle"
	on_floor = false
	_prev_on_floor = false
	_coyote_ticks_left = 0
	_jump_buffer_left = 0
	_active_ability = null
	for a: Ability in abilities.values():
		a.on_landed()
	if room != null:
		room.reset_broken()
	reset_physics_interpolation()
	respawned.emit()

func _physics_process(_delta: float) -> void:
	if room == null or profile == null or resonance_model == null:
		return
	if _freeze_ticks > 0:
		_freeze_ticks -= 1
		return
	if state == &"dead":
		return

	var input := _read_input()

	if input.switch_pressed:
		resonance_model.on_switch_pressed()
		_play_sfx(&"ui_move")
	resonance_model.on_resonate_held(input.resonate_held)
	resonance_model.tick()
	_cur_resonating = resonance_model.resonating_colors()
	_handle_resonance_change()
	_prev_resonating = _cur_resonating.duplicate()

	var ability_active := false
	if _active_ability != null:
		ability_active = _active_ability.physics_tick(self)
		if not ability_active:
			_active_ability = null

	if not ability_active:
		for name in abilities:
			if name == "double_jump":
				continue
			var a: Ability = abilities[name]
			if a.try_start(self, input):
				_active_ability = a
				ability_active = true
				break

	if not ability_active:
		_handle_horizontal(input)
		_handle_jump(input)
		_handle_gravity(input)

	_move_and_collide()
	_handle_landing_transition()
	_handle_hazard_goal_orb()
	if state == &"dead":
		return
	_update_state(ability_active)

func _read_input() -> Dictionary:
	var move_x := 0
	if Input.is_action_pressed("left"):
		move_x -= 1
	if Input.is_action_pressed("right"):
		move_x += 1
	var move_y := 0
	if Input.is_action_pressed("up"):
		move_y -= 1
	if Input.is_action_pressed("down"):
		move_y += 1
	return {
		"move_x": move_x,
		"move_y": move_y,
		"jump_pressed": Input.is_action_just_pressed("jump"),
		"jump_held": Input.is_action_pressed("jump"),
		"jump_released": Input.is_action_just_released("jump"),
		"dash_pressed": Input.is_action_just_pressed("dash"),
		"ability_pressed": Input.is_action_just_pressed("ability"),
		"switch_pressed": Input.is_action_just_pressed("switch"),
		"resonate_held": Input.is_action_pressed("resonate"),
		"down_held": Input.is_action_pressed("down"),
	}

func _handle_horizontal(input: Dictionary) -> void:
	var move_x: int = input.move_x
	if move_x != 0:
		facing = 1 if move_x > 0 else -1
	var target := float(move_x) * profile.run_speed * LabConstants.TILE_SIZE_PX
	var base_time: float = profile.ground_decel_time if target == 0.0 else profile.ground_accel_time
	var instant := base_time <= 0.0001
	var mult := 1.0
	if target != 0.0 and velocity.x != 0.0 and sign(target) != sign(velocity.x):
		mult *= profile.turn_accel_mult
	if not on_floor:
		mult *= maxf(profile.air_accel_mult, 0.0001)
	if instant:
		velocity.x = target
	else:
		var accel: float = (profile.run_speed * LabConstants.TILE_SIZE_PX) / base_time * mult
		velocity.x = move_toward(velocity.x, target, accel * TICK_DT)

func _handle_jump(input: Dictionary) -> void:
	if _jump_buffer_left > 0:
		_jump_buffer_left -= 1
	if input.jump_pressed:
		if on_floor:
			_do_ground_jump(&"ground")
		elif _coyote_ticks_left > 0:
			_do_ground_jump(&"coyote")
		else:
			var dj: Ability = abilities.get("double_jump")
			if dj == null or not dj.try_start(self, input):
				_jump_buffer_left = profile.buffer_ticks
	if velocity.y < 0.0 and input.jump_released and _cuttable_jump_active:
		var cutoff := -profile.min_jump_cutoff_speed() * LabConstants.TILE_SIZE_PX
		if velocity.y < cutoff:
			velocity.y = cutoff

func _do_ground_jump(kind: StringName) -> void:
	velocity.y = -profile.jump_speed() * LabConstants.TILE_SIZE_PX
	on_floor = false
	_coyote_ticks_left = 0
	_cuttable_jump_active = true
	state = &"jump"
	jumped.emit(kind)
	_play_sfx(&"jump")

## Called by abilities (double_jump, wall-jump if enabled) whose own ascent
## must not be clipped by the ground jump's early-release variable-height cut.
func disable_jump_cutoff() -> void:
	_cuttable_jump_active = false

func _handle_gravity(input: Dictionary) -> void:
	if on_floor and velocity.y >= 0.0:
		velocity.y = 0.0
		return
	var g_px := profile.gravity() * LabConstants.TILE_SIZE_PX
	var vy_abs := absf(velocity.y)
	var apex_hang_px := profile.apex_hang_speed * LabConstants.TILE_SIZE_PX
	var g_applied: float
	if vy_abs < apex_hang_px and input.jump_held:
		g_applied = g_px * profile.apex_hang_mult
	elif velocity.y >= 0.0:
		g_applied = g_px * profile.fall_gravity_mult
	else:
		g_applied = g_px
	velocity.y += g_applied * TICK_DT
	var fast_fall: bool = velocity.y > 0.0 and bool(input.down_held)
	var cap_px := (profile.fast_fall_speed if fast_fall else profile.max_fall_speed) * LabConstants.TILE_SIZE_PX
	if velocity.y > cap_px:
		velocity.y = cap_px

func _aabb_at(pos: Vector2) -> Rect2:
	return Rect2(pos - Vector2(box_size_px.x * 0.5, box_size_px.y), box_size_px)

func _overlapped_cells(aabb: Rect2) -> Array:
	var ts := room.tile_size_px
	var c0 := int(floor(aabb.position.x / ts))
	var c1 := int(floor((aabb.position.x + aabb.size.x - 0.01) / ts))
	var r0 := int(floor(aabb.position.y / ts))
	var r1 := int(floor((aabb.position.y + aabb.size.y - 0.01) / ts))
	var out: Array = []
	for r in range(r0, r1 + 1):
		for c in range(c0, c1 + 1):
			out.append(Vector2i(c, r))
	return out

func _fits(aabb: Rect2) -> bool:
	for cell in _overlapped_cells(aabb):
		if room.is_solid(cell.x, cell.y, _cur_resonating):
			return false
	return true

## Single-shot per-tick nudge (<= profile.corner_correct_px) so a near-miss on
## a ceiling corner or a ledge lip doesn't hard-stop the player.
func _try_corner_correction(dx: float, dy: float) -> void:
	var max_nudge := int(profile.corner_correct_px)
	if max_nudge <= 0:
		return
	if dy < 0.0 and not _fits(_aabb_at(position + Vector2(0.0, dy))):
		var pref_dir := signf(velocity.x) if velocity.x != 0.0 else float(facing)
		for dir in [pref_dir, -pref_dir]:
			if dir == 0.0:
				continue
			for nudge in range(1, max_nudge + 1):
				if _fits(_aabb_at(position + Vector2(dir * nudge, dy))):
					position.x += dir * nudge
					return
	if dx != 0.0 and not _fits(_aabb_at(position + Vector2(dx, 0.0))):
		for nudge in range(1, max_nudge + 1):
			if _fits(_aabb_at(position + Vector2(dx, -nudge))):
				position.y -= nudge
				return

func _move_axis(delta_total: float, is_x: bool) -> bool:
	var remaining := delta_total
	while absf(remaining) > 0.0001:
		var step_mag: float = minf(absf(remaining), LabConstants.MAX_SUBSTEP_PX)
		var dir: float = 1.0 if remaining > 0.0 else -1.0
		var step: float = step_mag * dir
		var trial := position
		if is_x:
			trial.x += step
		else:
			trial.y += step
		if _fits(_aabb_at(trial)):
			position = trial
			remaining -= step
			continue
		var best := 0
		var int_mag := int(floor(step_mag))
		for px in range(1, int_mag + 1):
			var p2 := position
			var s: float = px * dir
			if is_x:
				p2.x += s
			else:
				p2.y += s
			if _fits(_aabb_at(p2)):
				best = px
			else:
				break
		if best > 0:
			var p2 := position
			var s: float = best * dir
			if is_x:
				p2.x += s
			else:
				p2.y += s
			position = p2
		return true
	return false

func _move_and_collide() -> void:
	var dx := velocity.x * TICK_DT
	var dy := velocity.y * TICK_DT
	_try_corner_correction(dx, dy)
	var hit_x := _move_axis(dx, true)
	if hit_x:
		velocity.x = 0.0
	var was_falling := velocity.y > 0.0
	var hit_y := _move_axis(dy, false)
	if hit_y:
		if was_falling:
			_landing_impact_px_s = velocity.y
		velocity.y = 0.0
	var probe := position
	probe.y += 1.0
	on_floor = not _fits(_aabb_at(probe))

func _handle_landing_transition() -> void:
	if on_floor:
		_coyote_ticks_left = 0
		if not _prev_on_floor:
			landed.emit(absf(_landing_impact_px_s))
			_play_sfx(&"land_hard" if absf(_landing_impact_px_s) > 10.0 * LabConstants.TILE_SIZE_PX else &"land_soft")
			for a: Ability in abilities.values():
				a.on_landed()
			if _jump_buffer_left > 0:
				_do_ground_jump(&"buffered")
				_jump_buffer_left = 0
	else:
		if _prev_on_floor:
			_coyote_ticks_left = profile.coyote_ticks
		elif _coyote_ticks_left > 0:
			_coyote_ticks_left -= 1
	_prev_on_floor = on_floor

func _handle_resonance_change() -> void:
	var ended: Array = []
	for c in _prev_resonating:
		if not _cur_resonating.has(c):
			ended.append(c)
	if _cur_resonating != _prev_resonating:
		resonance_changed.emit(_cur_resonating)
		if _prev_resonating.is_empty() and not _cur_resonating.is_empty():
			_play_sfx(&"resonate_on")
		elif not _prev_resonating.is_empty() and _cur_resonating.is_empty():
			_play_sfx(&"resonate_off")
	if ended.is_empty():
		return
	if _fits(_aabb_at(position)):
		return
	var ts := room.tile_size_px
	var step := 4.0
	var n := int(ts / step)
	var candidates: Array[Vector2] = []
	for i in range(1, n + 1):
		candidates.append(Vector2(0.0, -i * step))
	for i in range(1, n + 1):
		candidates.append(Vector2(-i * step, 0.0))
		candidates.append(Vector2(i * step, 0.0))
	for off in candidates:
		if _fits(_aabb_at(position + off)):
			position += off
			_play_sfx(&"pass_through")
			return
	_die()

func _handle_hazard_goal_orb() -> void:
	if state == &"dead":
		return
	var cells := _overlapped_cells(_aabb_at(position))
	for cell in cells:
		if room.is_hazard(cell.x, cell.y):
			_die()
			return
	for cell in cells:
		var oc: String = room.orb_color_at(cell.x, cell.y)
		if oc != "":
			acquire_color(oc)
	for cell in cells:
		if room.is_goal(cell.x, cell.y):
			reached_goal.emit()
			_play_sfx(&"goal")
			return

func _die() -> void:
	state = &"dead"
	velocity = Vector2.ZERO
	deaths += 1
	died.emit()
	_play_sfx(&"death")

func _update_state(ability_active: bool) -> void:
	if ability_active:
		return
	if not on_floor:
		state = &"jump" if velocity.y < 0.0 else &"fall"
	elif absf(velocity.x) > 1.0:
		state = &"run"
	else:
		state = &"idle"

func _play_sfx(name: StringName, volume_db: float = 0.0) -> void:
	var sfx := get_node_or_null("/root/Sfx")
	if sfx != null:
		sfx.play(name, volume_db)

## Added by LabAbilities (wave 2). Whether `down` was *just* pressed this
# tick, as opposed to _read_input()'s "down_held" (continuously held, used
# for fast-fall): lets StompAbility fire on the press edge instead of every
# tick down is held in the air.
func is_down_just_pressed() -> bool:
	return Input.is_action_just_pressed("down")

## Added by LabAbilities (wave 2). Whether `ability` is currently held, as
# opposed to _read_input()'s "ability_pressed" (press edge, used by
# BlinkAbility): lets SwingAbility attach continuously ("hold near an
# anchor") rather than on a single press.
func is_ability_held() -> bool:
	return Input.is_action_pressed("ability")
