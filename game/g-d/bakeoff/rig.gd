class_name Rig
extends RefCounted
## The character rig: the Spine 4.3 JSON subset docs/bakeoff/character-rig.md defines (what tools/spinerig writes),
## posed by that contract's forward kinematics; `spinerig render` is its reference implementation. No Spine runtime.
## THROWAWAY bake-off code; dimension-agnostic (G-D copies it unchanged).
## Everything here is in skeleton space with Spine's conventions: y up, x right, angles counter-clockwise, degrees in
## the file and radians in the Transform2Ds. Each lane maps skeleton space onto its own nodes (the contract's y-flip).
## Anything outside the subset (curves, scale or shear, slot timelines, non-region attachments, extra skins) fails the
## load with a push_error naming the file and the offender, rather than being ignored; debug and release builds alike.
const IMAGE_EXTENSION := ".png"
## Looping is by animation name (character-rig.md): these loop, every other animation plays once and holds its last frame.
const LOOPING := ["idle", "run"]

class Bone:
	var name: String
	var parent := -1  ## index into bones; parents come before their children
	var x := 0.0
	var y := 0.0
	var rotation := 0.0  ## degrees

class Slot:
	var name: String
	var bone: int  ## index into bones
	var image: String  ## the part image's path: skeleton.images + the attachment's path + IMAGE_EXTENSION
	var local: Transform2D  ## the region attachment's centre and rotation in its bone's space
	var size: Vector2  ## the region attachment's width and height

class Clip:
	var duration := 0.0  ## the last key's time over every timeline, as the Spine runtime computes it
	var rotate := {}  ## bone index -> PackedFloat64Array [time, degrees, time, degrees, ...]
	var translate := {}  ## bone index -> PackedFloat64Array [time, x, y, time, x, y, ...]

var bones: Array[Bone] = []
## In draw order, back to front.
var slots: Array[Slot] = []
var animations := {}  ## name -> Clip
## From the .meta.json beside the rig: the setup pose's height and the skeleton-space y of ground contact (subtracted
## so the feet sit on the floor). Its "facing" must be "right": the art faces right and lanes mirror it for left.
var height_px: float
var feet_y_px: float
## The file the rig came from, for error messages.
var source: String

## The last load failure's message ("<file>: <what is wrong>"), also sent to push_error.
static var last_error := ""

## Reads PATH (spinerig's --out) and the meta file spinerig writes beside it (<stem>.meta.json). Returns null after a
## push_error naming the file and the problem when either is missing or outside the subset.
static func load_file(path: String) -> Rig:
	var spine: Variant = _read_json(path)
	if spine == null: return null
	var meta: Variant = _read_json(path.get_basename() + ".meta.json")
	if meta == null: return null
	return from_data(spine, meta, path.get_base_dir(), path)

static func _read_json(path: String) -> Variant:
	var text := FileAccess.get_file_as_string(path)
	if text == "": return _fail("%s: cannot read (%s)" % [path, error_string(FileAccess.get_open_error())])
	var data: Variant = JSON.parse_string(text)
	if data is not Dictionary: return _fail("%s: not a JSON object" % path)
	return data

static func _fail(message: String) -> Variant:
	last_error = message
	push_error(message)
	return null

