class_name PaintedArt
extends GreyboxArt
## Painted desert visuals (docs/bakeoff/desert-biome-brief.md): generated tiles and sprites, the tag reveal shader,
## three parallax backdrop layers. The character is GreyboxArt's: the rig once it is in the project, else the STAND-IN.
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
const TERRAIN := preload("res://art/terrain.gdshader")
const CHARACTER_LIGHT := preload("res://art/character_light.gdshader")
const SHADOW := Color("#211728")
## Kinds that leave a terrain cell's side open (drawn as broken rock with a contact shadow). Tagged and hazard cells
## are drawn edge to edge, so a terrain cell beside them keeps a straight side.
const OPEN_KINDS := ["empty", "start", "goal", "orb_red", "orb_green"]
## Set by make_backdrop, which Game2D calls before it builds the cells: solid tiles depend on their neighbours.
var _level: Greybox
var _ground_row := -1
## Per cell, its distance under the open air that lights it (see _distance_to_air); the terrain shader darkens with it.
var _air: PackedInt32Array

## A tagged cell's wall or platform, painted neutral gray: gray until its color is acquired, tinted once acquired,
## glowing and pulsing while active.
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

## Violet as GreyboxArt attaches her, wrapped in a CanvasGroup whose shader outlines and rim-lights her whole
## silhouette (art/character_light.gdshader), plus a soft shadow under her feet while she stands on something.
func attach_character(player: Node) -> void:
	super.attach_character(player)
	var character := player.get_node_or_null("Character")
	if character == null: return  # the STAND-IN capsule: nothing to light
	var group := CanvasGroup.new(); group.name = "CharacterLight"; group.fit_margin = 12.0
	var mat := ShaderMaterial.new(); mat.shader = CHARACTER_LIGHT; group.material = mat
	player.remove_child(character); group.add_child(character); player.add_child(group)
	player.add_child(FootShadow.new())

## A soft ellipse at the player's feet, shown while the player is on the floor.
class FootShadow extends Polygon2D:
	func _ready() -> void:
		name = "FootShadow"; z_index = -1
		var points := PackedVector2Array(); var colors := PackedColorArray()
		points.append(Vector2.ZERO); colors.append(Color(SHADOW, 0.45))
		for i in 25:
			var a := TAU * i / 24.0
			points.append(Vector2(cos(a) * 30.0, sin(a) * 6.0)); colors.append(Color(SHADOW, 0.0))
		polygon = points; vertex_colors = colors
		var fan: Array = []
		for i in 24: fan.append(PackedInt32Array([0, i + 1, i + 2]))
		polygons = fan
	func _process(_delta: float) -> void:
		visible = (get_parent() as Player2D).is_on_floor()

func make_backdrop(level: Greybox) -> Node2D:
	_level = level
	_ground_row = _most_common_top_row(level)
	_air = _distance_to_air(level)
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
		if Greybox.TAGGED[kind][1] == "wall": return _tile(tagged, tag_wall, cell, ts, 4, false)
		return _tile(tagged, tag_platform, cell, ts, 2, true)  # sampled like platform-tile: the slab top on every cell
	match kind:
		"solid":
			return _terrain(cell, ts)
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
			# Gloom rising out of the pit over the open cells above it, so the pit reads as a chasm, not a window.
			var gloom := Polygon2D.new(); gloom.z_index = 1
			var top := -ts / 2.0 - ts * _open_above(cell)
			gloom.polygon = PackedVector2Array([Vector2(-ts / 2.0, top), Vector2(ts / 2.0, top), Vector2(ts / 2.0, -ts / 2.0), Vector2(-ts / 2.0, -ts / 2.0)])
			gloom.vertex_colors = PackedColorArray([Color(HAZARD, 0.0), Color(HAZARD, 0.0), Color(HAZARD, 0.85), Color(HAZARD, 0.85)])
			pit.add_child(gloom)
			var spikes := Sprite2D.new(); spikes.texture = hazard_tile
			spikes.z_index = 2
			pit.add_child(_fit(spikes, ts))
			return pit
	assert(false, "PaintedArt: no visual for %s" % kind)
	return null

