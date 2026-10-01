# THROWAWAY (lab-export-probe). Hello-world scene for proving the export + publish pipeline:
# a moving square, a CPUParticles2D trail, a Label, keyboard + gamepad input (Godot's built-in
# ui_left/right/up/down actions already bind both; "play_tone" is a custom action declared in
# project.godot for Space + gamepad button A, since ui_accept has no gamepad binding by default),
# and an AudioStreamWAV synthesized at runtime and played on a key/button press.
extends Node2D

const SPEED_PX_S := 220.0
const SQUARE_SIZE := 32

@onready var square: Sprite2D = $Square
@onready var particles: CPUParticles2D = $Particles
@onready var label: Label = $CanvasLayer/PositionLabel
@onready var sfx: AudioStreamPlayer2D = $Sfx

func _ready() -> void:
	var image := Image.create(SQUARE_SIZE, SQUARE_SIZE, false, Image.FORMAT_RGBA8)
	image.fill(Color(0.90, 0.33, 0.25))
	square.texture = ImageTexture.create_from_image(image)
	square.position = Vector2(480, 270)
	sfx.stream = _make_beep()
	particles.emitting = false
	_update_label()

func _physics_process(delta: float) -> void:
	var dir := Vector2(
		Input.get_action_strength("ui_right") - Input.get_action_strength("ui_left"),
		Input.get_action_strength("ui_down") - Input.get_action_strength("ui_up")
	)
	var moving := dir.length_squared() > 0.0
	if moving:
		square.position += dir.normalized() * SPEED_PX_S * delta
		particles.position = square.position
	particles.emitting = moving
	_update_label()
	if Input.is_action_just_pressed("play_tone"):
		sfx.play()

func _update_label() -> void:
	label.text = "pos: (%.1f, %.1f)\nFPS: %d\nspace/A: play tone" % [
		square.position.x, square.position.y, Engine.get_frames_per_second()
	]

# A quarter-second 440 Hz sine tone, built at runtime so the probe ships no audio assets.
func _make_beep() -> AudioStreamWAV:
	var mix_rate := 22050
	var duration_s := 0.25
	var freq_hz := 440.0
	var frame_count := int(mix_rate * duration_s)
	var data := PackedByteArray()
	data.resize(frame_count * 2)
	for i in range(frame_count):
		var t := float(i) / mix_rate
		var sample := sin(TAU * freq_hz * t)
		var value := int(clamp(sample, -1.0, 1.0) * 32767.0)
		data.encode_s16(i * 2, value)
	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_16_BITS
	wav.mix_rate = mix_rate
	wav.stereo = false
	wav.data = data
	return wav
