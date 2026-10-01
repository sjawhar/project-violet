class_name PaintedArt
extends GreyboxArt
## Painted desert visuals (docs/bakeoff/desert-biome-brief.md): generated tiles and sprites, tag reveal shader,
## three parallax backdrop layers. The character is GreyboxArt's: the painted sprites once they are in the project, else the STAND-IN.
## THROWAWAY.
@export var ground_tile: Texture2D
@export var wall_tile: Texture2D
@export var platform_tile: Texture2D
@export var tag_wall: Texture2D
@export var tag_platform: Texture2D
@export var orb: Texture2D
@export var goal_gate: Texture2D
@export var hazard_tile: Texture2D
@export var backdrop_far: Texture2D
@export var backdrop_mid: Texture2D
@export var backdrop_near: Texture2D
const TINTS := {"red": Color("#e04a3a"), "green": Color("#3fbf6a")}
const HAZARD := Color("#2d2540")
const REVEAL := preload("res://art/reveal.gdshader")
## Set by make_backdrop, which Game2D calls before it builds the cells: solid tiles depend on their neighbours.
var _level: Greybox
var _ground_row := -1

## A tagged cell's wall or platform: gray until its color is acquired, tinted once acquired, glowing and pulsing while active.
class RevealSprite extends Sprite2D:
	var _pulse: Tween
	func set_resonance_look(revealed: bool, active: bool) -> void:
		var mat := material as ShaderMaterial
		mat.set_shader_parameter("saturation", 1.0 if revealed else 0.0)
		mat.set_shader_parameter("glow", 0.6 if active else 0.0)
		if _pulse: _pulse.kill(); _pulse = null
		if active:
			var set_glow := func(g: float): mat.set_shader_parameter("glow", g)
			_pulse = create_tween().set_loops().set_trans(Tween.TRANS_SINE)
			_pulse.tween_method(set_glow, 0.6, 0.2, 0.7)
			_pulse.tween_method(set_glow, 0.2, 0.6, 0.7)

func make_backdrop(level: Greybox) -> Node2D:
	_level = level
	_ground_row = _most_common_top_row(level)
	var holder := Node2D.new(); holder.name = "Backdrop"; holder.z_index = -10
	for layer_spec: Array in [["Far", backdrop_far, 0.2], ["Mid", backdrop_mid, 0.5], ["Near", backdrop_near, 0.8]]:
		var tex: Texture2D = layer_spec[1]
		var layer := Parallax2D.new(); layer.name = layer_spec[0]
		layer.scroll_scale = Vector2(layer_spec[2], 1.0)  # vertically the level fits the screen, so layers stay put
		layer.repeat_size = Vector2(tex.get_width(), 0)
		# Parallax2D loops seamlessly only when the repeat covers the screen; these textures are narrower than 1920 px.
		layer.repeat_times = ceili(float(ProjectSettings.get_setting("display/window/size/viewport_width")) / tex.get_width()) + 1
		var sprite := Sprite2D.new(); sprite.texture = tex; sprite.centered = false
		sprite.position.y = level.height * level.tile_px - tex.get_height()  # bottom edge on the level's bottom edge
		layer.add_child(sprite); holder.add_child(layer)
	return holder

func make_cell(kind: String, cell: Vector2i, ts: float) -> Node2D:
	if Greybox.TAGGED.has(kind):
		var color: String = Greybox.TAGGED[kind][0]
		var tagged := RevealSprite.new()
		var mat := ShaderMaterial.new(); mat.shader = REVEAL; mat.set_shader_parameter("tint", TINTS[color])
		tagged.material = mat
		return _tile(tagged, tag_wall if Greybox.TAGGED[kind][1] == "wall" else tag_platform, cell, ts, 4, false)
	match kind:
		"solid":
			if _level.kind_at(cell.x, cell.y - 1) == "solid": return _tile(Sprite2D.new(), wall_tile, cell, ts, 4, false)
			return _tile(Sprite2D.new(), ground_tile if cell.y == _ground_row else platform_tile, cell, ts, 2, true)
		"orb_red", "orb_green":
			var sprite := Sprite2D.new(); sprite.texture = orb; sprite.modulate = TINTS[kind.trim_prefix("orb_")]
			return _fit(sprite, ts * 0.8)
		"goal":
			var sprite := Sprite2D.new(); sprite.texture = goal_gate
			_fit(sprite, ts * 2.0)
			sprite.position.y = ts / 2.0 - ts  # two tiles tall, standing on the goal cell's floor
			return sprite
		"hazard":  # a row of sandstone spikes per cell over a dark shadow-violet pit floor, so they read against the dunes
			var pit := super.make_cell(kind, cell, ts) as Polygon2D
			pit.color = HAZARD
			var spikes := Sprite2D.new(); spikes.texture = hazard_tile
			pit.add_child(_fit(spikes, ts))
			return pit
	assert(false, "PaintedArt: no visual for %s" % kind)
	return null

## Shows one 1/n-by-1/n piece of a seamless tile texture per cell, picked by the cell's position, so one texture
## spans n cells and reads at its painted scale instead of repeating every tile. Surface tiles (top_row) keep their
## top edge on every cell. Sampled through mipmaps: 1024 px art drawn at 64 px per cell.
static func _tile(sprite: Sprite2D, tex: Texture2D, cell: Vector2i, ts: float, n: int, top_row: bool) -> Sprite2D:
	var side := tex.get_width() / float(n)
	sprite.texture = tex; sprite.region_enabled = true
	sprite.region_rect = Rect2(posmod(cell.x, n) * side, 0.0 if top_row else posmod(cell.y, n) * side, side, side)
	sprite.scale = Vector2.ONE * (ts / side)
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	return sprite

## Scales a square texture to `size` pixels wide, sampled through its mipmaps.
static func _fit(sprite: Sprite2D, size: float) -> Sprite2D:
	sprite.scale = Vector2.ONE * (size / sprite.texture.get_width())
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	return sprite

## The ground line: the row where most solid cells have open space above them.
static func _most_common_top_row(level: Greybox) -> int:
	var counts := {}
	for r in level.height:
		for c in level.width:
			if level.kind_at(c, r) == "solid" and level.kind_at(c, r - 1) != "solid": counts[r] = counts.get(r, 0) + 1
	var best := -1
	for r: int in counts: if best < 0 or counts[r] > counts[best]: best = r
	return best
