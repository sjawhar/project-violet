## THROWAWAY — Violet mechanics lab, presentation component.
## Capsule body with a face mark, squash/stretch on jump/land/dash, the
## trailing verlet Scarf, and CPUParticles2D juice (run dust, jump puff,
## landing dust, dash afterimages, stomp debris, blink trail). Drop into
## `prototypes/mechanics-lab/lab/juice/player_juice.gd` unchanged.
class_name PlayerJuice
extends Node2D


const BODY_COLOR := Color8(0xE8, 0xE3, 0xD8)
const FACE_COLOR := Color8(0x2B, 0x2F, 0x38)
const DUST_COLOR := Color(0.85, 0.82, 0.74, 0.75)
const DEBRIS_COLOR := Color(0.55, 0.5, 0.42, 0.9)

const REFERENCE_IMPACT := 1400.0
const RNG_SEED := 20261001

var _player: Node2D
var _body: _PlayerBody
var _scarf: Node2D
var _squash: Vector2 = Vector2.ONE
var _squash_tween: Tween
var _rng := RandomNumberGenerator.new()

var _run_dust: CPUParticles2D
var _jump_puff: CPUParticles2D
var _landing_dust: CPUParticles2D
var _stomp_debris: CPUParticles2D
var _was_running := false


func _ready() -> void:
	_rng.seed = RNG_SEED
	_run_dust = _make_particles({
		"amount": 12, "lifetime": 0.45, "one_shot": false, "explosiveness": 0.0,
		"spread_deg": 25.0, "speed_min": 20.0, "speed_max": 60.0, "gravity": Vector2(0, -40),
		"scale_min": 3.0, "scale_max": 6.0, "color": DUST_COLOR, "direction": Vector2(0, -1),
	})
	_jump_puff = _make_particles({
		"amount": 10, "lifetime": 0.3, "one_shot": true, "explosiveness": 0.9,
		"spread_deg": 40.0, "speed_min": 60.0, "speed_max": 140.0, "gravity": Vector2(0, 260),
		"scale_min": 3.0, "scale_max": 6.0, "color": DUST_COLOR, "direction": Vector2(0, -1),
	})
	_landing_dust = _make_particles({
		"amount": 10, "lifetime": 0.35, "one_shot": true, "explosiveness": 0.9,
		"spread_deg": 60.0, "speed_min": 40.0, "speed_max": 120.0, "gravity": Vector2(0, 200),
		"scale_min": 3.0, "scale_max": 7.0, "color": DUST_COLOR, "direction": Vector2(0, -1),
	})
	_stomp_debris = _make_particles({
		"amount": 16, "lifetime": 0.5, "one_shot": true, "explosiveness": 0.95,
		"spread_deg": 70.0, "speed_min": 80.0, "speed_max": 220.0, "gravity": Vector2(0, 500),
		"scale_min": 3.0, "scale_max": 8.0, "color": DEBRIS_COLOR, "direction": Vector2(0, -1),
	})
	_scarf = Scarf.new()
	add_child(_scarf)


## Wires this component to a `LabPlayer`: moves the capsule body into the
## player's `visual_root` (replacing core's placeholder) and connects every
## signal that drives juice.
func bind(player: Node) -> void:
	_player = player
	for child in player.visual_root.get_children():
		child.queue_free()
	_body = _PlayerBody.new()
	_body.box_size_px = player.box_size_px
	player.visual_root.add_child(_body)

	player.jumped.connect(_on_jumped)
	player.landed.connect(_on_landed)
	player.dash_started.connect(_on_dash_started)
	player.dash_ended.connect(_on_dash_ended)
	player.stomp_impact.connect(_on_stomp_impact)
	player.blinked.connect(_on_blinked)
	player.resonance_changed.connect(_on_resonance_changed)
	player.respawned.connect(_on_respawned)

	global_position = player.global_position
	_scarf.reset(_neck_global())


func _physics_process(delta: float) -> void:
	if _player == null:
		return
	global_position = _player.global_position
	_body.scale = Vector2(_player.facing * _squash.x, _squash.y)
	_scarf.step(_neck_global(), _player.velocity, delta)

	var running: bool = _player.state == &"run" and _player.on_floor
	if running and not _was_running:
		_run_dust.emitting = true
	elif not running and _was_running:
		_run_dust.emitting = false
	_was_running = running
	if running:
		_run_dust.position = Vector2(-_player.facing * 10.0, 0.0)
		_run_dust.direction = Vector2(-_player.facing, -0.3).normalized()

	if _player.state == &"dash":
		_spawn_afterimage()


func _neck_global() -> Vector2:
	return global_position + Vector2(_player.facing * _player.neck_offset.x, _player.neck_offset.y)


func _on_jumped(_kind: StringName) -> void:
	_jump_puff.restart()
	_jump_puff.emitting = true
	_pulse_squash(Vector2(0.75, 1.35), 0.03, 0.16)


