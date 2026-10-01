## THROWAWAY — verification-only, not part of the presentation contract.
## Dumps every synthesized Sfx sound to a real .wav file on disk (the exact
## baked PCM bytes `play()` uses), so an outside process (Python/ffprobe) can
## check durations and peak levels numerically. Run headless:
##   godot --headless --path prototypes/lab-presentation-sandbox res://verify/sfx_dump.tscn
extends Node


func _ready() -> void:
	var out_dir := "/tmp/pres-sfx-verify"
	DirAccess.make_dir_recursive_absolute(out_dir)
	for sound_name in Sfx.SOUND_NAMES:
		var stream: AudioStreamWAV = Sfx.get_stream(sound_name)
		var path := "%s/%s.wav" % [out_dir, sound_name]
		_write_wav(path, stream.data, stream.mix_rate, 1, 16)
		print("wrote %s (%d bytes)" % [path, stream.data.size()])
	print("DONE")
	get_tree().quit()


func _write_wav(path: String, pcm_bytes: PackedByteArray, mix_rate: int, channels: int, bits: int) -> void:
	var byte_rate: int = mix_rate * channels * bits / 8
	var block_align: int = channels * bits / 8
	var data_size: int = pcm_bytes.size()
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string("RIFF")
	f.store_32(36 + data_size)
	f.store_string("WAVE")
	f.store_string("fmt ")
	f.store_32(16)
	f.store_16(1)
	f.store_16(channels)
	f.store_32(mix_rate)
	f.store_32(byte_rate)
	f.store_16(block_align)
	f.store_16(bits)
	f.store_string("data")
	f.store_32(data_size)
	f.store_buffer(pcm_bytes)
	f.close()
