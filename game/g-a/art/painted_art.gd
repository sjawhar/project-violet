class_name PaintedArt
extends GreyboxArt
## Painted desert visuals (docs/bakeoff/desert-biome-brief.md): generated tiles and sprites, the tag reveal shader,
## three parallax backdrop layers. The character is GreyboxArt's: the painted sprites once they are in the project, else the STAND-IN.
## THROWAWAY.
@export var rock_face: Texture2D
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
const SPIKES := preload("res://art/spikes.gdshader")
const SHADOW := Color("#211728")
const HAZE := Color("#f2c49b")
const CHASM := Color("#1c1320")
const PIT_LIP := Color("#8a5a3e")
## Kinds that leave a terrain cell's side open (drawn as broken rock with a contact shadow). Tagged and hazard cells
## are drawn edge to edge, so a terrain cell beside them keeps a straight side.
const OPEN_KINDS := ["empty", "start", "goal", "orb_red", "orb_green"]
## Set by make_backdrop, which Game2D calls before it builds the cells: solid tiles depend on their neighbours.
var _level: Greybox
var _ground_row := -1
## Per cell, its distance under the open air that lights it (see _distance_to_air); the terrain shader darkens with it.
var _air: PackedFloat32Array

## A tagged cell's wall or platform, painted neutral gray: gray until its color is acquired, tinted once acquired,
## glowing and pulsing while active.
class RevealSprite extends Sprite2D:
	var _pulse: Tween
	var halo: Node2D  ## the light an active piece throws onto the backdrop beside it; hidden otherwise
	func set_resonance_look(revealed: bool, active: bool) -> void:
		var mat := material as ShaderMaterial
		mat.set_shader_parameter("saturation", 1.0 if revealed else 0.0)
		mat.set_shader_parameter("glow", 0.35 if active else 0.0)
		if halo: halo.visible = active; halo.modulate.a = 1.0
		if _pulse: _pulse.kill(); _pulse = null
		if active:
			var set_glow := func(g: float):
				mat.set_shader_parameter("glow", g)
				if halo: halo.modulate.a = 0.55 + g
			_pulse = create_tween().set_loops().set_trans(Tween.TRANS_SINE)
			_pulse.tween_method(set_glow, 0.35, 0.1, 0.7)
			_pulse.tween_method(set_glow, 0.1, 0.35, 0.7)

## Violet as GreyboxArt attaches her, wrapped in a CanvasGroup whose shader grades her whole silhouette darker and
## cooler and rim-lights its sun side (art/character_light.gdshader), plus a soft shadow under her feet while she
## stands on something.
func attach_character(player: Node) -> void:
	super.attach_character(player)
	var character := player.get_node_or_null("Character")
	if character == null: return  # the STAND-IN capsule: nothing to light
	var group := CanvasGroup.new(); group.name = "CharacterLight"; group.fit_margin = 8.0
	var mat := ShaderMaterial.new(); mat.shader = CHARACTER_LIGHT; group.material = mat
	player.add_child(FootShadow.new())  # before her, so it draws under her and over the ground
	player.remove_child(character); group.add_child(character); player.add_child(group)

## A soft ellipse at the player's feet, shown while the player is on the floor.
class FootShadow extends Polygon2D:
	func _ready() -> void:
		name = "FootShadow"
		var points := PackedVector2Array(); var colors := PackedColorArray()
		points.append(Vector2.ZERO); colors.append(Color(SHADOW, 0.55))
		for i in 25:
			var a := TAU * i / 24.0
			points.append(Vector2(cos(a) * 34.0, sin(a) * 7.0)); colors.append(Color(SHADOW, 0.0))
		polygon = points; vertex_colors = colors
		var fan: Array = []
		for i in 24: fan.append(PackedInt32Array([0, i + 1, i + 2]))
		polygons = fan
	func _process(_delta: float) -> void:
		visible = (get_parent() as Player2D).is_on_floor()

func make_backdrop(level: Greybox) -> Node2D:
	_level = level
	_ground_row = _most_common_top_row(level)
	_air = _distance_to_air(level, _ground_row)
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
	# Warm haze thickening toward the ground line: the mesas and what shows down the pits fade into the air.
	var haze := Polygon2D.new(); haze.name = "Haze"
	var w := float(level.width * level.tile_px); var ground := float(_ground_row * level.tile_px)
	var top := ground - 4.0 * level.tile_px; var bottom := float(level.height * level.tile_px)
	haze.polygon = PackedVector2Array([Vector2(0, top), Vector2(w, top), Vector2(w, ground), Vector2(0, ground), Vector2(0, bottom), Vector2(w, bottom)])
	haze.polygons = [PackedInt32Array([0, 1, 2, 3]), PackedInt32Array([3, 2, 5, 4])]
	haze.vertex_colors = PackedColorArray([Color(HAZE, 0.0), Color(HAZE, 0.0), Color(HAZE, 0.42), Color(HAZE, 0.42), Color(HAZE, 0.62), Color(HAZE, 0.62)])
	holder.add_child(haze)
	return holder

