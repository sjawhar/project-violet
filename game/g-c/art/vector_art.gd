class_name VectorArt
extends PaintedArt
## Flat-vector desert visuals for lane G-C (docs/bakeoff/desert-biome-brief.md, SVG kit): PaintedArt's slots filled with
## hand-written SVGs (art/*.svg) that Godot rasterizes at their viewBox size, placed as PaintedArt places them, plus:
## wall and ground tiles drawn from several variants, pits with a painted inside, and sky and rock filling the strips
## the camera shows above and below the level; tag colours locked and lit by the low sun in art/reveal.gdshader, with a
## chevron carved on red and a double wave on green; and the character drawn through art/character_outline.gdshader
## (dark outline, thin light halo, warm sun-side rim, hardened alpha fringe). The character is GreyboxArt's: the rig in
## protagonist/ once it is there, else the STAND-IN. Set dressing and atmosphere: aerial haze that grows with each
## backdrop layer's distance, uneven soft light shafts from the sun on the far layer, dust motes drifting in the air,
## dry-grass tufts on some open block tops, and a dark foreground silhouette strip along the bottom of the frame on a
## faster parallax layer. Terrain construction: each connected rock mass takes its own tone and its wall variant per
## four-row band (no vertical variant seams inside a block), open tops carry an uneven sand lip, exposed sides an
## eroded rock edge (warm on the sunward left, shaded on the right), and pits a painted inside that falls away into the
## shadow the spikes stand in. THROWAWAY.
## Extra wall-tile and ground-tile variants; each keeps the band heights where blocks meet, so any mix is seamless.
@export var wall_tile_variants: Array[Texture2D] = []
@export var ground_tile_variants: Array[Texture2D] = []
## The dark near-plane silhouettes along the bottom of the frame, and the grass tuft set on block tops.
@export var foreground: Texture2D
@export var tuft: Texture2D
## Terrain construction decals (art/lip-top.svg, edge-left.svg, edge-right.svg) and the inside of a pit (pit-depth.svg).
@export var lip_top: Texture2D
@export var edge_left: Texture2D
@export var edge_right: Texture2D
@export var pit_depth: Texture2D
## One tone per connected rock mass, so neighbouring blocks don't read as the same tile.
const MASS_TONES := [Color(1.0, 0.96, 0.9), Color(1.0, 1.0, 1.0), Color(0.97, 0.93, 0.95), Color(1.0, 0.98, 0.94)]
## Solid cell -> index of the connected rock mass it belongs to (filled by make_backdrop).
var _mass := {}
## Where backdrop-far.svg draws the sun, in its own pixels.
const SUN := Vector2(900, 660)
## The foreground strip's parallax: faster than the playfield, so it reads as nearer.
const FOREGROUND_SCROLL := 1.25
const HAZE := preload("res://art/haze.gdshader")
## Aerial perspective per backdrop layer: [haze colour, amount]; the farther the layer, the more it fades.
const LAYER_HAZE := {"Mid": [Color("#dcb2aa"), 0.3], "Near": [Color("#ecd0aa"), 0.12]}
## The top colour of backdrop-far.svg's sky gradient, used above the level.
const SKY_TOP := Color("#2e6d7e")
## How far the pit darkening reaches above a hazard cell, in cells.
const PIT_SHADE_CELLS := 2.0
## art/reveal.gdshader's shape cue per tag colour.
const PATTERNS := {"red": 1, "green": 2}
const OUTLINE := preload("res://art/character_outline.gdshader")

func make_backdrop(level: Greybox) -> Node2D:
	var holder := super.make_backdrop(level)
	_find_masses(level)
	var ts := float(level.tile_px)
	var width := level.width * ts
	# The camera keeps the whole level height in a 1080 px view, so a strip shows above and below the 1024 px level.
	var sky := ColorRect.new(); sky.name = "SkyAbove"; sky.color = SKY_TOP
	sky.position = Vector2(-ts, -ts); sky.size = Vector2(width + 2.0 * ts, ts)
	holder.add_child(sky)
	var rock := Node2D.new(); rock.name = "RockBelow"
	for c in range(-1, level.width + 1):
		var cell := Vector2i(c, level.height)
		var tile := _tile(Sprite2D.new(), _pick(_wall_tiles(), Vector2i(floori(c / 4.0), floori(cell.y / 4.0))), cell, ts, 4, false)
		tile.position = Vector2((c + 0.5) * ts, (level.height + 0.5) * ts)
		rock.add_child(tile)
	holder.add_child(rock)
	(holder.get_node("Far") as Node2D).add_child(_light_shafts())
	for layer_name: String in LAYER_HAZE:
		var mat := ShaderMaterial.new(); mat.shader = HAZE
		mat.set_shader_parameter("haze", LAYER_HAZE[layer_name][0]); mat.set_shader_parameter("amount", LAYER_HAZE[layer_name][1])
		(holder.get_node(layer_name).get_child(0) as CanvasItem).material = mat
	holder.add_child(_foreground(level))
	return holder