## Builds a rig from parsed spinerig output, or returns null after a push_error. BASE_DIR is the directory
## skeleton.images is relative to; WHERE (the file) starts every error message.
static func from_data(spine: Dictionary, meta: Dictionary, base_dir: String, where := "rig") -> Rig:
	var rig := Rig.new(); rig.source = where
	var bad := _keys_error(where, spine, ["skeleton", "bones", "slots", "skins", "animations"], ["skeleton", "bones", "slots", "skins"])
	bad = bad if bad else _keys_error(where + " meta", meta, ["height_px", "feet_y_px", "facing"], ["height_px", "feet_y_px", "facing"])
	if bad: return _fail(bad)
	rig.height_px = float(meta["height_px"]); rig.feet_y_px = float(meta["feet_y_px"])
	if rig.height_px <= 0.0: return _fail("%s meta: height_px must be positive" % where)
	if meta["facing"] != "right": return _fail("%s meta: facing is %s; a rig always faces right (lanes mirror it)" % [where, meta["facing"]])
	var skeleton: Dictionary = spine["skeleton"]
	bad = _keys_error(where + " skeleton", skeleton, ["spine", "x", "y", "width", "height", "images"], ["spine", "images"])
	if bad: return _fail(bad)
	if not String(skeleton["spine"]).begins_with("4.3."): return _fail("%s: spine %s is not 4.3" % [where, skeleton["spine"]])
	var images_dir := base_dir.path_join(skeleton["images"])

	var bone_index := {}
	for data: Dictionary in spine["bones"]:
		bad = _keys_error("%s bone %s" % [where, data.get("name")], data, ["name", "parent", "x", "y", "rotation", "length"], ["name"])
		if bad: return _fail(bad)
		var bone := Bone.new(); bone.name = data["name"]
		if bone_index.has(bone.name): return _fail("%s: bone %s appears twice" % [where, bone.name])
		if data.has("parent"):
			if not bone_index.has(data["parent"]): return _fail("%s: bone %s's parent %s is not listed before it" % [where, bone.name, data["parent"]])
			bone.parent = bone_index[data["parent"]]
		bone.x = data.get("x", 0.0); bone.y = data.get("y", 0.0); bone.rotation = data.get("rotation", 0.0)
		bone_index[bone.name] = rig.bones.size(); rig.bones.append(bone)

	var skins: Array = spine["skins"]
	if skins.size() != 1 or skins[0].get("name") != "default": return _fail("%s: expected exactly one skin, named default" % where)
	bad = _keys_error(where + " skin", skins[0], ["name", "attachments"], ["name", "attachments"])
	if bad: return _fail(bad)
	var skin: Dictionary = skins[0]["attachments"]
	for data: Dictionary in spine["slots"]:
		bad = _keys_error("%s slot %s" % [where, data.get("name")], data, ["name", "bone", "attachment"], ["name", "bone"])
		if bad: return _fail(bad)
		if data.get("attachment") is not String: return _fail("%s: slot %s has no attachment; every slot names one" % [where, data["name"]])
		var slot := Slot.new(); slot.name = data["name"]
		if not bone_index.has(data["bone"]): return _fail("%s: slot %s names unknown bone %s" % [where, slot.name, data["bone"]])
		slot.bone = bone_index[data["bone"]]
		var attachment_name := String(data["attachment"])
		if not (skin.has(slot.name) and skin[slot.name].has(attachment_name)): return _fail("%s: slot %s's attachment %s is not in the skin" % [where, slot.name, attachment_name])
		var att: Dictionary = skin[slot.name][attachment_name]
		bad = _keys_error("%s attachment %s" % [where, attachment_name], att, ["type", "path", "x", "y", "rotation", "width", "height"], ["path", "width", "height"])
		if bad: return _fail(bad)
		if att.get("type", "region") != "region": return _fail("%s: attachment %s has type %s; only region attachments are supported" % [where, attachment_name, att.get("type")])
		slot.image = images_dir.path_join(String(att["path"]) + IMAGE_EXTENSION).simplify_path()
		slot.local = Transform2D(deg_to_rad(att.get("rotation", 0.0)), Vector2(att.get("x", 0.0), att.get("y", 0.0)))
		slot.size = Vector2(att["width"], att["height"])
		rig.slots.append(slot)

	var animations_data: Dictionary = spine.get("animations", {})
	for anim_name: String in animations_data:
		var data: Dictionary = animations_data[anim_name]
		bad = _keys_error("%s animation %s" % [where, anim_name], data, ["bones"], ["bones"])
		if bad: return _fail(bad)
		var anim := Clip.new()
		for bone_name: String in data["bones"]:
			if not bone_index.has(bone_name): return _fail("%s: animation %s keys unknown bone %s" % [where, anim_name, bone_name])
			var timelines: Dictionary = data["bones"][bone_name]
			var context := "%s animation %s bone %s" % [where, anim_name, bone_name]
			bad = _keys_error(context, timelines, ["rotate", "translate"], [])
			if bad: return _fail(bad)
			for timeline: String in timelines:
				var channels: Array = ["value"] if timeline == "rotate" else ["x", "y"]
				var keys := _keys(context + " " + timeline, timelines[timeline], channels)
				if keys.is_empty(): return null
				var timelines_of: Dictionary = anim.rotate if timeline == "rotate" else anim.translate
				timelines_of[bone_index[bone_name]] = keys
				anim.duration = maxf(anim.duration, keys[keys.size() - 1 - channels.size()])
		rig.animations[anim_name] = anim
	return rig