func make_cell(kind: String, cell: Vector2i, ts: float) -> Node2D:
	if Greybox.TAGGED.has(kind):
		var color: String = Greybox.TAGGED[kind][0]
		var is_wall: bool = Greybox.TAGGED[kind][1] == "wall"
		var tagged := RevealSprite.new()
		var mat := ShaderMaterial.new(); mat.shader = REVEAL; mat.set_shader_parameter("tint", TINTS[color])
		mat.set_shader_parameter("vertical", is_wall)
		mat.set_shader_parameter("base", float(_level.kind_at(cell.x, cell.y + 1) == "solid"))
		mat.set_shader_parameter("cell", Vector2(cell))
		mat.set_shader_parameter("rock_face", rock_face)
		mat.set_shader_parameter("ends", Vector4(float(_level.kind_at(cell.x - 1, cell.y) != kind), float(_level.kind_at(cell.x, cell.y - 1) != kind),
			float(_level.kind_at(cell.x + 1, cell.y) != kind), float(_level.kind_at(cell.x, cell.y + 1) != kind)))
		tagged.material = mat
		if is_wall: _tile(tagged, tag_wall, cell, ts, 4, false)
		else: _tile(tagged, tag_platform, cell, ts, 2, true)  # the slab top on every cell
		mat.set_shader_parameter("side", tagged.region_rect.size.x)
		# The halo hangs off the sprite (ResonanceTag looks for set_resonance_look on the body's direct children),
		# scaled back to cell pixels.
		var broken_top := is_wall and _level.kind_at(cell.x, cell.y - 1) != kind  # the column's broken top: no halo above it
		tagged.halo = _halo(TINTS[color], is_wall, ts, broken_top); tagged.halo.visible = false
		tagged.halo.scale = Vector2.ONE / tagged.scale
		tagged.add_child(tagged.halo)
		return tagged
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
		"hazard":
			return _chasm(cell, ts)
	assert(false, "PaintedArt: no visual for %s" % kind)
	return null

## Two soft strips of the piece's colour, added onto the backdrop either side of a wall cell (above and below a
## platform cell): bright at the piece's worn edge and easing out within half a cell. Each strip spans exactly its own
## cell, so a column's strips meet without overlapping; on a column's broken top cell they start below the break.
static func _halo(color: Color, is_wall: bool, ts: float, broken_top: bool) -> Node2D:
	var holder := Node2D.new(); holder.z_index = -1
	var add := CanvasItemMaterial.new(); add.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	var h := ts / 2.0; var mid := ts * 0.12; var reach := ts * 0.42
	var top := ts * 0.1 if broken_top else -h  # below the deepest part of a broken top, so no glow hangs over the break
	for sgn: float in [-1.0, 1.0]:
		var strip := Polygon2D.new(); strip.material = add
		# three bands out from the piece's edge (0, mid, reach): a tight bright rim that eases out, not a flat band
		var d := [h - ts * 0.08, h + mid, h + reach]
		var pts := PackedVector2Array()
		for i in 3: pts.append(Vector2(sgn * d[i], top) if is_wall else Vector2(-h, sgn * d[i]))
		for i in [2, 1, 0]: pts.append(Vector2(sgn * d[i], h) if is_wall else Vector2(h, sgn * d[i]))
		strip.polygon = pts
		strip.polygons = [PackedInt32Array([0, 1, 4, 5]), PackedInt32Array([1, 2, 3, 4])]
		var a := [Color(color, 0.42), Color(color, 0.14), Color(color, 0.0)]
		strip.vertex_colors = PackedColorArray([a[0], a[1], a[2], a[2], a[1], a[0]])
		holder.add_child(strip)
	return holder

