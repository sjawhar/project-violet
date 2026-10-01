## THROWAWAY — Violet mechanics lab, presentation component (autoload `Sfx`).
## Synthesizes every sound as an sfxr-style AudioStreamWAV at startup — square
## /saw/noise oscillators, pitch slides, short attack/decay envelopes — no
## audio files. Drop into `prototypes/mechanics-lab/lab/juice/sfx.gd`
## unchanged (and register it as the `Sfx` autoload in project.godot).
extends Node

const MIX_RATE := 44100
const PLAYER_POOL_SIZE := 8
const PITCH_JITTER := 0.04
const RNG_SEED := 20261004
const NORMALIZE_TARGET_DBFS := -6.0

const SOUND_NAMES: Array[StringName] = [
	&"jump", &"double_jump", &"land_soft", &"land_hard", &"dash",
	&"resonate_on", &"resonate_off", &"pass_through", &"death", &"goal",
	&"orb", &"stomp", &"blink", &"swing_attach", &"ui_move", &"ui_select",
]

var _streams: Dictionary = {}
var _players: Array[AudioStreamPlayer] = []
var _next_player_index := 0
var _muted := false
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	_rng.seed = RNG_SEED
	for sound_name in SOUND_NAMES:
		var samples: PackedFloat32Array = _generate(sound_name)
		_streams[sound_name] = _build_stream(_normalize(samples, NORMALIZE_TARGET_DBFS))
	for i in range(PLAYER_POOL_SIZE):
		var p := AudioStreamPlayer.new()
		add_child(p)
		_players.append(p)


func _unhandled_input(event: InputEvent) -> void:
	if InputMap.has_action(&"mute") and event.is_action_pressed(&"mute"):
		_muted = not _muted


func play(name: StringName, volume_db: float = 0.0) -> void:
	if _muted:
		return
	if not _streams.has(name):
		push_warning("Sfx.play: unknown sound '%s'" % name)
		return
	var player: AudioStreamPlayer = _players[_next_player_index]
	_next_player_index = (_next_player_index + 1) % _players.size()
	player.stream = _streams[name]
	player.volume_db = volume_db
	player.pitch_scale = 1.0 + _rng.randf_range(-PITCH_JITTER, PITCH_JITTER)
	player.play()


## Exposed for the throwaway audio-verification tool, not part of the
## presentation contract's required surface — returns the exact baked
## stream so a numeric dump matches what `play()` actually plays.
func get_stream(name: StringName) -> AudioStreamWAV:
	return _streams.get(name)


func _generate(name: StringName) -> PackedFloat32Array:
	match name:
		&"jump":
			return _tone(0.12, 300.0, 650.0, &"square", 0.005, 2.0, 0.6)
		&"double_jump":
			var base := _tone(0.14, 420.0, 820.0, &"square", 0.004, 2.0, 0.55)
			var shimmer := _tone(0.1, 900.0, 1300.0, &"sine", 0.01, 3.0, 0.25)
			return _mix(base, shimmer)
		&"land_soft":
			return _mix(
				_tone(0.12, 180.0, 90.0, &"sine", 0.002, 2.0, 0.5),
				_noise_burst(0.08, 0.002, 3.0, 0.25)
			)
		&"land_hard":
			return _mix(
				_tone(0.22, 140.0, 55.0, &"sine", 0.002, 1.6, 0.75),
				_noise_burst(0.15, 0.002, 2.2, 0.45)
			)
		&"dash":
			return _mix(
				_noise_burst(0.16, 0.01, 1.8, 0.5),
				_tone(0.16, 900.0, 300.0, &"saw", 0.01, 1.5, 0.25)
			)
		&"resonate_on":
			return _mix(
				_tone(0.3, 440.0, 880.0, &"sine", 0.02, 1.2, 0.5),
				_tone(0.3, 660.0, 1320.0, &"sine", 0.02, 1.2, 0.25)
			)
		&"resonate_off":
			return _mix(
				_tone(0.3, 880.0, 440.0, &"sine", 0.02, 1.2, 0.5),
				_tone(0.3, 1320.0, 660.0, &"sine", 0.02, 1.2, 0.25)
			)
		&"pass_through":
			return _mix(
				_noise_burst(0.2, 0.02, 1.5, 0.3),
				_tone(0.2, 500.0, 1000.0, &"sine", 0.02, 1.3, 0.3)
			)
		&"death":
			return _mix(
				_tone(0.35, 380.0, 160.0, &"sine", 0.01, 1.3, 0.5),
				_tone(0.35, 390.0, 165.0, &"saw", 0.01, 1.3, 0.12)
			)
		&"goal":
			return _concat([
				_tone(0.11, 523.0, 523.0, &"sine", 0.005, 2.5, 0.45),
				_silence(0.02),
				_tone(0.11, 659.0, 659.0, &"sine", 0.005, 2.5, 0.45),
				_silence(0.02),
				_tone(0.16, 784.0, 784.0, &"sine", 0.005, 2.0, 0.5),
			])
		&"orb":
			return _tone(0.18, 700.0, 1100.0, &"sine", 0.005, 2.0, 0.45)
		&"stomp":
			return _mix(
				_tone(0.18, 120.0, 45.0, &"sine", 0.001, 1.4, 0.8),
				_noise_burst(0.12, 0.001, 2.0, 0.55)
			)
		&"blink":
			return _mix(
				_noise_burst(0.08, 0.002, 2.0, 0.35),
				_tone(0.12, 600.0, 1400.0, &"sine", 0.005, 1.8, 0.4)
			)
		&"swing_attach":
			return _mix(
				_tone(0.1, 500.0, 350.0, &"square", 0.002, 2.0, 0.45),
				_noise_burst(0.04, 0.001, 3.0, 0.2)
			)
		&"ui_move":
			return _tone(0.04, 700.0, 700.0, &"sine", 0.002, 2.0, 0.3)
		&"ui_select":
			return _concat([
				_tone(0.05, 600.0, 600.0, &"sine", 0.002, 2.0, 0.35),
				_silence(0.01),
				_tone(0.08, 900.0, 900.0, &"sine", 0.002, 2.0, 0.4),
			])
	push_error("Sfx: no generator for '%s'" % name)
	return PackedFloat32Array()


