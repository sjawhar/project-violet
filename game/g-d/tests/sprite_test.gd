extends Node3D
## THROWAWAY: tests for the violet-sprites reader and SpriteCharacter3D. godot --headless --path game/g-d res://tests/sprite_test.tscn
## Prints each failure and `sprite-test: N failure(s)`; exits 0 iff N == 0. The malformed-file checks expect the reader's
## push_errors in the log.
const SPRITES := GreyboxArt3D.SPRITES_PATH
const EPS := 1e-4
var failures: PackedStringArray = []

func _ready() -> void:
	var sprites := Sprites.load_file(SPRITES)
	if sprites == null:
		_fail("%s did not load" % SPRITES)
	else:
		test_frame_index(sprites, "idle", true)
		test_frame_index(sprites, "land", false)
		# character-rig.md's worked example: idle at 0.35 s and 1.35 s shows frame 2; jump at 0.8 s holds frame 4; jump
		# at 0.3 s, exactly on a boundary, shows frame 3.
		for c in [["idle", 0.35, 2], ["idle", 1.35, 2], ["jump", 0.8, 4], ["jump", 0.3, 3]]:
			if sprites.frame_index(c[0], c[1]) != c[2]: _fail("%s at t=%s: frame %d, expected %d" % [c[0], c[1], sprites.frame_index(c[0], c[1]), c[2]])
		await test_anchors(sprites)
		test_scarf_over_body(sprites)
	test_malformed()
	for f in failures: printerr("FAIL: " + f)
	print("sprite-test: %d failure(s)" % failures.size())
	get_tree().quit(0 if failures.is_empty() else 1)

func _fail(message: String) -> void:
	failures.append(message)

## The frame at boundary times, against the format's formula written out here: min(floor(t * n / d), n - 1), t wrapped
## for a looping animation.
func test_frame_index(sprites: Sprites, anim: String, loop: bool) -> void:
	var clip: Sprites.Clip = sprites.clips[anim]
	if clip.loop != loop: _fail("%s: loop is %s, expected %s" % [anim, clip.loop, loop]); return
	var n := clip.frames.size(); var d := clip.duration; var step := d / n
	var cases := {0.0: 0, step - EPS: 0, step: 1, 2.5 * step: 2, d - EPS: n - 1}
	if loop:
		cases[d] = 0; cases[d + step] = 1; cases[3.0 * d + 2.5 * step] = 2
	else:
		cases[d] = n - 1; cases[10.0 * d] = n - 1
	for t: float in cases:
		var got := sprites.frame_index(anim, t)
		if got != cases[t]: _fail("%s at t=%f: frame %d, expected %d" % [anim, t, got, cases[t]])

## Each layer's anchor pixel lands on the player's ground point (the character root), facing right and left. The pixel
## is located from the sprite's own drawn bounds (Sprite3D.get_aabb()), not from SpriteCharacter3D's formula, so a
## flipped y or a wrong sign shows. A Sprite3D rebuilds its geometry deferred, so each check waits a frame.
func test_anchors(sprites: Sprites) -> void:
	for facing in [1, -1]:
		var player := Player3D.new(); player.facing = facing; add_child(player)
		var character := SpriteCharacter3D.create(sprites); player.add_child(character)
		for anim in ["idle", "land", "run"]:
			character.animator.animation = anim; character.animator.time = 0.0; character._apply()
			character.set_process(false)
			await get_tree().process_frame
			var frame := sprites.frame(anim, 0.0)
			for pair in [[character.body, frame.body], [character.scarf, frame.scarf]]:
				var sprite: Sprite3D = pair[0]; var layer: Sprites.Layer = pair[1]
				var box := sprite.get_aabb(); var px := sprite.pixel_size
				var x := box.end.x - layer.anchor.x * px if sprite.flip_h else box.position.x + layer.anchor.x * px
				var y := box.end.y - layer.anchor.y * px
				var at := Vector2(sprite.position.x + x, sprite.position.y + y)
				if at.length() > EPS: _fail("%s %s facing %d: anchor lands at %s, not on the root" % [anim, sprite.name, facing, at])
		player.queue_free()

func test_scarf_over_body(sprites: Sprites) -> void:
	var player := Player3D.new(); add_child(player)
	var character := SpriteCharacter3D.create(sprites); player.add_child(character)
	if not (character.scarf.render_priority > character.body.render_priority and character.scarf.position.z > character.body.position.z):
		_fail("the scarf is not drawn over the body (priority %d vs %d, z %f vs %f)" % [character.scarf.render_priority, character.body.render_priority, character.scarf.position.z, character.body.position.z])
	player.queue_free()

## Malformed files are refused with a push_error, and a game given one exits non-zero (a child Godot runs
## tests/sprite_attach.tscn, which attaches the character the way the game does).
func test_malformed() -> void:
	var good := FileAccess.get_file_as_string(SPRITES)
	var data: Dictionary = JSON.parse_string(good)
	var cases := {}
	var wrong_format := data.duplicate(true); wrong_format["format"] = "violet-rig"; cases["wrong format"] = wrong_format
	var wrong_version := data.duplicate(true); wrong_version["version"] = 2; cases["wrong version"] = wrong_version
	var wrong_units := data.duplicate(true); wrong_units["units"] = "m"; cases["wrong units"] = wrong_units
	var missing := data.duplicate(true); missing["animations"]["idle"]["frames"][0]["body"]["image"] = "../glow-up/trial-b/frames/no-such-frame.png"
	cases["missing image"] = missing
	var no_anim := data.duplicate(true); no_anim["animations"].erase("land"); cases["missing animation"] = no_anim
	for label: String in cases:
		# Written beside the real file, so the relative image paths still resolve.
		var path := SPRITES.get_base_dir().path_join("zz-test-%s.sprites.json" % label.replace(" ", "-"))
		var f := FileAccess.open(path, FileAccess.WRITE); f.store_string(JSON.stringify(cases[label])); f.close()
		var sprites := Sprites.load_file(path)
		if label == "missing animation":
			if sprites == null: _fail("%s: the reader refused a file the format allows" % label)
			elif SpriteCharacter3D.create(sprites) != null: _fail("%s: a character was made without land" % label)
		elif sprites != null: _fail("%s: the reader accepted it" % label)
		var code := _attach_exit_code(path)
		if code == 0: _fail("%s: the game exited 0 instead of failing" % label)
		DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	if _attach_exit_code(SPRITES) != 0: _fail("the real sprites: the attach child did not exit 0")

func _attach_exit_code(path: String) -> int:
	var output := []
	return OS.execute(OS.get_executable_path(), ["--headless", "--path", ProjectSettings.globalize_path("res://"),
		"res://tests/sprite_attach.tscn", "--", "--sprites=" + path], output, true)