## Flood-fills the solid cells into connected rock masses.
func _find_masses(level: Greybox) -> void:
	_mass.clear()
	var next := 0
	for r in level.height:
		for c in level.width:
			var start := Vector2i(c, r)
			if level.kind_at(c, r) != "solid" or _mass.has(start): continue
			var todo: Array[Vector2i] = [start]; _mass[start] = next
			while not todo.is_empty():
				var cell: Vector2i = todo.pop_back()
				for d: Vector2i in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
					var n := cell + d
					if n.x < 0 or n.y < 0 or n.x >= level.width or n.y >= level.height: continue
					if level.kind_at(n.x, n.y) == "solid" and not _mass.has(n): _mass[n] = next; todo.append(n)
			next += 1

## Faint warm rays fanning up from the low sun, added on top of the far layer so they move with it.
func _light_shafts() -> Node2D:
	var rays := Node2D.new(); rays.name = "LightShafts"
	var mat := CanvasItemMaterial.new(); mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	# [angle, width, strength, length]: uneven on purpose, so the fan does not read as a stamped sunburst
	for spec: Vector4 in [Vector4(-150, 14, 0.07, 1300), Vector4(-122, 7, 0.05, 900), Vector4(-97, 18, 0.09, 1500), Vector4(-66, 9, 0.05, 1100), Vector4(-41, 16, 0.07, 1400)]:
		var a0 := deg_to_rad(spec.x - spec.y / 2.0); var a1 := deg_to_rad(spec.x + spec.y / 2.0); var am := deg_to_rad(spec.x)
		var ray := Polygon2D.new(); ray.material = mat
		# bright along the middle, fading to nothing at both edges and at the far end
		ray.polygon = PackedVector2Array([SUN, SUN + Vector2(cos(a0), sin(a0)) * spec.w, SUN + Vector2(cos(am), sin(am)) * spec.w, SUN + Vector2(cos(a1), sin(a1)) * spec.w])
		var warm := Color(1.0, 0.86, 0.62, 0.0)
		ray.vertex_colors = PackedColorArray([Color(warm, spec.z), warm, Color(warm, spec.z * 0.15), warm])
		ray.polygons = [PackedInt32Array([0, 1, 2]), PackedInt32Array([0, 2, 3])]
		rays.add_child(ray)
	return rays

## The dark silhouette strip in front of the playfield, on the bottom edge of what the camera shows.
func _foreground(level: Greybox) -> Node2D:
	var layer := Parallax2D.new(); layer.name = "Foreground"
	layer.scroll_scale = Vector2(FOREGROUND_SCROLL, 1.0)
	layer.repeat_size = Vector2(foreground.get_width(), 0)
	layer.repeat_times = 2
	layer.z_index = 20  # holder is at -10: this lands in front of the world and the character
	var sprite := Sprite2D.new(); sprite.texture = foreground; sprite.centered = false
	# the camera shows (1080 - 1024) / 2 = 28 px below the level; the strip's bottom edge goes there
	sprite.position.y = level.height * level.tile_px + 28.0 - foreground.get_height()
	layer.add_child(sprite)
	return layer

func make_cell(kind: String, cell: Vector2i, ts: float) -> Node2D:
	match kind:
		"solid":
			var m: int = _mass.get(cell, 0)
			var tile: Sprite2D
			if _level.kind_at(cell.x, cell.y - 1) == "solid":
				tile = _tile(Sprite2D.new(), _pick(_wall_tiles(), Vector2i(m * 7919, floori(cell.y / 4.0))), cell, ts, 4, false)
			elif cell.y == _ground_row:
				tile = _tile(Sprite2D.new(), _pick([ground_tile] + ground_tile_variants, Vector2i(floori(cell.x / 2.0), 0)), cell, ts, 2, true)
			else:
				tile = super.make_cell(kind, cell, ts) as Sprite2D
			tile.modulate = MASS_TONES[m % MASS_TONES.size()]
			return _dress(tile, cell, ts)
		"hazard":
			var pit := super.make_cell(kind, cell, ts)
			var inside := Sprite2D.new(); inside.name = "PitDepth"; inside.texture = pit_depth; inside.centered = false
			var side := pit_depth.get_width() / 4.0
			inside.region_enabled = true
			inside.region_rect = Rect2(posmod(cell.x, 4) * side, 0.0, side, pit_depth.get_height())
			inside.scale = Vector2.ONE * (ts / side)
			inside.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
			inside.position = Vector2(-ts / 2.0, -ts / 2.0 - PIT_SHADE_CELLS * ts)
			pit.add_child(inside)
			return pit
	var node := super.make_cell(kind, cell, ts)
	if Greybox.TAGGED.has(kind):
		var mat := node.material as ShaderMaterial
		mat.set_shader_parameter("pattern", PATTERNS[Greybox.TAGGED[kind][0]])
		mat.set_shader_parameter("open_sides", Vector4(
			0.0 if _level.kind_at(cell.x - 1, cell.y) == kind else 1.0, 0.0 if _level.kind_at(cell.x + 1, cell.y) == kind else 1.0,
			0.0 if _level.kind_at(cell.x, cell.y - 1) == kind else 1.0, 0.0 if _level.kind_at(cell.x, cell.y + 1) == kind else 1.0))
		mat.set_shader_parameter("run_v", _run(kind, cell, Vector2i.UP, Vector2i.DOWN))
		mat.set_shader_parameter("run_h", _run(kind, cell, Vector2i.LEFT, Vector2i.RIGHT))
	return node