func _on_landed(impact_speed: float) -> void:
	var impact_norm: float = clampf(absf(impact_speed) / REFERENCE_IMPACT, 0.0, 1.4)
	_landing_dust.scale_amount_min = 3.0 + impact_norm * 4.0
	_landing_dust.scale_amount_max = 6.0 + impact_norm * 6.0
	_landing_dust.amount = int(6 + impact_norm * 10)
	_landing_dust.restart()
	_landing_dust.emitting = true
	var stretch_x: float = 1.0 + impact_norm * 0.4
	var stretch_y: float = 1.0 - impact_norm * 0.45
	_pulse_squash(Vector2(stretch_x, stretch_y), 0.02, 0.2)


func _on_dash_started(dir: Vector2) -> void:
	_kill_squash_tween()
	var along: float = absf(dir.x) >= absf(dir.y)
	_squash = Vector2(1.6, 0.65) if along else Vector2(0.65, 1.6)


func _on_dash_ended() -> void:
	_pulse_squash(Vector2.ONE, 0.0, 0.14)


func _on_stomp_impact() -> void:
	_stomp_debris.position = Vector2.ZERO
	_stomp_debris.restart()
	_stomp_debris.emitting = true


func _on_blinked(from: Vector2, to: Vector2) -> void:
	_spawn_blink_trail(from, to)


func _on_resonance_changed(colors: Array) -> void:
	var c: StringName = colors[0] if colors.size() > 0 else &""
	_scarf.set_resonance_color(c)


func _on_respawned() -> void:
	_scarf.reset(_neck_global())
	_kill_squash_tween()
	_squash = Vector2.ONE


func _kill_squash_tween() -> void:
	if _squash_tween and _squash_tween.is_valid():
		_squash_tween.kill()


func _pulse_squash(target: Vector2, attack: float, release: float) -> void:
	_kill_squash_tween()
	_squash_tween = create_tween()
	if attack > 0.0:
		_squash_tween.tween_property(self, "_squash", target, attack).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	else:
		_squash = target
	_squash_tween.tween_property(self, "_squash", Vector2.ONE, release).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


func _make_particles(cfg: Dictionary) -> CPUParticles2D:
	var p := CPUParticles2D.new()
	p.amount = cfg.amount
	p.lifetime = cfg.lifetime
	p.one_shot = cfg.one_shot
	p.explosiveness = cfg.explosiveness
	p.emitting = false
	p.direction = cfg.direction
	p.spread = cfg.spread_deg
	p.initial_velocity_min = cfg.speed_min
	p.initial_velocity_max = cfg.speed_max
	p.gravity = cfg.gravity
	p.scale_amount_min = cfg.scale_min
	p.scale_amount_max = cfg.scale_max
	p.color = cfg.color
	add_child(p)
	return p


func _spawn_afterimage() -> void:
	if _rng.randf() > 0.6:
		return
	var ghost := _PlayerBody.new()
	ghost.box_size_px = _player.box_size_px
	ghost.modulate = Color(1, 1, 1, 0.35)
	ghost.scale = Vector2(_player.facing, 1.0)
	ghost.global_position = global_position
	get_parent().add_child(ghost)
	var tw := ghost.create_tween()
	tw.tween_property(ghost, "modulate:a", 0.0, 0.22)
	tw.tween_callback(ghost.queue_free)


func _spawn_blink_trail(from: Vector2, to: Vector2) -> void:
	var trail := _BlinkTrail.new()
	trail.from_point = from
	trail.to_point = to
	get_parent().add_child(trail)
	var tw := trail.create_tween()
	tw.tween_property(trail, "modulate:a", 0.0, 0.25)
	tw.tween_callback(trail.queue_free)


## The capsule body: a rounded-rect + two cap circles with a small face
## mark offset toward facing. `scale.x`'s sign carries the facing flip.
class _PlayerBody:
	extends Node2D

	var box_size_px: Vector2

	func _draw() -> void:
		var r: float = box_size_px.x * 0.5
		var straight: float = maxf(box_size_px.y - box_size_px.x, 0.0)
		var top_y: float = -box_size_px.y + r
		var bottom_y: float = -r
		draw_rect(Rect2(-r, top_y, box_size_px.x, straight), BODY_COLOR)
		draw_circle(Vector2(0, top_y), r, BODY_COLOR)
		draw_circle(Vector2(0, bottom_y), r, BODY_COLOR)
		draw_circle(Vector2(r * 0.4, top_y), r * 0.16, FACE_COLOR)

	func _ready() -> void:
		set_notify_transform(true)
		queue_redraw()


## A short ghost line between two points, drawn as a tapered capsule shape,
## used for the blink teleport trail.
class _BlinkTrail:
	extends Node2D

	var from_point: Vector2
	var to_point: Vector2

	func _draw() -> void:
		var local_to := to_point - from_point
		draw_line(Vector2.ZERO, local_to, Color(0.55, 0.75, 0.95, 0.6), 10.0, true)

	func _ready() -> void:
		position = from_point
		queue_redraw()
