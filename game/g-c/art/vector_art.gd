class_name VectorArt
extends PaintedArt
## Flat-vector desert visuals for lane G-C (docs/bakeoff/desert-biome-brief.md, SVG kit): PaintedArt's slots filled with
## hand-written SVGs (art/*.svg) that Godot rasterizes at their viewBox size, placed as PaintedArt places them, plus:
## wall and ground tiles drawn from several variants picked per block, pits that darken toward the spikes, and sky and
## rock filling the strips the camera shows above and below the level; tag colours locked by art/reveal.gdshader, with
## chevrons on red and waves on green; and the character drawn through art/character_outline.gdshader (dark outline,
## warm sun-side rim, hardened alpha fringe). The character is GreyboxArt's: the rig in protagonist/ once it is there,
## else the STAND-IN. THROWAWAY.
## Extra wall-tile and ground-tile variants; each keeps the band heights where blocks meet, so any mix is seamless.
@export var wall_tile_variants: Array[Texture2D] = []
@export var ground_tile_variants: Array[Texture2D] = []
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
	return holder

func make_cell(kind: String, cell: Vector2i, ts: float) -> Node2D:
	match kind:
		"solid":
			if _level.kind_at(cell.x, cell.y - 1) == "solid":
				return _tile(Sprite2D.new(), _pick(_wall_tiles(), Vector2i(floori(cell.x / 4.0), floori(cell.y / 4.0))), cell, ts, 4, false)
			if cell.y == _ground_row:
				return _tile(Sprite2D.new(), _pick([ground_tile] + ground_tile_variants, Vector2i(floori(cell.x / 2.0), 0)), cell, ts, 2, true)
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

## The character inside a CanvasGroup that outlines and rim-lights the whole silhouette.
func attach_character(player: Node) -> void:
	super.attach_character(player)
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
