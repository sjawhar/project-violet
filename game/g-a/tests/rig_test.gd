extends Node
## THROWAWAY rig reader tests. godot --headless --path game/g-a res://tests/rig_test.tscn
## fk: a two-bone chain with known rotations puts the slot where a hand calculation does.
## interpolation: a rotate key halfway between 0 and 90 gives 45; idle wraps over its duration; jump plays once and
## holds its last frame; outside the keys the first or last key holds.
## round-trip: tests/rig/placeholder.rig.json (spinerig generate's own output) loads, poses every animation, and its
## setup pose's height matches the meta's height_px within a pixel.
## reference: every slot's placement in every frame `spinerig render` draws for that rig
## (tests/rig/placeholder.reference.json, from render.py's own code) matches Rig.pose.
## malformed: the fixture with one slot naming an unknown bone makes Rig.load_file return null, naming the file and
## the slot (the load's push_error prints it to stderr too).
## refusals: an attachment without a path, a skeleton.spine that isn't 4.3.x, a slot with no attachment, and a meta
## facing left each make Rig.from_data return null with a message naming the offender.
## Regenerate the fixture with tests/rig/make-fixture.sh.
## Prints one line per failure and `rig-test: N failure(s)`; exits 0 iff N == 0.
const FIXTURE := "res://tests/rig/placeholder.rig.json"
const REFERENCE := "res://tests/rig/placeholder.reference.json"
var failures: PackedStringArray = []

func _ready() -> void:
	test_fk(); test_interpolation(); test_round_trip(); test_reference(); test_malformed(); test_refusals()
	for f in failures: printerr(f)
	print("rig-test: %d failure(s)" % failures.size())
	get_tree().quit(0 if failures.is_empty() else 1)

## Root bone at (10, 20) rotated 30 degrees; child 100 along it rotated 60 more; the slot's attachment 10 along the
## child. By hand: child origin = (10 + 100 cos 30, 20 + 100 sin 30) = (96.6025, 70), child angle 90, so the
## attachment centre = (96.6025, 70 + 10) and the slot's angle is 90 + 15 (the attachment's own rotation) = 105.
func test_fk() -> void:
	var rig := Rig.from_data(_skeleton([
		{"name": "root", "x": 10, "y": 20, "rotation": 30},
		{"name": "child", "parent": "root", "x": 100, "rotation": 60},
	], {"x": 10, "y": 0, "rotation": 15}), _meta(), "res://", "fk")
	var t: Transform2D = rig.pose("", 0.0)["part"]
	_near("fk position.x", t.origin.x, 96.6025)
	_near("fk position.y", t.origin.y, 80.0)
	_near("fk rotation", rad_to_deg(t.get_rotation()), 105.0)
	_near("fk scale", t.get_scale().x, 1.0)

## One bone at the origin, keyed 0 at t=0 and 90 at t=1 in idle (loops) and jump (plays once); the slot sits 10 along it.
func test_interpolation() -> void:
	var spine := _skeleton([{"name": "root"}], {"x": 10, "y": 0})
	var turn := {"bones": {"root": {"rotate": [{"time": 0, "value": 0}, {"time": 1, "value": 90}]}}}
	spine["animations"] = {"idle": turn, "jump": turn}
	var rig := Rig.from_data(spine, _meta(), "res://", "interpolation")
	_near("duration", rig.duration("idle"), 1.0)
	_near("halfway", _angle(rig.pose("idle", 0.5)), 45.0)
	var halfway: Transform2D = rig.pose("idle", 0.5)["part"]
	_near("halfway position.x", halfway.origin.x, 10.0 * cos(PI / 4.0))
	_near("halfway position.y", halfway.origin.y, 10.0 * sin(PI / 4.0))
	_near("idle wraps 1.5 to 0.5", _angle(rig.pose("idle", 1.5)), 45.0)
	_near("idle wraps 2.25 to 0.25", _angle(rig.pose("idle", 2.25)), 22.5)
	_near("idle at t = duration wraps to the first key", _angle(rig.pose("idle", 1.0)), 0.0)
	_near("jump halfway", _angle(rig.pose("jump", 0.5)), 45.0)
	_near("jump at t = duration holds the last key", _angle(rig.pose("jump", 1.0)), 90.0)
	_near("jump after its end holds the last key", _angle(rig.pose("jump", 2.25)), 90.0)
	spine["animations"] = {"idle": {"bones": {"root": {"rotate": [{"time": 0.5, "value": 30}, {"time": 1, "value": 90}]}}}}
	rig = Rig.from_data(spine, _meta(), "res://", "interpolation")
	_near("before the first key, the first key holds", _angle(rig.pose("idle", 0.25)), 30.0)

