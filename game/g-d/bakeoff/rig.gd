class_name Rig
extends RefCounted
## The character rig: the Spine 4.3 JSON subset docs/bakeoff/character-rig.md defines (what tools/spinerig writes),
## posed by that contract's forward kinematics; `spinerig render` is its reference implementation. No Spine runtime.
## THROWAWAY bake-off code; dimension-agnostic (G-D copies it unchanged).
## Everything here is in skeleton space with Spine's conventions: y up, x right, angles counter-clockwise, degrees in
## the file and radians in the Transform2Ds. Each lane maps skeleton space onto its own nodes (the contract's y-flip).
## Anything outside the subset (curves, scale or shear, slot timelines, non-region attachments, extra skins) fails an
## assert naming it, rather than being ignored.
const IMAGE_EXTENSION := ".png"

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
## From the .meta.json beside the rig: the setup pose's height, the feet's y and the way the art faces.
var height_px: float
var feet_y_px: float
var facing: String

## Reads PATH (spinerig's --out) and the meta file spinerig writes beside it (<stem>.meta.json).
static func load_file(path: String) -> Rig:
	var meta_path := path.get_basename() + ".meta.json"
	return from_data(_read_json(path), _read_json(meta_path), path.get_base_dir(), path)

static func _read_json(path: String) -> Dictionary:
	var text := FileAccess.get_file_as_string(path)
	assert(text != "", "%s: cannot read (%s)" % [path, error_string(FileAccess.get_open_error())])
	var data: Variant = JSON.parse_string(text)
	assert(data is Dictionary, "%s: not a JSON object" % path)
	return data

## Builds a rig from parsed spinerig output. BASE_DIR is the directory skeleton.images is relative to; WHERE names
## the source in assert messages.
static func from_data(spine: Dictionary, meta: Dictionary, base_dir: String, where := "rig") -> Rig:
	var rig := Rig.new()
	_only(where, spine, ["skeleton", "bones", "slots", "skins", "animations"])
	_only(where + " meta", meta, ["height_px", "feet_y_px", "facing"])
	rig.height_px = float(meta["height_px"]); rig.feet_y_px = float(meta["feet_y_px"]); rig.facing = meta["facing"]
	assert(rig.height_px > 0.0, "%s meta: height_px must be positive" % where)
	assert(rig.facing in ["right", "left"], "%s meta: facing %s is neither right nor left" % [where, rig.facing])
	var skeleton: Dictionary = spine["skeleton"]
	_only(where + " skeleton", skeleton, ["spine", "x", "y", "width", "height", "images"])
	assert(String(skeleton["spine"]).begins_with("4.3"), "%s: spine %s is not 4.3" % [where, skeleton["spine"]])
	var images_dir := base_dir.path_join(skeleton["images"])

	var bone_index := {}
	for data: Dictionary in spine["bones"]:
		_only("%s bone %s" % [where, data.get("name")], data, ["name", "parent", "x", "y", "rotation", "length"])
		var bone := Bone.new(); bone.name = data["name"]
		assert(not bone_index.has(bone.name), "%s: bone %s appears twice" % [where, bone.name])
		if data.has("parent"):
			assert(bone_index.has(data["parent"]), "%s: bone %s's parent %s is not listed before it" % [where, bone.name, data["parent"]])
			bone.parent = bone_index[data["parent"]]
		bone.x = data.get("x", 0.0); bone.y = data.get("y", 0.0); bone.rotation = data.get("rotation", 0.0)
		bone_index[bone.name] = rig.bones.size(); rig.bones.append(bone)

	var skins: Array = spine["skins"]
	assert(skins.size() == 1 and skins[0].get("name") == "default", "%s: expected exactly one skin, named default" % where)
	_only(where + " skin", skins[0], ["name", "attachments"])
	var skin: Dictionary = skins[0]["attachments"]
	for data: Dictionary in spine["slots"]:
		_only("%s slot %s" % [where, data.get("name")], data, ["name", "bone", "attachment"])
		var slot := Slot.new(); slot.name = data["name"]
		assert(bone_index.has(data["bone"]), "%s: slot %s names unknown bone %s" % [where, slot.name, data["bone"]])
		slot.bone = bone_index[data["bone"]]
		var attachment_name: String = data["attachment"]
		assert(skin.has(slot.name) and skin[slot.name].has(attachment_name), "%s: slot %s's attachment %s is not in the skin" % [where, slot.name, attachment_name])
		var att: Dictionary = skin[slot.name][attachment_name]
		_only("%s attachment %s" % [where, attachment_name], att, ["type", "path", "x", "y", "rotation", "width", "height"])
		assert(att.get("type", "region") == "region", "%s: attachment %s has type %s; only region attachments are supported" % [where, attachment_name, att.get("type")])
		slot.image = images_dir.path_join(String(att.get("path", attachment_name)) + IMAGE_EXTENSION).simplify_path()
		slot.local = Transform2D(deg_to_rad(att.get("rotation", 0.0)), Vector2(att.get("x", 0.0), att.get("y", 0.0)))
		slot.size = Vector2(att["width"], att["height"])
		rig.slots.append(slot)

	for anim_name: String in spine["animations"]:
		var data: Dictionary = spine["animations"][anim_name]
		_only("%s animation %s" % [where, anim_name], data, ["bones"])
		var anim := Clip.new()
		for bone_name: String in data["bones"]:
			assert(bone_index.has(bone_name), "%s: animation %s keys unknown bone %s" % [where, anim_name, bone_name])
			var timelines: Dictionary = data["bones"][bone_name]
			var context := "%s animation %s bone %s" % [where, anim_name, bone_name]
			_only(context, timelines, ["rotate", "translate"])
			if timelines.has("rotate"): anim.rotate[bone_index[bone_name]] = _keys(context + " rotate", timelines["rotate"], ["value"])
			if timelines.has("translate"): anim.translate[bone_index[bone_name]] = _keys(context + " translate", timelines["translate"], ["x", "y"])
		for keys: PackedFloat64Array in anim.rotate.values(): anim.duration = maxf(anim.duration, keys[keys.size() - 2])
		for keys: PackedFloat64Array in anim.translate.values(): anim.duration = maxf(anim.duration, keys[keys.size() - 3])
		rig.animations[anim_name] = anim
	return rig