## A hazard cell and the open column above it, painted as a chasm: the column darkens from the pit's rim down into
## shadow (so the backdrop fades out instead of showing as a window), a ragged rock wall slants in from each end of
## the pit, and the spikes on the floor vary in size and catch the warm light at their tips.
func _chasm(cell: Vector2i, ts: float) -> Node2D:
	var holder := Node2D.new()
	var rim := _rim_row(cell)
	var top := (rim - cell.y) * ts - ts / 2.0            # the rim's y, relative to this hazard cell's centre
	var bottom := ts / 2.0; var depth := bottom - top; var h := ts / 2.0
	var fill := Polygon2D.new(); fill.z_index = -1
	var ys: Array[float] = [top, top + depth * 0.35, top + depth * 0.7, bottom]
	var alphas: Array[float] = [0.0, 0.62, 0.9, 1.0]
	var pts := PackedVector2Array(); var cols := PackedColorArray(); var quads: Array = []
	# At an end of the pit the fill runs on under the rock beside it, so the rock's eroded edge shows chasm, not sky.
	var left := -h - (ts * 0.4 if _level.kind_at(cell.x - 1, cell.y) == "solid" else 0.0)
	var right := h + (ts * 0.4 if _level.kind_at(cell.x + 1, cell.y) == "solid" else 0.0)
	for i in 4:
		pts.append(Vector2(left, ys[i])); pts.append(Vector2(right, ys[i]))
		cols.append(Color(CHASM, alphas[i])); cols.append(Color(CHASM, alphas[i]))
		if i > 0: quads.append(PackedInt32Array([2 * i - 2, 2 * i - 1, 2 * i + 1, 2 * i]))
	fill.polygon = pts; fill.vertex_colors = cols; fill.polygons = quads
	holder.add_child(fill)
	for sgn: int in [-1, 1]:  # a wall slanting in from each end of the pit
		if _level.kind_at(cell.x + sgn, cell.y) != "solid": continue
		holder.add_child(_pit_wall(cell, float(sgn), top, bottom, ts))
	var rng := RandomNumberGenerator.new(); rng.seed = hash(cell)
	var spikes := Sprite2D.new(); spikes.texture = hazard_tile
	var mat := ShaderMaterial.new(); mat.shader = SPIKES; spikes.material = mat
	_fit(spikes, ts)
	var tall := rng.randf_range(0.75, 1.3)
	spikes.scale.y *= tall; spikes.position.y = h - h * tall  # grow or shrink from the pit floor
	spikes.flip_h = rng.randf() < 0.5
	holder.add_child(spikes)
	return holder

## The row of a pit's rim for the hazard cell CELL: the lower of the two walls' tops that bound its pit.
func _rim_row(cell: Vector2i) -> int:
	var rim := 0
	for sgn: int in [-1, 1]:
		var c := cell.x
		while _level.kind_at(c, cell.y) == "hazard": c += sgn
		var r := cell.y
		while r > 0 and _level.kind_at(c, r - 1) == "solid": r -= 1
		rim = maxi(rim, r)
	return rim

## A dark rock face inside the pit at one end: ragged, a lit lip at the rim, slanting further in as it goes down.
func _pit_wall(cell: Vector2i, sgn: float, top: float, bottom: float, ts: float) -> Polygon2D:
	var wall := Polygon2D.new(); wall.z_index = 1
	var rng := RandomNumberGenerator.new(); rng.seed = hash(cell) + 7
	var edge := sgn * (ts / 2.0 + 6.0)                     # starts just under the rock beside the pit (SGN points at it)
	var pts := PackedVector2Array([Vector2(edge, top + 2.0)]); var cols := PackedColorArray([Color(PIT_LIP, 1.0)])
	var steps := 8
	for i in steps + 1:
		var f := float(i) / steps
		var reach := lerpf(0.18, 0.6, f) * ts + rng.randf_range(-6.0, 6.0)
		pts.append(Vector2(sgn * ts / 2.0 - sgn * reach, lerpf(top, bottom, f)))
		cols.append(PIT_LIP.lerp(CHASM, smoothstep(0.0, 0.5, f)))
	pts.append(Vector2(edge, bottom)); cols.append(Color(CHASM, 1.0))
	wall.polygon = pts; wall.vertex_colors = cols
	return wall

## How far a surface cell's quad reaches above the cell, as a fraction of a cell: room for the sand crust's drifts
## and the dry grass (terrain.gdshader).
const LIP := 0.45