## A timeline's keys flattened to [time, channel..., time, channel...]; a missing time or channel is 0, as in Spine.
## Empty after a push_error when the timeline is outside the subset.
static func _keys(context: String, entries: Array, channels: Array) -> PackedFloat64Array:
	var out := PackedFloat64Array()
	if entries.is_empty(): _fail("%s: no keys" % context); return out
	var last := -INF
	for key: Dictionary in entries:
		var bad := _keys_error(context, key, ["time"] + channels, [])  # a "curve" lands here: only linear keys are supported
		if bad: _fail(bad); return PackedFloat64Array()
		var time: float = key.get("time", 0.0)
		if time < last: _fail("%s: key times go backwards at %s" % [context, time]); return PackedFloat64Array()
		last = time; out.append(time)
		for channel: String in channels: out.append(key.get(channel, 0.0))
	return out

## "" when DATA has only ALLOWED keys and every REQUIRED one; else the message naming the first offender.
static func _keys_error(context: String, data: Dictionary, allowed: Array, required: Array) -> String:
	for key: String in data:
		if key not in allowed: return "%s: unsupported key %s (the reader handles %s)" % [context, key, allowed]
	for key: String in required:
		if not data.has(key): return "%s: missing key %s" % [context, key]
	return ""

func has_animation(animation: String) -> bool:
	return animations.has(animation)

func duration(animation: String) -> float:
	assert(animations.has(animation), "rig has no animation %s" % animation)
	return (animations[animation] as Clip).duration

## Slot name -> Transform2D: the slot's attachment centre, rotation and scale in skeleton space, for ANIMATION at TIME
## seconds, or the setup pose when ANIMATION is "". A LOOPING animation wraps TIME over its duration, so t = 0 follows
## t = duration; any other plays once and holds its last frame. Keys interpolate linearly and add to the setup pose (rotate: degrees onto the bone's rotation;
## translate: onto its x and y); outside a timeline's keys its first or last key's value holds.
func pose(animation: String, time: float) -> Dictionary:
	var rotation := PackedFloat64Array(); var offset := PackedVector2Array()
	for bone in bones: rotation.append(bone.rotation); offset.append(Vector2(bone.x, bone.y))
	if animation != "":
		assert(animations.has(animation), "rig has no animation %s" % animation)
		var anim: Clip = animations[animation]
		var t := clampf(time, 0.0, anim.duration)
		if animation in LOOPING: t = fposmod(time, anim.duration) if anim.duration > 0.0 else 0.0
		for i: int in anim.rotate: rotation[i] += _sample(anim.rotate[i], 2, 1, t)
		for i: int in anim.translate:
			offset[i] += Vector2(_sample(anim.translate[i], 3, 1, t), _sample(anim.translate[i], 3, 2, t))
	var world: Array[Transform2D] = []
	for i in bones.size():
		var local := Transform2D(deg_to_rad(rotation[i]), offset[i])
		world.append(world[bones[i].parent] * local if bones[i].parent >= 0 else local)
	var out := {}
	for slot in slots: out[slot.name] = world[slot.bone] * slot.local
	return out

## The axis-aligned box around every slot's attachment rectangle in POSE (skeleton space, y up).
## For the setup pose this is spinerig's skeleton x/y/width/height, and its height is the meta's height_px.
func bounds(pose_: Dictionary) -> Rect2:
	var box := Rect2()
	for i in slots.size():
		var t: Transform2D = pose_[slots[i].name]
		for corner: Vector2 in [Vector2(-0.5, -0.5), Vector2(0.5, -0.5), Vector2(0.5, 0.5), Vector2(-0.5, 0.5)]:
			var p := t * (corner * slots[i].size)
			box = Rect2(p, Vector2.ZERO) if i == 0 and corner == Vector2(-0.5, -0.5) else box.expand(p)
	return box

## The value of CHANNEL (1-based within each STRIDE-wide key) at time T, linear between the keys around it.
static func _sample(keys: PackedFloat64Array, stride: int, channel: int, t: float) -> float:
	if t <= keys[0]: return keys[channel]
	var count := keys.size() / stride
	for i in count - 1:
		var t1 := keys[(i + 1) * stride]
		if t < t1:
			var t0 := keys[i * stride]
			return lerpf(keys[i * stride + channel], keys[(i + 1) * stride + channel], (t - t0) / (t1 - t0))
	return keys[(count - 1) * stride + channel]
