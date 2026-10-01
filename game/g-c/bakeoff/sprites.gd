class_name Sprites
extends RefCounted
## Reads a violet-sprites v1 file (the painted, frame-by-frame protagonist; format in docs/bakeoff/character-rig.md):
## per animation a duration, a loop flag and frames, each frame a body layer and a scarf layer, each layer an image
## (relative to the JSON) and an anchor, the image pixel (from its top-left, y down) that sits on the character root,
## the player's ground point. THROWAWAY bake-off code; dimension-agnostic.
## A file that is malformed (wrong format or version, a missing key, an image that does not load) is refused: load_file
## and from_data push_error the reason, keep it in last_error and return null. There is no fallback.
const FORMAT := "violet-sprites"
const VERSION := 1
const LAYERS := ["body", "scarf"]

## One layer of one frame: its texture and the pixel of it that sits on the character root.
class Layer:
	var texture: Texture2D
	var anchor: Vector2

## One animation (a clip): how long it runs, whether it loops, and its frames (each a Dictionary layer name -> Layer).
class Clip:
	var duration: float
	var loop: bool
	var frames: Array[Dictionary] = []

var source: String
var height_px: float
var animations := {}  ## name -> Clip
static var last_error := ""

static func load_file(path: String) -> Sprites:
	if not FileAccess.file_exists(path): return _refuse("%s: no such file" % path)
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if data is not Dictionary: return _refuse("%s: not a JSON object" % path)
	return from_data(data, path.get_base_dir(), path)

## DATA is the parsed file; images resolve against BASE_DIR; SOURCE names the file in errors.
static func from_data(data: Dictionary, base_dir: String, source_: String) -> Sprites:
	if data.get("format") != FORMAT: return _refuse("%s: format is %s, not %s" % [source_, data.get("format"), FORMAT])
	if data.get("version") != float(VERSION) and data.get("version") != VERSION:
		return _refuse("%s: version is %s, not %d" % [source_, data.get("version"), VERSION])
	if data.get("facing") != "right": return _refuse("%s: facing is %s; a sprite set always faces right" % [source_, data.get("facing")])
	for key: String in ["height_px", "animations"]:
		if not data.has(key): return _refuse("%s: missing key %s" % [source_, key])
	var sprites := Sprites.new()
	sprites.source = source_; sprites.height_px = float(data["height_px"])
	if sprites.height_px <= 0.0: return _refuse("%s: height_px must be positive" % source_)
	for anim_name: String in data["animations"]:
		var spec: Dictionary = data["animations"][anim_name]
		for key: String in ["duration", "loop", "frames"]:
			if not spec.has(key): return _refuse("%s animation %s: missing key %s" % [source_, anim_name, key])
		var anim := Clip.new()
		anim.duration = float(spec["duration"]); anim.loop = bool(spec["loop"])
		if anim.duration <= 0.0 or (spec["frames"] as Array).is_empty():
			return _refuse("%s animation %s: needs a positive duration and at least one frame" % [source_, anim_name])
		for i in (spec["frames"] as Array).size():
			var frame: Dictionary = spec["frames"][i]
			var layers := {}
			for layer_name: String in LAYERS:
				var where := "%s animation %s frame %d %s" % [source_, anim_name, i, layer_name]
				if not frame.has(layer_name): return _refuse("%s: missing" % where)
				var layer_spec: Dictionary = frame[layer_name]
				if not layer_spec.has("image") or not layer_spec.has("anchor") or (layer_spec["anchor"] as Array).size() != 2:
					return _refuse("%s: needs an image and a two-number anchor" % where)
				var image_path := base_dir.path_join(layer_spec["image"]).simplify_path()
				if not ResourceLoader.exists(image_path): return _refuse("%s: image %s does not exist" % [where, image_path])
				var layer := Layer.new()
				layer.texture = load(image_path) as Texture2D
				if layer.texture == null: return _refuse("%s: image %s does not load as a texture" % [where, image_path])
				layer.anchor = Vector2(float(layer_spec["anchor"][0]), float(layer_spec["anchor"][1]))
				layers[layer_name] = layer
			anim.frames.append(layers)
		sprites.animations[anim_name] = anim
	return sprites

func has_animation(anim_name: String) -> bool:
	return animations.has(anim_name)

func duration(anim_name: String) -> float:
	return (animations[anim_name] as Clip).duration

## The frame shown at time T: min(floor(t * n / duration), n - 1), with t wrapped for looping animations; held
## animations stay on their last frame.
func frame_index(anim_name: String, t: float) -> int:
	var anim: Clip = animations[anim_name]
	var n := anim.frames.size()
	var at := fposmod(t, anim.duration) if anim.loop else maxf(t, 0.0)
	return mini(floori(at * n / anim.duration), n - 1)

## The layers (name -> Layer) of the frame shown at time T.
func frame(anim_name: String, t: float) -> Dictionary:
	return (animations[anim_name] as Clip).frames[frame_index(anim_name, t)]

static func _refuse(message: String) -> Sprites:
	last_error = message
	push_error(message)
	return null
