class_name Sprites
extends RefCounted
## A violet-sprites v1 character (docs/bakeoff/character-rig.md): named animations of painted frames, each frame a
## body layer and a scarf layer, each layer an image and its anchor, the image pixel (from the top-left, y down) that
## sits on the character root, the player's ground point. THROWAWAY bake-off code; dimension-agnostic.
## A malformed file is refused: load_file push_errors the reason and returns null, never a partial character.
const FORMAT := "violet-sprites"
const VERSION := 1

class Layer:
	var texture: Texture2D
	var anchor: Vector2

class Frame:
	var body: Layer
	var scarf: Layer

class Clip:
	var duration: float
	var loop: bool
	var frames: Array[Frame] = []

var source: String
var height_px: float
var clips := {}  ## animation name -> Clip

static func load_file(path: String) -> Sprites:
	var text := FileAccess.get_file_as_string(path)
	if text == "": return _fail(path, "cannot read (%s)" % error_string(FileAccess.get_open_error()))
	var data: Variant = JSON.parse_string(text)
	if data is not Dictionary: return _fail(path, "not a JSON object")
	if data.get("format") != FORMAT: return _fail(path, "format is %s, not %s" % [data.get("format"), FORMAT])
	if not (data.get("version") is float and int(data["version"]) == VERSION): return _fail(path, "version is %s, not %d" % [data.get("version"), VERSION])
	if data.get("facing") != "right": return _fail(path, "facing is %s; the frames always face right (lanes mirror them)" % data.get("facing"))
	if data.get("units") != "px": return _fail(path, "units are %s, not px" % data.get("units"))
	if not (data.get("height_px") is float and data["height_px"] > 0.0): return _fail(path, "height_px must be a positive number")
	if not (data.get("animations") is Dictionary and not data["animations"].is_empty()): return _fail(path, "animations must be a non-empty object")
	var sprites := Sprites.new()
	sprites.source = path; sprites.height_px = data["height_px"]
	for anim_name: String in data["animations"]:
		var anim: Variant = data["animations"][anim_name]
		var where := "%s: animation %s" % [path, anim_name]
		if anim is not Dictionary: return _fail(where, "not an object")
		if not (anim.get("duration") is float and anim["duration"] > 0.0): return _fail(where, "duration must be a positive number")
		if anim.get("loop") is not bool: return _fail(where, "loop must be true or false")
		if not (anim.get("frames") is Array and not anim["frames"].is_empty()): return _fail(where, "frames must be a non-empty array")
		var clip := Clip.new(); clip.duration = anim["duration"]; clip.loop = anim["loop"]
		for i in anim["frames"].size():
			var frame_data: Variant = anim["frames"][i]
			if frame_data is not Dictionary: return _fail("%s frame %d" % [where, i], "not an object")
			var frame := Frame.new()
			for layer_name: String in ["body", "scarf"]:
				var layer := _layer(path, frame_data.get(layer_name), "%s frame %d %s" % [where, i, layer_name])
				if layer == null: return null
				frame.set(layer_name, layer)
			clip.frames.append(frame)
		sprites.clips[anim_name] = clip
	return sprites

static func _layer(path: String, data: Variant, where: String) -> Layer:
	if data is not Dictionary: _fail(where, "missing"); return null
	if data.get("image") is not String: _fail(where, "image must be a path"); return null
	var anchor: Variant = data.get("anchor")
	if not (anchor is Array and anchor.size() == 2 and anchor[0] is float and anchor[1] is float): _fail(where, "anchor must be [x, y]"); return null
	var image := path.get_base_dir().path_join(data["image"]).simplify_path()
	if not ResourceLoader.exists(image): _fail(where, "image %s does not exist" % image); return null
	var texture := load(image) as Texture2D
	if texture == null: _fail(where, "image %s does not load as a texture" % image); return null
	var layer := Layer.new(); layer.texture = texture; layer.anchor = Vector2(anchor[0], anchor[1])
	return layer

static func _fail(where: String, reason: String) -> Sprites:
	push_error("%s: %s" % [where, reason])
	return null

func has_animation(anim_name: String) -> bool:
	return clips.has(anim_name)

func duration(anim_name: String) -> float:
	return (clips[anim_name] as Clip).duration

## The frame shown TIME seconds into ANIM_NAME: min(floor(t * n / duration), n - 1), with t wrapped for a looping
## animation. Frames are held, not interpolated; a held animation stays on its last frame.
func frame_index(anim_name: String, time: float) -> int:
	var clip: Clip = clips[anim_name]
	var n := clip.frames.size()
	var t := fposmod(time, clip.duration) if clip.loop else maxf(time, 0.0)
	return mini(floori(t * n / clip.duration), n - 1)

func frame(anim_name: String, time: float) -> Frame:
	return (clips[anim_name] as Clip).frames[frame_index(anim_name, time)]
