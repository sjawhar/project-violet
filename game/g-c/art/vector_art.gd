class_name VectorArt
extends PaintedArt
## Flat-vector desert visuals for lane G-C (docs/bakeoff/desert-biome-brief.md, SVG kit): PaintedArt's slots filled with
## hand-written SVGs (art/*.svg) that Godot rasterizes at their viewBox size, placed as PaintedArt places them, plus:
## wall and ground tiles drawn from several variants picked per block, pits that darken toward the spikes, sky and
## rock filling the strips the camera shows above and below the level, and foreground light from the low sun on the
## left: warm block tops and sunward edges, shaded far faces, deeper rock darker, a feathered shadow cast right from each
## far face onto the backdrop, haze between the dunes and the playfield, and a contact shadow under the character when grounded. The character is GreyboxArt's: the rig in
## protagonist/ once it is there, else the STAND-IN. THROWAWAY.
## Extra wall-tile and ground-tile variants; each keeps the band heights where blocks meet, so any mix is seamless.
@export var wall_tile_variants: Array[Texture2D] = []
@export var ground_tile_variants: Array[Texture2D] = []
## The top colour of backdrop-far.svg's sky gradient, used above the level.
const SKY_TOP := Color("#2e6d7e")
## How far the pit darkening reaches above a hazard cell, in cells.
const PIT_SHADE_CELLS := 2.0
const SUN_WARM := Color("#ffd49a")
const SHADE := Color("#3b2f55")
## How far the shadow a block's far (right) face casts onto the backdrop reaches, in pixels.
const CAST_SHADOW_PX := 44.0

## A soft ellipse under the character's feet, shown only while it stands on the floor.
class FootShadow extends Polygon2D:
	var player: CharacterBody2D
	func _process(_delta: float) -> void:
		visible = player.is_on_floor()

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
	holder.add_child(_haze(level))
	return holder

## Depth haze over the backdrop layers, thickening toward the playfield so the dunes sit behind the level.
func _haze(level: Greybox) -> TextureRect:
	var ts := float(level.tile_px)
	var grad := Gradient.new()
	grad.offsets = PackedFloat32Array([0.0, 0.55, 1.0])
	grad.colors = PackedColorArray([Color("#f2c49b", 0.0), Color("#eab89a", 0.22), Color("#d9a7a4", 0.38)])
	var tex := GradientTexture2D.new(); tex.gradient = grad
	tex.fill_from = Vector2(0, 0); tex.fill_to = Vector2(0, 1); tex.width = 4; tex.height = 256
	var rect := TextureRect.new(); rect.name = "Haze"; rect.texture = tex
	rect.stretch_mode = TextureRect.STRETCH_SCALE
	rect.position = Vector2(-ts, 7.0 * ts); rect.size = Vector2((level.width + 2) * ts, (level.height - 7.0) * ts)
	return rect

func attach_character(player: Node) -> void:
	super.attach_character(player)
	var shadow := FootShadow.new(); shadow.name = "FootShadow"; shadow.player = player
	var points := PackedVector2Array()
	for i in 24:
		var a := TAU * i / 24.0
		points.append(Vector2(8.0 + cos(a) * 30.0, sin(a) * 5.0))
	shadow.polygon = points; shadow.color = Color(SHADE, 0.45); shadow.z_index = -1
	player.add_child(shadow)

func make_cell(kind: String, cell: Vector2i, ts: float) -> Node2D:
	match kind:
		"solid":
			var tile: Sprite2D
			if _level.kind_at(cell.x, cell.y - 1) == "solid":
				tile = _tile(Sprite2D.new(), _pick(_wall_tiles(), Vector2i(floori(cell.x / 4.0), floori(cell.y / 4.0))), cell, ts, 4, false)
			elif cell.y == _ground_row:
				tile = _tile(Sprite2D.new(), _pick([ground_tile] + ground_tile_variants, Vector2i(floori(cell.x / 2.0), 0)), cell, ts, 2, true)
			else:
				tile = super.make_cell(kind, cell, ts) as Sprite2D
			return _lit(tile, cell, ts)
		"hazard":
			var pit := super.make_cell(kind, cell, ts)
			var shade := Polygon2D.new(); shade.name = "PitShade"
			var h := ts / 2.0; var top := -h - PIT_SHADE_CELLS * ts
			shade.polygon = PackedVector2Array([Vector2(-h, top), Vector2(h, top), Vector2(h, -h), Vector2(-h, -h)])
			var clear := Color(HAZARD, 0.0); var dark := Color(HAZARD, 0.9)
			shade.vertex_colors = PackedColorArray([clear, clear, dark, dark])
			pit.add_child(shade)
			return pit
	return super.make_cell(kind, cell, ts)

## A solid cell's tile with the low sun's light on it: deeper rock darker, a warm top where it is open to the sky, a warm
## rim on the sunward (left) face and shade on the far (right) face where those face open air.
func _lit(tile: Sprite2D, cell: Vector2i, ts: float) -> Node2D:
	var holder := Node2D.new(); holder.add_child(tile)
	var h := ts / 2.0
	var depth := 0
	while _level.kind_at(cell.x, cell.y - depth - 1) == "solid" and depth < 16: depth += 1
	if depth > 0:
		var top_a := minf(0.05 * depth, 0.3); var bottom_a := minf(0.05 * (depth + 1), 0.3)
		holder.add_child(_gradient_quad(Rect2(-h, -h, ts, ts), Color(SHADE, top_a), Color(SHADE, bottom_a), true))
	if not _is_block(cell + Vector2i.UP):
		holder.add_child(_gradient_quad(Rect2(-h, -h, ts, 10.0), Color(SUN_WARM, 0.45), Color(SUN_WARM, 0.0), true))
	if not _is_block(cell + Vector2i.LEFT):
		holder.add_child(_gradient_quad(Rect2(-h, -h, 7.0, ts), Color(SUN_WARM, 0.4), Color(SUN_WARM, 0.0), false))
	if not _is_block(cell + Vector2i.RIGHT):
		holder.add_child(_gradient_quad(Rect2(h - 22.0, -h, 22.0, ts), Color(SHADE, 0.0), Color(SHADE, 0.38), false))
		# the low sun on the left throws the block's shadow right, onto the backdrop behind the open air
		holder.add_child(_gradient_quad(Rect2(h, -h, CAST_SHADOW_PX, ts), Color(SHADE, 0.3), Color(SHADE, 0.0), false))
	return holder

func _is_block(cell: Vector2i) -> bool:
	var kind := _level.kind_at(cell.x, cell.y)
	return kind == "solid" or Greybox.TAGGED.has(kind)

## A rectangle shaded from colour A to colour B, top to bottom (vertical) or left to right.
static func _gradient_quad(r: Rect2, a: Color, b: Color, vertical: bool) -> Polygon2D:
	var quad := Polygon2D.new()
	quad.polygon = PackedVector2Array([r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y)])
	quad.vertex_colors = PackedColorArray([a, a, b, b] if vertical else [a, b, b, a])
	return quad

func _wall_tiles() -> Array:
	return [wall_tile] + wall_tile_variants

## A stable pseudo-random pick per block, so neighbouring blocks rarely repeat and every run looks the same.
static func _pick(tiles: Array, block: Vector2i) -> Texture2D:
	var h := (block.x * 73856093) ^ (block.y * 19349663)
	return tiles[posmod(h, tiles.size())]