## This cell's index in the straight run of KIND cells through it along BACK/FORWARD, and the run's length.
func _run(kind: String, cell: Vector2i, back: Vector2i, forward: Vector2i) -> Vector2:
	var before := 0
	while _level.kind_at(cell.x + back.x * (before + 1), cell.y + back.y * (before + 1)) == kind: before += 1
	var after := 0
	while _level.kind_at(cell.x + forward.x * (after + 1), cell.y + forward.y * (after + 1)) == kind: after += 1
	return Vector2(before, before + after + 1)

## A solid cell's tile with its construction: an eroded rock edge on each side open to the air, an uneven sand lip
## where the top is open, and a grass tuft on about one open top in three (the same cells every run).
func _dress(tile: Sprite2D, cell: Vector2i, ts: float) -> Node2D:
	var holder := Node2D.new(); holder.add_child(tile)
	var h := ts / 2.0
	var sc := ts / float(edge_left.get_height())
	if not _is_block(cell + Vector2i.LEFT):
		holder.add_child(_decal(edge_left, Vector2(-h - 40.0 * sc, -h), sc))
	if not _is_block(cell + Vector2i.RIGHT):
		holder.add_child(_decal(edge_right, Vector2(h - 24.0 * sc, -h), sc))
	if _is_block(cell + Vector2i.UP): return holder
	var lip_sc := ts / float(lip_top.get_width())
	holder.add_child(_decal(lip_top, Vector2(-h, -h - 48.0 * lip_sc), lip_sc))
	var mix := (cell.x * 2654435761) ^ (cell.y * 40503)
	if posmod(mix, 3) == 0:
		var w := ts * 1.1
		var grass := _decal(tuft, Vector2.ZERO, w / tuft.get_width())
		grass.position = Vector2(-w / 2.0 + float(posmod(mix >> 3, 17) - 8), -h - tuft.get_height() * grass.scale.y + 2.0)
		holder.add_child(grass)
	return holder

func _is_block(cell: Vector2i) -> bool:
	var kind := _level.kind_at(cell.x, cell.y)
	return kind == "solid" or Greybox.TAGGED.has(kind)

static func _decal(tex: Texture2D, at: Vector2, sc: float) -> Sprite2D:
	var sprite := Sprite2D.new(); sprite.texture = tex; sprite.centered = false
	sprite.position = at; sprite.scale = Vector2.ONE * sc
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	return sprite

## Warm dust motes drifting on the wind around the character, in world space so they stay put as the camera moves.
func _dust() -> CPUParticles2D:
	var dust := CPUParticles2D.new(); dust.name = "Dust"
	dust.amount = 70; dust.lifetime = 10.0; dust.preprocess = 10.0
	dust.local_coords = false; dust.use_fixed_seed = true; dust.seed = 7
	dust.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE; dust.emission_rect_extents = Vector2(1150, 560)
	dust.position = Vector2(0, -420)
	dust.direction = Vector2(1, -0.15); dust.spread = 25.0; dust.gravity = Vector2.ZERO
	dust.initial_velocity_min = 6.0; dust.initial_velocity_max = 22.0
	dust.scale_amount_min = 1.5; dust.scale_amount_max = 3.5
	var ramp := Gradient.new()
	ramp.offsets = PackedFloat32Array([0.0, 0.2, 0.8, 1.0])
	ramp.colors = PackedColorArray([Color(1, 0.9, 0.7, 0), Color(1, 0.9, 0.7, 0.55), Color(1, 0.9, 0.7, 0.55), Color(1, 0.9, 0.7, 0)])
	dust.color_ramp = ramp
	dust.z_index = 5
	return dust

## The character inside a CanvasGroup that outlines and rim-lights the whole silhouette.
func attach_character(player: Node) -> void:
	super.attach_character(player)
	player.add_child(_dust())
	var group := CanvasGroup.new(); group.name = "CharacterOutline"
	group.fit_margin = 10.0; group.clear_margin = 10.0
	var mat := ShaderMaterial.new(); mat.shader = OUTLINE; group.material = mat
	player.add_child(group)
	for child in player.get_children():
		if child is RigCharacter2D or child.name in ["StandIn"]: child.reparent(group, false)

func _wall_tiles() -> Array:
	return [wall_tile] + wall_tile_variants

## A stable pseudo-random pick per block, so neighbouring blocks rarely repeat and every run looks the same.
static func _pick(tiles: Array, block: Vector2i) -> Texture2D:
	var h := (block.x * 73856093) ^ (block.y * 19349663)
	return tiles[posmod(h, tiles.size())]
