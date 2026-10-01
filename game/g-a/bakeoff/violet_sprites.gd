class_name VioletSprites
extends RefCounted
## Reads violet-sprites v1 (docs/bakeoff/character-rig.md, "Painted sprite sequences"): Violet as painted, held
## frames, each a body layer and a neutral-gray scarf layer, every layer an image plus the anchor pixel (from the
## image's top-left, y down) that sits on the character root. THROWAWAY bake-off code.
## load_file returns null after push_error, with the reason in last_error, for any file it cannot honour: wrong format,
## version, facing or units, a missing animation, field or image. There is no fallback.

## One layer of one frame: its texture and the image pixel that sits on the root.
class Layer:
	var texture: Texture2D
	var anchor: Vector2

## One frame: the body, drawn first, and the scarf, drawn over it.
class Frame:
	var body: Layer
	var scarf: Layer

## One animation: its frames, evenly spaced over duration, looping or holding the last.
class Clip:
	var duration: float
	var loop: bool
	var frames: Array[Frame] = []

static var last_error := ""
var source := ""
var height_px: float
var animations := {}  ## name -> Clip

static func load_file(path: String) -> VioletSprites:
	var text := FileAccess.get_file_as_string(path)
	if text.is_empty(): return _fail("%s: cannot read the file (%s)" % [path, error_string(FileAccess.get_open_error())])
	var data: Variant = JSON.parse_string(text)
	if data is not Dictionary: return _fail("%s: not a JSON object" % path)
	return from_data(data, path.get_base_dir(), path)

static func _fail(message: String) -> VioletSprites:
	last_error = message
	push_error(message)
	return null

static func from_data(data: Dictionary, base_dir: String, where: String) -> VioletSprites:
	if data.get("format") != "violet-sprites": return _fail("%s: format is %s, not violet-sprites" % [where, data.get("format")])
	if data.get("version") is not float or data["version"] != 1.0: return _fail("%s: version is %s, not 1" % [where, data.get("version")])
	if data.get("facing") != "right": return _fail("%s: facing is %s, not right" % [where, data.get("facing")])
	if data.get("units") != "px": return _fail("%s: units are %s, not px" % [where, data.get("units")])
	if data.get("height_px") is not float or data["height_px"] <= 0.0: return _fail("%s: height_px %s is not a positive number" % [where, data.get("height_px")])
	if data.get("animations") is not Dictionary: return _fail("%s: no animations object" % where)
	var sprites := VioletSprites.new(); sprites.source = where; sprites.height_px = data["height_px"]
	for anim_name: String in data["animations"]:
		var spec: Variant = data["animations"][anim_name]
		var context := "%s: animation %s" % [where, anim_name]
		if spec is not Dictionary: return _fail("%s is not an object" % context)
		if spec.get("duration") is not float or spec["duration"] <= 0.0: return _fail("%s: duration %s is not a positive number" % [context, spec.get("duration")])
		if spec.get("loop") is not bool: return _fail("%s: loop %s is not a boolean" % [context, spec.get("loop")])
		if spec.get("frames") is not Array or spec["frames"].is_empty(): return _fail("%s: no frames" % context)
		var anim := Clip.new(); anim.duration = spec["duration"]; anim.loop = spec["loop"]
		for i in spec["frames"].size():
			var frame_spec: Variant = spec["frames"][i]
			if frame_spec is not Dictionary: return _fail("%s frame %d is not an object" % [context, i])
			var frame := Frame.new()
			for layer_name: String in ["body", "scarf"]:
				var layer := _layer(frame_spec.get(layer_name), base_dir, "%s frame %d %s" % [context, i, layer_name])
				if layer == null: return null
				frame.set(layer_name, layer)
			anim.frames.append(frame)
		sprites.animations[anim_name] = anim
	return sprites

static func _layer(spec: Variant, base_dir: String, context: String) -> Layer:
	if spec is not Dictionary: _fail("%s: missing" % context); return null
	if spec.get("image") is not String: _fail("%s: image %s is not a path" % [context, spec.get("image")]); return null
	var anchor: Variant = spec.get("anchor")
	if anchor is not Array or anchor.size() != 2 or anchor[0] is not float or anchor[1] is not float:
		_fail("%s: anchor %s is not [x, y]" % [context, anchor]); return null
	var path := base_dir.path_join(spec["image"]).simplify_path()
	if not ResourceLoader.exists(path): _fail("%s: image %s does not exist" % [context, path]); return null
	var texture := load(path) as Texture2D
	if texture == null: _fail("%s: image %s does not load as a texture" % [context, path]); return null
	var layer := Layer.new(); layer.texture = texture; layer.anchor = Vector2(anchor[0], anchor[1])
	return layer

func has_animation(animation: String) -> bool:
	return animations.has(animation)

func duration(animation: String) -> float:
	return (animations[animation] as Clip).duration

## The frame index showing TIME seconds into ANIMATION: min(floor(t * n / duration), n - 1), with t first wrapped to
## t mod duration for a looping animation; frames are held, never interpolated (character-rig.md, Timing).
func frame_index(animation: String, time: float) -> int:
	var anim: Clip = animations[animation]
	var n: int = anim.frames.size()
	var t := fposmod(time, anim.duration) if anim.loop else time
	return mini(floori(t * n / anim.duration), n - 1)

func frame(animation: String, time: float) -> Frame:
	return (animations[animation] as Clip).frames[frame_index(animation, time)]