func test_round_trip() -> void:
	var rig := Rig.load_file(FIXTURE)
	if rig == null: failures.append("round-trip: %s did not load" % FIXTURE); return
	if rig.slots.size() != 14: failures.append("round-trip: %d slots, expected the 14 parts" % rig.slots.size())
	for anim_name: String in RigAnimator.ANIMATIONS:
		if not rig.has_animation(anim_name): failures.append("round-trip: no %s animation" % anim_name); continue
		for step in 9:
			var pose := rig.pose(anim_name, rig.duration(anim_name) * step / 6.0)
			for slot in rig.slots:
				var t: Variant = pose.get(slot.name)
				if not (t is Transform2D and t.origin.is_finite() and is_finite(t.get_rotation())):
					failures.append("round-trip: %s at step %d: slot %s has no finite transform" % [anim_name, step, slot.name])
	var box := rig.bounds(rig.pose("", 0.0))
	if absf(box.size.y - rig.height_px) > 1.0:
		failures.append("round-trip: setup pose is %.3f px tall, meta height_px is %.3f" % [box.size.y, rig.height_px])
	if not rig.slots[0].image.begins_with("res://tests/rig/parts/"):
		failures.append("round-trip: slot image %s is not under skeleton.images" % rig.slots[0].image)

func test_reference() -> void:
	var rig := Rig.load_file(FIXTURE)
	var reference: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(REFERENCE))
	var fps: float = reference["fps"]
	var names: Array = rig.slots.map(func(slot: Rig.Slot) -> String: return slot.name)
	if names != reference["slots"]: failures.append("reference: slot order %s, spinerig render draws %s" % [names, reference["slots"]]); return
	var worst := 0.0
	for anim_name: String in reference["animations"]:
		var frames: Array = reference["animations"][anim_name]
		if frames.size() != maxi(1, roundi(rig.duration(anim_name) * fps)):
			failures.append("reference: %s has %d frames at %d fps, spinerig render draws %d" % [anim_name, roundi(rig.duration(anim_name) * fps), fps, frames.size()])
		for i in frames.size():
			var pose := rig.pose(anim_name, i / fps)
			for s in names.size():
				var want: Array = frames[i][s]
				var t: Transform2D = pose[names[s]]
				var off := maxf(t.origin.distance_to(Vector2(want[0], want[1])), absf(wrapf(rad_to_deg(t.get_rotation()) - want[2], -180.0, 180.0)))
				worst = maxf(worst, off)
				if off > 1e-3: failures.append("reference: %s frame %d slot %s: %s %.3f deg, spinerig render %s" % [anim_name, i, names[s], t.origin, rad_to_deg(t.get_rotation()), want])
	print("reference: worst difference from spinerig render %.6f (px or degrees)" % worst)

func test_malformed() -> void:
	var path := "user://malformed.rig.json"
	var spine: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	spine["slots"][0]["bone"] = "no_such_bone"
	FileAccess.open(path, FileAccess.WRITE).store_string(JSON.stringify(spine))
	FileAccess.open("user://malformed.rig.meta.json", FileAccess.WRITE).store_string(FileAccess.get_file_as_string(FIXTURE.get_basename() + ".meta.json"))
	var rig := Rig.load_file(path)
	var want := "%s: slot %s names unknown bone no_such_bone" % [path, spine["slots"][0]["name"]]
	if rig != null: failures.append("malformed: load_file returned a rig for a slot naming an unknown bone")
	if Rig.last_error != want: failures.append("malformed: error %s, expected %s" % [Rig.last_error, want])

func test_refusals() -> void:
	var no_path := _skeleton([{"name": "root"}], {}); no_path["skins"][0]["attachments"]["part"]["part"].erase("path")
	_refused("missing path", no_path, _meta(), "refusals attachment part: missing key path")
	var old_spine := _skeleton([{"name": "root"}], {}); old_spine["skeleton"]["spine"] = "4.2.43"
	_refused("spine 4.2", old_spine, _meta(), "refusals: spine 4.2.43 is not 4.3")
	old_spine["skeleton"]["spine"] = "4.30.1"
	_refused("spine 4.30", old_spine, _meta(), "refusals: spine 4.30.1 is not 4.3")
	var no_attachment := _skeleton([{"name": "root"}], {}); no_attachment["slots"][0]["attachment"] = null
	_refused("slot with no attachment", no_attachment, _meta(), "refusals: slot part has no attachment; every slot names one")
	var left := _meta(); left["facing"] = "left"
	_refused("facing left", _skeleton([{"name": "root"}], {}), left, "refusals meta: facing is left; a rig always faces right (lanes mirror it)")

func _refused(what: String, spine: Dictionary, meta: Dictionary, want: String) -> void:
	Rig.last_error = ""
	if Rig.from_data(spine, meta, "res://", "refusals") != null: failures.append("refusals: %s loaded" % what)
	if Rig.last_error != want: failures.append("refusals: %s: error %s, expected %s" % [what, Rig.last_error, want])

func _skeleton(bones: Array, attachment: Dictionary) -> Dictionary:
	var att := attachment.duplicate(); att["path"] = "part"; att["width"] = 4; att["height"] = 2
	return {
		"skeleton": {"spine": "4.3.00", "images": "parts/"},
		"bones": bones,
		"slots": [{"name": "part", "bone": bones[-1]["name"], "attachment": "part"}],
		"skins": [{"name": "default", "attachments": {"part": {"part": att}}}],
		"animations": {},
	}

func _meta() -> Dictionary:
	return {"height_px": 2, "feet_y_px": 0, "facing": "right"}

func _angle(pose: Dictionary) -> float:
	return rad_to_deg((pose["part"] as Transform2D).get_rotation())

func _near(what: String, got: float, want: float) -> void:
	if absf(got - want) > 1e-3: failures.append("%s: got %.5f, want %.5f" % [what, got, want])
