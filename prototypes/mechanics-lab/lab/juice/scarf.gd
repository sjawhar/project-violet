## THROWAWAY — Violet mechanics lab, presentation component.
## A verlet chain trailing from the neck: flutters, avoids folding back
## through the body, tapers from neck to tip, and smoothly crossfades to
## the resonating color (neutral when none). This is the character's
## identity and a known weak point in the art track ("looks bolted onto
## her face") — it must read as attached at the neck and flow naturally.
## Drop into `prototypes/mechanics-lab/lab/juice/scarf.gd` unchanged.
class_name Scarf
extends Node2D

const SEGMENT_COUNT := 6
const SEGMENT_LEN := 16.0
const NECK_HALF_WIDTH := 9.0
const TIP_HALF_WIDTH := 1.5
const GRAVITY := Vector2(0, 220.0)
const DAMPING := 0.96
const TRAIL_STRENGTH := 0.35
const FLUTTER_AMPLITUDE := 26.0
const FLUTTER_FREQ := 7.0
const RELAX_ITERATIONS := 4
const COLOR_LERP_SPEED := 6.0
const RNG_SEED := 20261002

const NEUTRAL := Color8(0x9A, 0xA0, 0xA6)
const PALETTE := {
	&"red": Color8(0xE5, 0x55, 0x3F),
	&"green": Color8(0x4C, 0xC2, 0x7A),
	&"yellow": Color8(0xF2, 0xC9, 0x4C),
	&"blue": Color8(0x4A, 0x90, 0xE2),
}

var _points: PackedVector2Array
var _prev_points: PackedVector2Array
var _time := 0.0
var _rng := RandomNumberGenerator.new()
var _phase_offsets: PackedFloat32Array
var _current_color: Color = NEUTRAL
var _target_color: Color = NEUTRAL


func _ready() -> void:
	_rng.seed = RNG_SEED
	_phase_offsets = PackedFloat32Array()
	for i in range(SEGMENT_COUNT + 1):
		_phase_offsets.append(_rng.randf_range(0.0, TAU))
	reset(Vector2.ZERO)


## Collapses the whole chain onto `anchor` (no popping on (re)spawn/teleport).
func reset(anchor: Vector2) -> void:
	_points = PackedVector2Array()
	_prev_points = PackedVector2Array()
	for i in range(SEGMENT_COUNT + 1):
		_points.append(anchor)
		_prev_points.append(anchor)
	queue_redraw()


## Advances the simulation one frame: `anchor` is the neck's current global
## position, `velocity` the player's velocity (px/s), used so the tail
## trails behind motion instead of swinging independently of it.
func step(anchor: Vector2, velocity: Vector2, delta: float) -> void:
	if delta <= 0.0:
		return
	_time += delta
	_points[0] = anchor
	var trail: Vector2 = -velocity * TRAIL_STRENGTH * delta

	for i in range(1, SEGMENT_COUNT + 1):
		var current: Vector2 = _points[i]
		var vel_est: Vector2 = (current - _prev_points[i]) * DAMPING
		var flutter: Vector2 = Vector2(
			sin(_time * FLUTTER_FREQ + _phase_offsets[i]),
			cos(_time * FLUTTER_FREQ * 0.6 + _phase_offsets[i])
		) * FLUTTER_AMPLITUDE * delta * delta
		_prev_points[i] = current
		_points[i] = current + vel_est + GRAVITY * delta * delta + trail + flutter

	for _iter in range(RELAX_ITERATIONS):
		_points[0] = anchor
		for i in range(1, SEGMENT_COUNT + 1):
			var diff: Vector2 = _points[i] - _points[i - 1]
			var dist: float = diff.length()
			if dist > 0.0001:
				_points[i] = _points[i - 1] + diff * (SEGMENT_LEN / dist)
			else:
				_points[i] = _points[i - 1] + Vector2(0, SEGMENT_LEN)
		# Keep the chain from folding back through the body: each link stays
		# at least its own arc-length from the neck, which a near-straight
		# chain already satisfies, but a sharp fold could violate — push
		# back out along the current direction from the anchor when it does.
		for i in range(2, SEGMENT_COUNT + 1):
			var min_radius: float = float(i) * SEGMENT_LEN * 0.82
			var from_anchor: Vector2 = _points[i] - anchor
			var radius: float = from_anchor.length()
			if radius < min_radius and radius > 0.0001:
				_points[i] = anchor + from_anchor * (min_radius / radius)

	_current_color = _current_color.lerp(_target_color, clampf(delta * COLOR_LERP_SPEED, 0.0, 1.0))
	queue_redraw()


## `c` is a resonance color key (`&"red"`/`&"green"`/`&"yellow"`/`&"blue"`),
## or empty/null for no resonance (neutral gray).
func set_resonance_color(c) -> void:
	_target_color = PALETTE.get(c, NEUTRAL)


func _draw() -> void:
	if _points.size() < 2:
		return
	var left := PackedVector2Array()
	var right := PackedVector2Array()
	for i in range(_points.size()):
		var t: float = float(i) / float(_points.size() - 1)
		var half_width: float = lerpf(NECK_HALF_WIDTH, TIP_HALF_WIDTH, t)
		var tangent: Vector2
		if i == 0:
			tangent = (_points[1] - _points[0])
		elif i == _points.size() - 1:
			tangent = (_points[i] - _points[i - 1])
		else:
			tangent = (_points[i + 1] - _points[i - 1])
		if tangent.length() < 0.001:
			tangent = Vector2.DOWN
		var normal: Vector2 = tangent.normalized().orthogonal()
		var local: Vector2 = _points[i] - global_position
		left.append(local + normal * half_width)
		right.append(local - normal * half_width)
	var polygon := PackedVector2Array()
	polygon.append_array(left)
	right.reverse()
	polygon.append_array(right)
	draw_colored_polygon(polygon, _current_color)
