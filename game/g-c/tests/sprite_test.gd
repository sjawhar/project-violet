extends Node
## THROWAWAY sprite reader tests. godot --headless --path game/g-c res://tests/sprite_test.tscn
## frames: the frame index at boundary times matches min(floor(t * n / duration), n - 1), wrapping a looping animation
## (idle) and holding a held one (jump) on its last frame.
## anchor: with the character under a Player2D, a grounded frame's body and scarf anchor pixels land exactly on the
## player's ground point, facing right and facing left, and facing left mirrors the layers about that point (catches a
## flipped y, a wrong offset sign, a missing mirror, and a flip_h mirror, which moves the anchor off the root).
## order: the scarf layer draws above the body layer.
## malformed: a wrong format, a wrong version and a missing image each make Sprites.from_data return null with a
## message naming the problem (and push_error it), never a partial set.
## Prints one line per failure and `sprite-test: N failure(s)`; exits 0 iff N == 0.
const SPRITES := "res://protagonist/sprites/violet.sprites.json"
var failures: PackedStringArray = []

func _ready() -> void:
	var sprites := Sprites.load_file(SPRITES)
	if sprites == null:
		failures.append("load: %s did not load: %s" % [SPRITES, Sprites.last_error])
	else:
		test_frames(sprites); test_anchor(sprites); test_order(sprites)
	test_malformed()
	for f in failures: printerr(f)
	print("sprite-test: %d failure(s)" % failures.size())
	get_tree().quit(0 if failures.is_empty() else 1)

func test_frames(sprites: Sprites) -> void:
	var idle := sprites.duration("idle"); var n_idle: int = (sprites.animations["idle"] as Sprites.Clip).frames.size()
	var jump := sprites.duration("jump"); var n_jump: int = (sprites.animations["jump"] as Sprites.Clip).frames.size()
	var step := idle / n_idle
	for case: Array in [[0.0, 0], [step - 1e-4, 0], [step, 1], [idle - 1e-4, n_idle - 1], [idle, 0], [idle + step, 1], [3.0 * idle + 2.5 * step, 2]]:
		_expect_frame(sprites, "idle", case[0], case[1])
	var jstep := jump / n_jump
	for case: Array in [[0.0, 0], [jstep - 1e-4, 0], [jstep, 1], [jump - 1e-4, n_jump - 1], [jump, n_jump - 1], [10.0 * jump, n_jump - 1]]:
		_expect_frame(sprites, "jump", case[0], case[1])

func _expect_frame(sprites: Sprites, anim_name: String, t: float, want: int) -> void:
	var got := sprites.frame_index(anim_name, t)
	if got != want: failures.append("frames: %s at t=%.4f is frame %d, the formula says %d" % [anim_name, t, got, want])

func test_anchor(sprites: Sprites) -> void:
	var player := Player2D.new(); player.position = Vector2(500, 300)
	add_child(player); player.set_physics_process(false)
	var character := SpriteCharacter2D.create(sprites)
	player.add_child(character); character.set_process(false)
	for facing: int in [1, -1]:
		for case: Array in [["idle", 0.0], ["land", sprites.duration("land")]]:
			character.show_frame(sprites.frame(case[0], case[1]), facing)
			for layer: Sprite2D in [character.body, character.scarf]:
				# the file's anchor pixel (from the image's top-left, y down), placed the way Sprite2D draws it: at
				# pixel + offset in the sprite's own space
				var frame_anchor: Vector2 = (sprites.frame(case[0], case[1])[String(layer.name).to_lower()] as Sprites.Layer).anchor
				var at := layer.get_global_transform() * (frame_anchor + layer.offset)
				# facing left mirrors about the root: a pixel to the right of the anchor in the image lands left of it
				var ahead := layer.get_global_transform() * (frame_anchor + Vector2(10, 0) + layer.offset)
				if signf(ahead.x - at.x) != float(facing):
					failures.append("anchor: %s facing %d: the %s layer is not mirrored to the facing" % [case[0], facing, layer.name])
				if at.distance_to(player.global_position) > 1e-3:
					failures.append("anchor: %s facing %d: the %s anchor pixel lands at %s, the ground point is %s" % [case[0], facing, layer.name, at, player.global_position])
	# the soles: the body image's lowest opaque row on a grounded frame sits at the anchor's row, within 2 image px
	var layer: Sprites.Layer = sprites.frame("idle", 0.0)["body"]
	var image := layer.texture.get_image(); if image.is_compressed(): image.decompress()
	var lowest := -1
	for y in range(image.get_height() - 1, -1, -1):
		for x in range(0, image.get_width(), 2):
			if image.get_pixel(x, y).a > 0.5: lowest = y; break
		if lowest >= 0: break
	if absf(lowest - layer.anchor.y) > 2.0: failures.append("anchor: idle frame 0's soles are at image row %d, its anchor at row %.1f" % [lowest, layer.anchor.y])
	player.queue_free()

func test_order(sprites: Sprites) -> void:
	var character := SpriteCharacter2D.create(sprites)
	if character.scarf.get_index() <= character.body.get_index() or character.scarf.z_index < character.body.z_index:
		failures.append("order: the scarf (index %d, z %d) does not draw above the body (index %d, z %d)" % [character.scarf.get_index(), character.scarf.z_index, character.body.get_index(), character.body.z_index])
	character.free()

func test_malformed() -> void:
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(SPRITES))
	var base := SPRITES.get_base_dir()
	var wrong_format := data.duplicate(true); wrong_format["format"] = "violet-rig"
	_refused("wrong format", wrong_format, "format is violet-rig")
	var wrong_version := data.duplicate(true); wrong_version["version"] = 2
	_refused("wrong version", wrong_version, "version is 2")
	var missing := data.duplicate(true); missing["animations"]["run"]["frames"][3]["scarf"]["image"] = "../glow-up/trial-b/frames/no-such-frame.png"
	_refused("missing image", missing, "no-such-frame.png does not exist")
	if Sprites.from_data(data.duplicate(true), base, "control") == null: failures.append("malformed: the unmodified file was refused: %s" % Sprites.last_error)

func _refused(what: String, data: Dictionary, want: String) -> void:
	Sprites.last_error = ""
	if Sprites.from_data(data, SPRITES.get_base_dir(), "malformed") != null: failures.append("malformed: %s loaded" % what)
	elif want not in Sprites.last_error: failures.append("malformed: %s: error %s, expected it to mention %s" % [what, Sprites.last_error, want])
