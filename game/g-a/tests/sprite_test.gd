extends Node
## THROWAWAY violet-sprites reader tests. godot --headless --path game/g-a res://tests/sprite_test.tscn
## Against the lane's real file (res://protagonist/sprites/violet.sprites.json):
## timing: the frame showing at boundary times for looping run and idle and held jump, by character-rig.md's formula
## (including its worked examples: idle 0.35 s and 1.35 s show frame 2, jump 0.3 s frame 3, jump 0.8 s holds frame 4);
## anchor: with the character at (400, 300), each layer's anchor pixel lands exactly on that ground point, facing
## right and left, for a grounded and an airborne frame, and idle frame 0's corners land where the doc's example puts
## them; draw order: the scarf draws over the body;
## malformed: a wrong format, a wrong version and a missing image each make the reader return null with an error
## naming the problem, and the game run on a malformed file exits 1 (a second process, so the quit is real).
## Prints one line per failure and `sprite-test: N failure(s)`; exits 0 iff N == 0.
const FILE := "res://protagonist/sprites/violet.sprites.json"
var failures: Array[String] = []

func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--exit-probe="):  # the second process: run the game's own attach on a malformed file
			GreyboxArt.attach_sprites(self, arg.trim_prefix("--exit-probe="))
			return
	var sprites := VioletSprites.load_file(FILE)
	if sprites == null: failures.append("%s did not load: %s" % [FILE, VioletSprites.last_error])
	else:
		_timing(sprites); _anchor(sprites); _draw_order(sprites)
	_malformed()
	for f in failures: print(f)
	print("sprite-test: %d failure(s)" % failures.size())
	get_tree().quit(0 if failures.is_empty() else 1)

func _timing(sprites: VioletSprites) -> void:
	for case: Array in [
		["idle", 0.0, 0], ["idle", 0.35, 2], ["idle", 1.35, 2], ["idle", 0.9999, 7], ["idle", 1.0, 0],
		["run", 0.0749, 0], ["run", 0.075, 1], ["run", 0.5999, 7], ["run", 0.6, 0], ["run", 0.675, 1],
		["jump", 0.0, 0], ["jump", 0.3, 3], ["jump", 0.4999, 4], ["jump", 0.5, 4], ["jump", 0.8, 4], ["jump", 10.0, 4],
	]:
		var got := sprites.frame_index(case[0], case[1])
		if got != case[2]: failures.append("timing: %s at %.4f s shows frame %d, expected %d" % [case[0], case[1], got, case[2]])

## Where image pixel P of SPRITE lands on the canvas: the character's transform, then the sprite's, with an
## uncentered Sprite2D drawing pixel P at offset + P.
static func _canvas(character: SpriteCharacter2D, sprite: Sprite2D, p: Vector2) -> Vector2:
	return character.transform * (sprite.transform * (sprite.offset + p))

func _anchor(sprites: VioletSprites) -> void:
	var character := SpriteCharacter2D.create(sprites)
	character.position = Vector2(400, 300)
	for case: Array in [["idle", 0.0], ["jump", 0.0], ["run", 0.3]]:
		var frame := sprites.frame(case[0], case[1])
		for facing in [1, -1]:
			character.show_frame(frame, facing)
			for pair: Array in [[character.body, frame.body, "body"], [character.scarf, frame.scarf, "scarf"]]:
				var at := _canvas(character, pair[0], (pair[1] as VioletSprites.Layer).anchor)
				if at.distance_to(character.position) > 1e-3:
					failures.append("anchor: %s %s facing %d: its anchor lands at %s, not the ground point %s" % [case[0], pair[2], facing, at, character.position])
	# character-rig.md's worked example: idle frame 0 at (400, 300), scale 1.6 * 64 / 1072.
	character.show_frame(sprites.frame("idle", 0.0), 1)
	for pair: Array in [[character.body, Vector2(380.45, 195.50), "body"], [character.scarf, Vector2(390.72, 213.80), "scarf"]]:
		var corner := _canvas(character, pair[0], Vector2.ZERO)
		if corner.distance_to(pair[1]) > 0.01: failures.append("anchor: idle frame 0's %s top-left lands at %s, the doc says %s" % [pair[2], corner, pair[1]])
	character.show_frame(sprites.frame("idle", 0.0), -1)
	var mirrored := _canvas(character, character.body, Vector2.ZERO)
	if mirrored.distance_to(Vector2(419.55, 195.50)) > 0.01: failures.append("anchor: facing left, idle frame 0's body top-left lands at %s, not mirrored to (419.55, 195.50)" % mirrored)
	character.free()

func _draw_order(sprites: VioletSprites) -> void:
	var character := SpriteCharacter2D.create(sprites)
	var body := character.body; var scarf := character.scarf
	if body.get_parent() != character or scarf.get_parent() != character: failures.append("draw order: the layers are not both children of the character")
	elif not (scarf.get_index() > body.get_index() and scarf.z_index == body.z_index and not scarf.show_behind_parent):
		failures.append("draw order: the scarf (child %d, z %d) does not draw over the body (child %d, z %d)" % [scarf.get_index(), scarf.z_index, body.get_index(), body.z_index])
	character.free()

func _malformed() -> void:
	var real: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FILE))
	var wrong_format := real.duplicate(true); wrong_format["format"] = "violet-sprite"
	var wrong_version := real.duplicate(true); wrong_version["version"] = 2
	var missing_image := real.duplicate(true); missing_image["animations"]["land"]["frames"][3]["scarf"]["image"] = "../glow-up/trial-b/frames/land-scarf-03-missing.png"
	for case: Array in [[wrong_format, "format is violet-sprite"], [wrong_version, "version is 2"], [missing_image, "land-scarf-03-missing.png does not exist"]]:
		VioletSprites.last_error = ""
		var sprites := VioletSprites.from_data(case[0], FILE.get_base_dir(), "malformed")
		if sprites != null: failures.append("malformed: a file with %s loaded" % case[1])
		elif case[1] not in VioletSprites.last_error: failures.append("malformed: error %s does not name %s" % [VioletSprites.last_error, case[1]])
	# The game itself on a malformed file: push_error, then exit 1, never the STAND-IN or a silent fallback.
	var bad := ProjectSettings.globalize_path("user://wrong-version.sprites.json")
	FileAccess.open(bad, FileAccess.WRITE).store_string(JSON.stringify(wrong_version))
	var output := []
	var code := OS.execute(OS.get_executable_path(), ["--headless", "--path", ProjectSettings.globalize_path("res://"),
		"res://tests/sprite_test.tscn", "--", "--exit-probe=" + bad], output, true)
	if code != 1: failures.append("malformed: the game on %s exited %d, not 1" % [bad, code])
	elif "version is 2" not in output[0]: failures.append("malformed: the game on %s exited 1 without naming the version:\n%s" % [bad, output[0]])