## A tone with a linear pitch slide from `f0` to `f1` Hz over `duration`
## seconds, `osc` in {square, saw, sine}, attack/decay envelope.
func _tone(duration: float, f0: float, f1: float, osc: StringName, attack: float, decay_power: float, amp: float) -> PackedFloat32Array:
	var n := maxi(int(duration * MIX_RATE), 1)
	var samples := PackedFloat32Array()
	samples.resize(n)
	var phase := 0.0
	for i in range(n):
		var t: float = float(i) / MIX_RATE
		var freq: float = lerpf(f0, f1, t / duration)
		phase += TAU * freq / MIX_RATE
		var s: float = _oscillate(osc, phase)
		samples[i] = s * _envelope(t, duration, attack, decay_power) * amp
	return samples


func _oscillate(osc: StringName, phase: float) -> float:
	match osc:
		&"square":
			return 1.0 if sin(phase) >= 0.0 else -1.0
		&"saw":
			var x: float = fposmod(phase, TAU) / TAU
			return 2.0 * x - 1.0
		_:
			return sin(phase)


func _noise_burst(duration: float, attack: float, decay_power: float, amp: float) -> PackedFloat32Array:
	var n := maxi(int(duration * MIX_RATE), 1)
	var samples := PackedFloat32Array()
	samples.resize(n)
	for i in range(n):
		var t: float = float(i) / MIX_RATE
		samples[i] = _rng.randf_range(-1.0, 1.0) * _envelope(t, duration, attack, decay_power) * amp
	return samples


func _envelope(t: float, duration: float, attack: float, decay_power: float) -> float:
	if attack > 0.0 and t < attack:
		return t / attack
	var decay_t: float = (t - attack) / maxf(duration - attack, 0.0001)
	return pow(clampf(1.0 - decay_t, 0.0, 1.0), decay_power)


func _mix(a: PackedFloat32Array, b: PackedFloat32Array) -> PackedFloat32Array:
	var n := maxi(a.size(), b.size())
	var out := PackedFloat32Array()
	out.resize(n)
	for i in range(n):
		var av: float = a[i] if i < a.size() else 0.0
		var bv: float = b[i] if i < b.size() else 0.0
		out[i] = av + bv
	return out


func _concat(parts: Array) -> PackedFloat32Array:
	var total := 0
	for p in parts:
		total += p.size()
	var out := PackedFloat32Array()
	out.resize(total)
	var offset := 0
	for p in parts:
		for i in range(p.size()):
			out[offset + i] = p[i]
		offset += p.size()
	return out


func _silence(duration: float) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	out.resize(maxi(int(duration * MIX_RATE), 0))
	return out


func _normalize(samples: PackedFloat32Array, target_dbfs: float) -> PackedFloat32Array:
	var peak := 0.0
	for s in samples:
		peak = maxf(peak, absf(s))
	if peak < 0.0001:
		return samples
	var target_amp: float = pow(10.0, target_dbfs / 20.0)
	var gain: float = target_amp / peak
	var out := PackedFloat32Array()
	out.resize(samples.size())
	for i in range(samples.size()):
		out[i] = samples[i] * gain
	return out


func _build_stream(samples: PackedFloat32Array) -> AudioStreamWAV:
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = MIX_RATE
	stream.stereo = false
	var bytes := PackedByteArray()
	bytes.resize(samples.size() * 2)
	for i in range(samples.size()):
		var v: int = int(clampf(samples[i], -1.0, 1.0) * 32767.0)
		bytes.encode_s16(i * 2, v)
	stream.data = bytes
	return stream