## A timeline's keys flattened to [time, channel..., time, channel...]; a missing time or channel is 0, as in Spine.
static func _keys(context: String, entries: Array, channels: Array) -> PackedFloat64Array:
	assert(not entries.is_empty(), "%s: no keys" % context)
	var out := PackedFloat64Array()
	var last := -INF
	for key: Dictionary in entries:
		_only(context, key, ["time"] + channels)  # a "curve" lands here: only linear keys are supported
		var time: float = key.get("time", 0.0)
		assert(time >= last, "%s: key times go backwards at %s" % [context, time])
		last = time; out.append(time)
		for channel: String in channels: out.append(key.get(channel, 0.0))
	return out

static func _only(context: String, data: Dictionary, allowed: Array) -> void:
	for key: String in data: assert(key in allowed, "%s: unsupported key %s (the reader handles %s)" % [context, key, allowed])

func has_animation(animation: String) -> bool:
	return animations.has(animation)

func duration(animation: String) -> float:
	assert(animations.has(animation), "rig has no animation %s" % animation)
	return (animations[animation] as Clip).duration

## Slot name -> Transform2D: the slot's attachment centre, rotation and scale in skeleton space, for ANIMATION at TIME
## seconds, or the setup pose when ANIMATION is "". Every animation loops: TIME wraps over its duration, so t = 0
## follows t = duration. Keys interpolate linearly and add to the setup pose (rotate: degrees onto the bone's rotation;
## translate: onto its x and y); outside a timeline's keys its first or last key's value holds.
func pose(animation: String, time: float) -> Dictionary:
	var rotation := PackedFloat64Array(); var offset := PackedVector2Array()
	for bone in bones: rotation.append(bone.rotation); offset.append(Vector2(bone.x, bone.y))
	if animation != "":
		assert(animations.has(animation), "rig has no animation %s" % animation)
		var anim: Clip = animations[animation]
		var t := fposmod(time, anim.duration) if anim.duration > 0.0 else 0.0
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