## A terrain cell: a quad drawn through the terrain shader (the rock-face painting in level space, eroded open sides,
## rounded open corners, a dark mass under a lit lip), plus a contact shadow on each open side.
func _terrain(cell: Vector2i, ts: float) -> Node2D:
	var covered := _level.kind_at(cell.x, cell.y - 1) == "solid"
	var h := ts / 2.0
	var quad := Polygon2D.new()
	var top := -h - (0.0 if covered else ts * LIP)  # a surface cell's quad reaches above it for the crust and grass
	quad.polygon = PackedVector2Array([Vector2(-h, top), Vector2(h, top), Vector2(h, h), Vector2(-h, h)])
	var open := Vector4(
		float(_level.kind_at(cell.x - 1, cell.y) in OPEN_KINDS), float(not covered),
		float(_level.kind_at(cell.x + 1, cell.y) in OPEN_KINDS), float(_level.kind_at(cell.x, cell.y + 1) in OPEN_KINDS))
	var mat := ShaderMaterial.new(); mat.shader = TERRAIN
	mat.set_shader_parameter("side", ts)
	mat.set_shader_parameter("rock_face", rock_face)
	mat.set_shader_parameter("open", open)
	mat.set_shader_parameter("cell", Vector2(cell))
	var foot := func(dx: int) -> float:  # a surface cell at the foot of rock, or a tagged wall, rising beside it
		var above: String = _level.kind_at(cell.x + dx, cell.y - 1)
		return float(not covered and _level.kind_at(cell.x + dx, cell.y) == "solid" and (above == "solid" or (Greybox.TAGGED.has(above) and Greybox.TAGGED[above][1] == "wall")))
	mat.set_shader_parameter("foot", Vector2(foot.call(-1), foot.call(1)))
	mat.set_shader_parameter("run", Vector2(_run(cell, -1), _run(cell, 1)))
	mat.set_shader_parameter("ground_y", float(_ground_row))
	mat.set_shader_parameter("raised", float(cell.y <= _ground_row and _column_top(cell.x) < _ground_row))
	mat.set_shader_parameter("air", Vector4(_corner_air(cell), _corner_air(cell + Vector2i(1, 0)),
		_corner_air(cell + Vector2i(0, 1)), _corner_air(cell + Vector2i(1, 1))))
	quad.material = mat
	var holder := Node2D.new()
	holder.add_child(quad)
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

## How many cells of rock lie between this cell and the open air beside it, in direction dx (0 when the neighbour is
## open), capped at 3: the shader lights the face toward the sunset and shades the far face from it.
func _run(cell: Vector2i, dx: int) -> float:
	for k in 3:
		var c := cell.x + dx * (k + 1)
		if c < 0 or c >= _level.width: return 3.0
		if _level.kind_at(c, cell.y) in OPEN_KINDS: return float(k)
	return 3.0

## The first row from the top that is not open in a column, so a mass rising above the ground line can be found.
func _column_top(c: int) -> int:
	for r in _level.height:
		if not _level.kind_at(c, r) in OPEN_KINDS: return r
	return _level.height

## The air distance at a cell corner (the corner at the cell's top-left): the mean over the rock cells around it,
## so the darkening runs smoothly across cell borders. Open cells are left out, so a mass is not lightened along its
## open sides: its value depends on depth under its top alone.
func _corner_air(corner: Vector2i) -> float:
	var total := 0.0; var n := 0
	for c: Vector2i in [corner + Vector2i(-1, -1), corner + Vector2i(0, -1), corner + Vector2i(-1, 0), corner]:
		if c.x >= 0 and c.y >= 0 and c.x < _level.width and c.y < _level.height and _level.kind_at(c.x, c.y) in OPEN_KINDS: continue
		total += _air_at(c); n += 1
	return total / n if n > 0 else 0.0

func _air_at(c: Vector2i) -> float:
	if c.x < 0 or c.y < 0 or c.x >= _level.width or c.y >= _level.height: return AIR_CAP  # beyond the level is deep rock
	return _air[c.y * _level.width + c.x]

## Per cell, how far it lies under the open air that lights it: its depth below the open cell straight above it,
## averaged with the rock cells beside it in the same row (open cells are left out), capped at AIR_CAP. Rock is lit
## from above, so a mass darkens steadily from its top down, the same across its whole width, and the ground under a
## narrow pillar darkens only softly. At and below the ground line a cell is never deeper than its depth under that
## line, so the ground under a raised block shades like the ground beside it and its bands line up.
const AIR_CAP := 5
static func _distance_to_air(level: Greybox, ground_row: int) -> PackedFloat32Array:
	var w := level.width; var h := level.height
	var straight := PackedFloat32Array(); straight.resize(w * h)
	for c in w:
		var depth := float(AIR_CAP)  # the level's top edge counts as deep rock
		for r in h:
			if level.kind_at(c, r) in OPEN_KINDS or Greybox.TAGGED.has(level.kind_at(c, r)): depth = 0.0; straight[r * w + c] = 0.0; continue  # a tagged wall standing on rock does not shade it
			depth = minf(depth + 1.0, AIR_CAP)
			if r >= ground_row: depth = minf(depth, float(r - ground_row + 1))
			straight[r * w + c] = depth
	var dist := PackedFloat32Array(); dist.resize(w * h)
	for r in h:
		for c in w:
			if level.kind_at(c, r) in OPEN_KINDS: dist[r * w + c] = 0.0; continue
			var total := 0.0; var n := 0
			for dc in [-1, 0, 1]:
				var cc: int = c + dc
				if cc < 0 or cc >= w or level.kind_at(cc, r) in OPEN_KINDS: continue
				total += straight[r * w + cc]; n += 1
			dist[r * w + c] = total / n
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