## A terrain cell: its stone tile drawn through the terrain shader (eroded open sides, rounded open corners, a dark
## mass under a lit lip), plus a contact shadow on each open side.
func _terrain(cell: Vector2i, ts: float) -> Node2D:
	var covered := _level.kind_at(cell.x, cell.y - 1) == "solid"
	var sprite: Sprite2D
	if covered: sprite = _tile(Sprite2D.new(), wall_tile, cell, ts, 4, false)
	else: sprite = _tile(Sprite2D.new(), ground_tile if cell.y == _ground_row else platform_tile, cell, ts, 2, true)
	var open := Vector4(
		float(_level.kind_at(cell.x - 1, cell.y) in OPEN_KINDS), float(not covered),
		float(_level.kind_at(cell.x + 1, cell.y) in OPEN_KINDS), float(_level.kind_at(cell.x, cell.y + 1) in OPEN_KINDS))
	var mat := ShaderMaterial.new(); mat.shader = TERRAIN
	mat.set_shader_parameter("side", sprite.region_rect.size.x)
	mat.set_shader_parameter("open", open)
	mat.set_shader_parameter("cell", Vector2(cell))
	var foot := func(dx: int) -> float:  # a surface cell at the foot of rock rising beside it
		return float(not covered and _level.kind_at(cell.x + dx, cell.y) == "solid" and _level.kind_at(cell.x + dx, cell.y - 1) == "solid")
	mat.set_shader_parameter("foot", Vector2(foot.call(-1), foot.call(1)))
	mat.set_shader_parameter("air", Vector4(_corner_air(cell), _corner_air(cell + Vector2i(1, 0)),
		_corner_air(cell + Vector2i(0, 1)), _corner_air(cell + Vector2i(1, 1))))
	sprite.material = mat
	var holder := Node2D.new()
	holder.add_child(sprite)
	for side_open: Array in [[open.x, -1.0], [open.z, 1.0]]:  # a soft shadow dropped onto the backdrop beside an open side
		if side_open[0] < 0.5: continue
		var face: float = side_open[1] * ts * 0.1  # starts under the rock, so the eroded edge shows the gradient too
		var out: float = side_open[1] * ts * 0.95
		var shadow := Polygon2D.new(); shadow.z_index = -1
		shadow.polygon = PackedVector2Array([Vector2(face, -ts / 2.0), Vector2(out, -ts / 2.0), Vector2(out, ts / 2.0), Vector2(face, ts / 2.0)])
		var top_alpha := 0.0 if open.y > 0.5 else 0.5  # a surface cell's shadow fades out at the ground line
		shadow.vertex_colors = PackedColorArray([Color(SHADOW, top_alpha), Color(SHADOW, 0.0), Color(SHADOW, 0.0), Color(SHADOW, 0.5)])
		holder.add_child(shadow)
	return holder

## How many open cells stand directly above a cell (the pit's depth above a hazard cell), at most 3.
func _open_above(cell: Vector2i) -> int:
	var n := 0
	while n < 3 and _level.kind_at(cell.x, cell.y - 1 - n) in OPEN_KINDS: n += 1
	return n

## The air distance at a cell corner (the corner at the cell's top-left): the mean of the four cells around it,
## so the darkening runs smoothly across cell borders.
func _corner_air(corner: Vector2i) -> float:
	var total := 0.0
	for c in [corner + Vector2i(-1, -1), corner + Vector2i(0, -1), corner + Vector2i(-1, 0), corner]: total += _air_at(c)
	return total / 4.0

func _air_at(c: Vector2i) -> int:
	if c.x < 0 or c.y < 0 or c.x >= _level.width or c.y >= _level.height: return AIR_CAP  # beyond the level is deep rock
	return _air[c.y * _level.width + c.x]

## Per cell, how far it lies under the open air that lights it: the cheapest path to an open cell moving up or
## diagonally up (cost 1) or sideways (cost 2), never down, capped at AIR_CAP. Rock is lit from above, so a mass darkens
## steadily from its top down and only a little from its open sides.
const AIR_CAP := 5
static func _distance_to_air(level: Greybox) -> PackedInt32Array:
	var w := level.width
	var dist := PackedInt32Array(); dist.resize(w * level.height); dist.fill(AIR_CAP)
	# Rows top to bottom: a cell's cost depends only on the row above and on its own row, so two sweeps of each row
	# (left to right, right to left) settle the sideways steps.
	for r in level.height:
		for c in w:
			if level.kind_at(c, r) in OPEN_KINDS: dist[r * w + c] = 0; continue
			var best := AIR_CAP
			if r > 0:
				best = mini(best, dist[(r - 1) * w + c] + 1)
				if c > 0: best = mini(best, dist[(r - 1) * w + c - 1] + 1)
				if c < w - 1: best = mini(best, dist[(r - 1) * w + c + 1] + 1)
			dist[r * w + c] = best
		for c in range(1, w): dist[r * w + c] = mini(dist[r * w + c], dist[r * w + c - 1] + 2)
		for c in range(w - 2, -1, -1): dist[r * w + c] = mini(dist[r * w + c], dist[r * w + c + 1] + 2)
	return dist

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
