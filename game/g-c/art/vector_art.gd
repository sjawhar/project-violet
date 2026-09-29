class_name VectorArt
extends PaintedArt
## Flat-vector desert visuals for lane G-C (docs/bakeoff/desert-biome-brief.md, SVG kit): PaintedArt's slots filled with
## hand-written SVGs (art/*.svg) that Godot rasterizes at their viewBox size, placed as PaintedArt places them, plus:
## wall and ground tiles drawn from several variants picked per block, pits that darken toward the spikes, and sky and
## rock filling the strips the camera shows above and below the level; tag colours locked by art/reveal.gdshader, with
## chevrons on red and waves on green; and the character drawn through art/character_outline.gdshader (dark outline,
## warm sun-side rim, hardened alpha fringe). The character is GreyboxArt's: the rig in protagonist/ once it is there,
## else the STAND-IN. Set dressing and atmosphere: soft light shafts from the sun on the far layer, dust motes drifting
## in the air, dry-grass tufts on some open block tops, and a dark foreground silhouette strip along the bottom of the
## frame on a faster parallax layer. THROWAWAY.
## Extra wall-tile and ground-tile variants; each keeps the band heights where blocks meet, so any mix is seamless.
@export var wall_tile_variants: Array[Texture2D] = []
@export var ground_tile_variants: Array[Texture2D] = []
## The dark near-plane silhouettes along the bottom of the frame, and the grass tuft set on block tops.
@export var foreground: Texture2D
@export var tuft: Texture2D
## Where backdrop-far.svg draws the sun, in its own pixels.
const SUN := Vector2(900, 660)
## The foreground strip's parallax: faster than the playfield, so it reads as nearer.
const FOREGROUND_SCROLL := 1.25
## The top colour of backdrop-far.svg's sky gradient, used above the level.
const SKY_TOP := Color("#2e6d7e")
## How far the pit darkening reaches above a hazard cell, in cells.
const PIT_SHADE_CELLS := 2.0
## art/reveal.gdshader's shape cue per tag colour.
const PATTERNS := {"red": 1, "green": 2}
const OUTLINE := preload("res://art/character_outline.gdshader")

func make_backdrop(level: Greybox) -> Node2D:
	var holder := super.make_backdrop(level)
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
	holder.add_child(_foreground(level))
	return holder

## Faint warm rays fanning up from the low sun, added on top of the far layer so they move with it.
func _light_shafts() -> Node2D:
	var rays := Node2D.new(); rays.name = "LightShafts"
	var mat := CanvasItemMaterial.new(); mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	for spec: Vector2 in [Vector2(-160, 9), Vector2(-136, 6), Vector2(-110, 10), Vector2(-82, 7), Vector2(-56, 9), Vector2(-32, 6)]:
		var a0 := deg_to_rad(spec.x - spec.y / 2.0); var a1 := deg_to_rad(spec.x + spec.y / 2.0); var am := deg_to_rad(spec.x)
		var ray := Polygon2D.new(); ray.material = mat
		# bright along the middle, fading to nothing at both edges and at the far end
		ray.polygon = PackedVector2Array([SUN, SUN + Vector2(cos(a0), sin(a0)) * 1500.0, SUN + Vector2(cos(am), sin(am)) * 1500.0, SUN + Vector2(cos(a1), sin(a1)) * 1500.0])
		var warm := Color(1.0, 0.86, 0.62, 0.0)
		ray.vertex_colors = PackedColorArray([Color(warm, 0.11), warm, Color(warm, 0.03), warm])
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
			if _level.kind_at(cell.x, cell.y - 1) == "solid":
				return _tile(Sprite2D.new(), _pick(_wall_tiles(), Vector2i(floori(cell.x / 4.0), floori(cell.y / 4.0))), cell, ts, 4, false)
			var surface: Sprite2D
			if cell.y == _ground_row:
				surface = _tile(Sprite2D.new(), _pick([ground_tile] + ground_tile_variants, Vector2i(floori(cell.x / 2.0), 0)), cell, ts, 2, true)
			else:
				surface = super.make_cell(kind, cell, ts) as Sprite2D
			return _with_tuft(surface, cell, ts)
		"hazard":
			var pit := super.make_cell(kind, cell, ts)
			var shade := Polygon2D.new(); shade.name = "PitShade"
			var h := ts / 2.0; var top := -h - PIT_SHADE_CELLS * ts
			shade.polygon = PackedVector2Array([Vector2(-h, top), Vector2(h, top), Vector2(h, -h), Vector2(-h, -h)])
			var clear := Color(HAZARD, 0.0); var dark := Color(HAZARD, 0.9)
			shade.vertex_colors = PackedColorArray([clear, clear, dark, dark])
			pit.add_child(shade)
			return pit
	var node := super.make_cell(kind, cell, ts)
	if Greybox.TAGGED.has(kind):
		(node.material as ShaderMaterial).set_shader_parameter("pattern", PATTERNS[Greybox.TAGGED[kind][0]])
	return node

## An open-topped block cell, with a grass tuft on about one cell in three (the same cells every run).
func _with_tuft(surface: Sprite2D, cell: Vector2i, ts: float) -> Node2D:
	var h := (cell.x * 2654435761) ^ (cell.y * 40503)
	if posmod(h, 3) != 0: return surface
	var holder := Node2D.new(); holder.add_child(surface)
	var grass := Sprite2D.new(); grass.texture = tuft; grass.centered = false
	var w := ts * 1.1
	grass.scale = Vector2.ONE * (w / tuft.get_width())
	grass.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	grass.position = Vector2(-w / 2.0 + float(posmod(h >> 3, 17) - 8), -ts / 2.0 - tuft.get_height() * grass.scale.y + 4.0)
	holder.add_child(grass)
	return holder

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
	group.fit_margin = 8.0; group.clear_margin = 8.0
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
