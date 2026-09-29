class_name KitArt3D
extends GreyboxArt3D
## Lane G-D's desert look: the agent-built 3D desert kit (res://kit/, copied from assets/bakeoff/desert-kit-3d/) on
## GreyboxArt3D's environment, lights and character. Art only: the builder still makes every collider. THROWAWAY.
## Kit conventions (kit/README.md): metres, +Y up, origin at the base centre, front toward +Z; `tag-block` and `orb`
## are untinted gray, so tagged cells and orbs are tinted here per docs/bakeoff/mechanic.md.
const KIT := "res://kit/%s.glb"
## Deterministic backdrop placement, so every capture shows the same desert.
const SEED := 20260927
const FAR := ["mesa-large", "mesa-small", "arch", "dune-ridge"]
const MID := ["boulder-a", "boulder-b", "ruin-column", "ruin-wall", "saguaro", "acacia"]
const NEAR := ["boulder-a", "boulder-b", "saguaro"]
## Backdrop props stay behind this plane, clear of the player's 1 m deep strip at z = 0.
const PROP_FRONT_Z := -1.5
## Parallax slides a prop a few metres against the level as the camera moves, so pit avoidance keeps this much clear.
const PIT_MARGIN := 2.0
## Tag block albedo before its color is acquired (mechanic.md: grayscale).
const TAG_GRAY := Color(0.6, 0.6, 0.6)
## Emission energy of an active tag block: enough to glow, low enough that ACES keeps its hue instead of going peach.
const TAG_GLOW := 0.15
## The tag-blocks keep the brief's colors (TAG_COLORS) and sit on visual layer TAG_BLOCK_LAYER. Their own lights, the
## warm sun and the fills skip that layer (lights 0.4 m from each face, 13 to a wall, overexposed the faces to peach, and
## the warm sun pushed red toward the orange sandstone); a neutral white key lights only the blocks, at an energy that
## renders them close to their own colors.
const TAG_BLOCK_LAYER := 2
const TAG_KEY_ENERGY := 0.6
## Violet is drawn this far in front of the play plane, just past the blocks' front faces, so she stays visible when she
## passes a wall of the active color; her feet still meet the front edge of the ground.
const CHARACTER_Z := 0.6
## A dark outline behind her, PAD metres wide, gives her a value break from sand, sky and mesa alike.
const OUTLINE_COLOR := Color("#241a33")
const OUTLINE_PAD := 0.05
## Tag lights at this share of GreyboxArt3D's: a 13-cell wall of full-energy lights washed its surroundings out.
const LIGHT_SCALE := 0.35
## Depth fog: the play plane, 32 m from the camera, stays clear, and the sand is fully fogged where it meets the sky.
const FOG_BEGIN := 34.0
const FOG_END := 190.0
## Aerial perspective per backdrop layer: each layer's materials are pulled this far toward HORIZON, so every layer is
## paler than the one in front of it and none competes with the play plane.
const HAZE_MID := 0.15
const HAZE_FAR := 0.35
const HAZE_HORIZON := 0.6
## A horizon layer of pale mesas and dunes 60-100 m behind the level fills the band between the play area and the
## clouds. It has its own random stream, so the nearer layers keep their placement.
const HORIZON_LAYER := ["mesa-large", "mesa-small", "arch", "dune-ridge"]
## The painted sky (art/sky.png, gen image) hangs on a quad this far back, behind the far end of the sand plane, and
## follows the camera on x: a sky at infinity. One copy spans the whole frame, stretched about 2x across.
## Its bottom rows are clear haze of HORIZON, which is also the fog color, so the fully fogged
## far sand meets the sky with no seam, and the sand hides the bottom 15% of the painting.
const SKY_TEXTURE := "res://art/sky.png"
const SKY_Z := -165.0
const SKY_SIZE := Vector2(200, 63)
const SKY_BOTTOM := -9.5
## Mean of sky.png's bottom 20 rows (ImageMagick), so fog and sky meet at the same color.
const HORIZON := Color8(252, 193, 119)
## Dark foreground silhouettes, between the camera and the play plane, frame the bottom of the shot (as Planet of Lana
## and INSIDE do). Their tops stay below this height on the play plane, under the 3 m walking surface.
const FOREGROUND_TOP := 2.2
const FOREGROUND_COLOR := Color("#3a2e4d")
const FOREGROUND := ["saguaro", "acacia"]
## Tile shading: each cell of rock under the surface is pulled this far toward shadow violet (up to three cells deep),
## so the strata darken with depth instead of repeating identically down a block.
const DEPTH_TINT := 0.08

var _scenes := {}
## Imported material -> its toon copy, shared by every instance of that piece.
var _toon := {}
## [orb kind, imported material] -> its tinted copy. Held here, not only by the orb: when a picked-up orb's material died
## with the orb, the headless (dummy) renderer logged 'Parameter "material" is null', which the export smoke run fails on.
var _orb_materials := {}
## [toon material, depth] -> its tile variant.
var _tile_materials := {}
## [toon material, haze] -> its hazed backdrop copy.
var _haze_materials := {}
## The level being dressed, kept by make_backdrop (called before the builder) so make_cell can see a cell's neighbours.
var _level: Greybox

## A tagged cell drawn as the kit's solid 1 m tag-block instead of GreyboxArt3D's box, keeping the box's light: gray
## until the color is acquired, the tag color once acquired, glowing while active. Emission stays enabled and only its
## energy moves, so no shader variant is compiled mid-game.
class KitTaggedBox extends GreyboxArt3D.TaggedBox:
	var tag_color: Color
	var block_materials: Array[StandardMaterial3D] = []
	func set_resonance_look(revealed: bool, active: bool) -> void:
		super(revealed, active)
		for mat in block_materials:
			mat.albedo_color = tag_color if revealed else TAG_GRAY
			mat.emission_energy_multiplier = TAG_GLOW if active else 0.0

## The painted sky quad: follows the camera on x.
class SkyLayer extends MeshInstance3D:
	func _process(_delta: float) -> void:
		position.x = get_viewport().get_camera_3d().global_position.x

## A bird: two dark wings that flap, flying across the sky and wrapping around the camera's view.
class Bird extends Node3D:
	var speed: float
	var phase: float
	var home: Vector3
	var wings: Array[Node3D] = []
	var t := 0.0
	func _process(delta: float) -> void:
		t += delta
		var cam_x := get_viewport().get_camera_3d().global_position.x
		position = Vector3(cam_x + fposmod(home.x + t * speed + 45.0, 90.0) - 45.0, home.y + sin(t * 0.7 + phase) * 0.6, home.z)
		var flap := sin(t * 6.0 + phase) * 30.0
		wings[0].rotation_degrees.z = 20.0 + flap
		wings[1].rotation_degrees.z = -20.0 - flap

## One outline sprite: the parent part's image, dark and unshaded, a little larger, behind every part of the character.
class OutlineSprite extends Sprite3D:
	var part: Sprite3D
	func _process(_delta: float) -> void:
		flip_h = part.flip_h
		var size := part.texture.get_size() * part.pixel_size * Vector2(absf(part.scale.x), absf(part.scale.y))
		scale = Vector3(1.0 + 2.0 * OUTLINE_PAD / maxf(size.x, 0.001), 1.0 + 2.0 * OUTLINE_PAD / maxf(size.y, 0.001), 1.0)

## An orb cell's visual. Picking the orb up frees its Area3D and everything under it, so once in the tree the pedestal
## moves up to the World node and only the floating orb stays with the area.
class OrbPedestal extends Node3D:
	var pedestal: Node3D
	func _ready() -> void:
		pedestal.reparent.call_deferred(get_parent().get_parent())

func _new_tagged_box() -> GreyboxArt3D.TaggedBox:
	return KitTaggedBox.new()

func make_cell(kind: String, cell: Vector2i) -> Node3D:
	match kind:
		"solid":
			# Sand where the cell is open above, layered rock beneath.
			var piece := "rock-tile" if _level.kind_at(cell.x, cell.y - 1) == "solid" else "sand-tile"
			return _vary_tile(_on_cell_floor(_piece(piece)), cell)
		"hazard":
			return _on_cell_floor(_piece("hazard-spikes"))
		"goal":
			return _on_cell_floor(_piece("goal-gate"))
		"orb_red", "orb_green":
			var holder := OrbPedestal.new(); holder.name = "OrbPedestal"
			var pedestal := _on_cell_floor(_piece("orb-pedestal")); pedestal.name = "Pedestal_%d_%d" % [cell.x, cell.y]
			var orb: Node3D = pedestal.find_child("orb", true, false)
			var orb_transform := pedestal.transform * _local_to(pedestal, orb)
			orb.owner = null; orb.reparent(holder, false); orb.transform = orb_transform
			var color := COLORS[kind] as Color
			for mi: MeshInstance3D in _meshes(orb):
				for s in mi.mesh.get_surface_count():
					var key := [kind, mi.get_active_material(s)]
					if not _orb_materials.has(key):
						var mat := (mi.get_active_material(s) as StandardMaterial3D).duplicate() as StandardMaterial3D
						mat.albedo_color = color; mat.emission_enabled = true; mat.emission = color; mat.emission_energy_multiplier = 1.5
						_orb_materials[key] = mat
					mi.set_surface_override_material(s, _orb_materials[key])
			holder.pedestal = pedestal; holder.add_child(pedestal)
			return holder
	var tagged := super.make_cell(kind, cell) as KitTaggedBox
	var color: String = Greybox.TAGGED[kind][0]
	tagged.mesh = null  # the tag-block is the visual; the box's light and look stay
	tagged.energy_scale = LIGHT_SCALE
	tagged.tag_color = TAG_COLORS[color]
	tagged.light.light_cull_mask &= ~(1 << (TAG_BLOCK_LAYER - 1))
	var block := _on_cell_floor(_piece("tag-block")); block.name = "TagBlock"
	for mi: MeshInstance3D in _meshes(block):
		mi.layers = 1 << (TAG_BLOCK_LAYER - 1)
		for s in mi.mesh.get_surface_count():
			var mat := (mi.get_active_material(s) as StandardMaterial3D).duplicate() as StandardMaterial3D
			mat.albedo_color = TAG_GRAY; mat.emission_enabled = true; mat.emission = TAG_COLORS[color]; mat.emission_energy_multiplier = 0.0
			tagged.block_materials.append(mat)
			mi.set_surface_override_material(s, mat)
	tagged.add_child(block)
	return tagged

## GreyboxArt3D's character, moved in front of the play plane and outlined.
func attach_character(player: Node) -> void:
	super.attach_character(player)
	var character := player.get_node("Character") as RigCharacter3D
	character.position.z = CHARACTER_Z
	for part: Sprite3D in character.find_children("*", "Sprite3D", false, false):
		var outline := OutlineSprite.new(); outline.name = "Outline"; outline.part = part
		outline.texture = part.texture; outline.pixel_size = part.pixel_size; outline.texture_filter = part.texture_filter
		outline.shaded = false; outline.modulate = OUTLINE_COLOR; outline.render_priority = -1
		outline.position.z = -0.05  # behind every part (they span 0-0.04 m)
		part.add_child(outline)

func make_backdrop(level: Greybox) -> Node3D:
	_level = level
	var holder := super.make_backdrop(level)
	var env := (holder.get_node("Environment") as WorldEnvironment).environment
	env.fog_enabled = true; env.fog_mode = Environment.FOG_MODE_DEPTH
	env.fog_light_color = HORIZON; env.fog_density = 1.0
	env.fog_depth_begin = FOG_BEGIN; env.fog_depth_end = FOG_END; env.fog_sky_affect = 0.0
	# The sand runs back to the sky quad, so its far edge is fully fogged to HORIZON where it meets the sky.
	var sand := holder.get_node("Sand") as MeshInstance3D
	(sand.mesh as PlaneMesh).size = Vector2(level.width + 600, 180)
	sand.position = Vector3(level.width / 2.0, 0, SKY_Z + 90.0)
	holder.add_child(_sky_layer())
	var tag_bit := 1 << (TAG_BLOCK_LAYER - 1)
	(holder.get_node("Sun") as DirectionalLight3D).light_cull_mask &= ~tag_bit
	var tag_key := DirectionalLight3D.new(); tag_key.name = "TagKey"
	tag_key.light_color = Color.WHITE; tag_key.light_energy = TAG_KEY_ENERGY; tag_key.light_cull_mask = tag_bit
	tag_key.rotation_degrees = Vector3(-50, 30, 0)
	holder.add_child(tag_key)
	_add_birds(holder)
	_add_fill_lights(holder)
	var props := Node3D.new(); props.name = "Props"; holder.add_child(props)
	var rng := RandomNumberGenerator.new(); rng.seed = SEED
	_scatter(props, rng, FAR, Vector2(-10, level.width + 10), Vector2(-12, -9), Vector2(-2, 6), Vector2(0.7, 1.0), 10.0, false, HAZE_FAR)
	_scatter(props, rng, MID, Vector2(-8, level.width + 8), Vector2(-8, -5), Vector2(3, 8), Vector2(0.7, 1.0), 25.0, true, HAZE_MID)
	_scatter(props, rng, NEAR, Vector2(-6, level.width + 6), Vector2(-3.5, -2.5), Vector2(6, 12), Vector2(0.8, 1.0), 25.0, true, 0.0)
	var horizon_rng := RandomNumberGenerator.new(); horizon_rng.seed = SEED + 1
	_scatter(props, horizon_rng, HORIZON_LAYER, Vector2(-60, level.width + 60), Vector2(-100, -60), Vector2(-5, 6), Vector2(0.7, 1.1), 180.0, false, HAZE_HORIZON)
	_add_foreground(holder, rng)
	return holder

func _sky_layer() -> SkyLayer:
	var sky := SkyLayer.new(); sky.name = "Sky"
	var quad := QuadMesh.new(); quad.size = SKY_SIZE; sky.mesh = quad
	sky.position = Vector3(0, SKY_BOTTOM + SKY_SIZE.y / 2.0, SKY_Z)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; mat.disable_fog = true
	mat.albedo_texture = load(SKY_TEXTURE)
	sky.material_override = mat
	return sky

func _add_birds(holder: Node3D) -> void:
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; mat.disable_fog = true; mat.albedo_color = Color("#4a3a5a")
	var wing_mesh := BoxMesh.new(); wing_mesh.size = Vector3(0.9, 0.08, 0.08)
	var flock := [Vector3(-20, 17, -35), Vector3(-17.5, 18.2, -35), Vector3(-15.5, 16.6, -35), Vector3(10, 19.5, -40), Vector3(12, 20.3, -40)]
	for i in flock.size():
		var bird := Bird.new(); bird.name = "Bird%d" % i
		bird.home = flock[i]; bird.speed = 2.2 + 0.15 * i; bird.phase = i * 1.3
		for side in [-1.0, 1.0]:
			var pivot := Node3D.new()
			var wing := MeshInstance3D.new(); wing.mesh = wing_mesh; wing.material_override = mat; wing.position.x = side * 0.45
			pivot.add_child(wing); bird.add_child(pivot); bird.wings.append(pivot)
		holder.add_child(bird)

## Two weak shadowless fills from either side of the camera, so the side faces of the pits and steps stop reading black.
func _add_fill_lights(holder: Node3D) -> void:
	for yaw in [-60.0, 60.0]:
		var fill := DirectionalLight3D.new(); fill.name = "Fill%d" % int(yaw)
		fill.light_color = Color("#e6d2e8"); fill.light_energy = 0.3; fill.shadow_enabled = false
		fill.rotation_degrees = Vector3(-15, yaw, 0)
		fill.light_cull_mask &= ~(1 << (TAG_BLOCK_LAYER - 1))
		holder.add_child(fill)

## Flat dark kit silhouettes at z 4.5-7, each scaled so its top stays below FOREGROUND_TOP on the play plane, and kept
## off the pits (the hazards must stay in view) with a margin for their stronger parallax.
func _add_foreground(holder: Node3D, rng: RandomNumberGenerator) -> void:
	var fg := Node3D.new(); fg.name = "Foreground"; holder.add_child(fg)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; mat.disable_fog = true; mat.albedo_color = FOREGROUND_COLOR
	var cam := Vector2(32.0, 10.5)  # the camera's distance from the play plane and its height (Game3D)
	var x := -12.0
	while x < _level.width + 12:
		var piece: String = FOREGROUND[rng.randi_range(0, FOREGROUND.size() - 1)]
		var inst := _piece(piece)
		var z := rng.randf_range(4.5, 7.0)
		var max_h := cam.y - (cam.y - FOREGROUND_TOP) * (cam.x - z) / cam.x
		var size := _aabb(inst).size
		var s := max_h / size.y * rng.randf_range(0.75, 1.0)
		inst.scale = Vector3.ONE * s
		inst.rotation_degrees.y = rng.randf_range(-40, 40)
		x += size.x * s / 2.0
		inst.position = Vector3(x, 0, z)
		for mi: MeshInstance3D in _meshes(inst):
			for i in mi.mesh.get_surface_count(): mi.set_surface_override_material(i, mat)
		if _over_ground(x - size.x * s / 2.0 - 2.0 * PIT_MARGIN, x + size.x * s / 2.0 + 2.0 * PIT_MARGIN): fg.add_child(inst)
		else: inst.free()
		x += size.x * s / 2.0 + rng.randf_range(1.0, 6.0)

## Darkens a tile toward shadow violet with its depth under the surface, and turns every other tile around, so
## neighbouring blocks stop showing identical strata.
func _vary_tile(inst: Node3D, cell: Vector2i) -> Node3D:
	var depth := 0
	while depth < 3 and _level.kind_at(cell.x, cell.y - depth - 1) == "solid": depth += 1
	if (cell.x + cell.y) % 2 == 1: inst.rotation_degrees.y = 180.0
	for mi: MeshInstance3D in _meshes(inst):
		for s in mi.mesh.get_surface_count():
			var base := mi.get_surface_override_material(s) as StandardMaterial3D
			var key := [base, depth]
			if not _tile_materials.has(key):
				var mat := base.duplicate() as StandardMaterial3D
				mat.albedo_color = base.albedo_color.lerp(SHADOW_VIOLET, DEPTH_TINT * depth)
				_tile_materials[key] = mat
			mi.set_surface_override_material(s, _tile_materials[key])
	return inst

## Places pieces left to right across x_range, each at a random depth in z_range (pulled back so its front stays behind
## PROP_FRONT_Z), with a random gap after it, a random uniform scale and a random yaw of up to yaw_deg. With avoid_pits,
## pieces are skipped where they would stand behind a pit: seen through the gap they read as ledges inside it. Every
## piece is hazed toward HORIZON by haze.
func _scatter(parent: Node3D, rng: RandomNumberGenerator, pieces: Array, x_range: Vector2, z_range: Vector2, gap: Vector2, scale_range: Vector2, yaw_deg: float, avoid_pits: bool, haze: float) -> void:
	var x := x_range.x
	while x < x_range.y:
		var piece: String = pieces[rng.randi_range(0, pieces.size() - 1)]
		var inst := _piece(piece)
		var s := rng.randf_range(scale_range.x, scale_range.y)
		var size := _aabb(inst).size * s
		inst.scale = Vector3.ONE * s
		inst.rotation_degrees.y = rng.randf_range(-yaw_deg, yaw_deg)
		x += size.x / 2.0
		inst.position = Vector3(x, 0, minf(rng.randf_range(z_range.x, z_range.y), PROP_FRONT_Z - size.z / 2.0))
		if not avoid_pits or _over_ground(x - size.x / 2.0 - PIT_MARGIN, x + size.x / 2.0 + PIT_MARGIN): parent.add_child(_haze(inst, haze))
		else: inst.free()
		x += size.x / 2.0 + rng.randf_range(gap.x, gap.y)

func _haze(inst: Node3D, haze: float) -> Node3D:
	if haze == 0.0: return inst
	for mi: MeshInstance3D in _meshes(inst):
		for s in mi.mesh.get_surface_count():
			var base := mi.get_surface_override_material(s) as StandardMaterial3D
			var key := [base, haze]
			if not _haze_materials.has(key):
				var mat := base.duplicate() as StandardMaterial3D
				mat.albedo_color = base.albedo_color.lerp(HORIZON, haze)
				if mat.emission_enabled: mat.emission = mat.emission.lerp(HORIZON, haze)
				_haze_materials[key] = mat
			mi.set_surface_override_material(s, _haze_materials[key])
	return inst

## True when every level column the span [x0, x1] covers (clamped to the level) has solid ground in the bottom row.
func _over_ground(x0: float, x1: float) -> bool:
	for c in range(maxi(floori(x0), 0), mini(ceili(x1), _level.width)):
		if _level.kind_at(c, _level.height - 1) != "solid": return false
	return true

## A kit piece, toon-shaded like the rest of the lane.
func _piece(piece: String) -> Node3D:
	if not _scenes.has(piece): _scenes[piece] = load(KIT % piece)
	var inst: Node3D = (_scenes[piece] as PackedScene).instantiate()
	for mi: MeshInstance3D in _meshes(inst):
		for s in mi.mesh.get_surface_count():
			var src := mi.get_active_material(s) as StandardMaterial3D
			if not _toon.has(src):
				var mat := src.duplicate() as StandardMaterial3D
				mat.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON; mat.specular_mode = BaseMaterial3D.SPECULAR_TOON
				_toon[src] = mat
			mi.set_surface_override_material(s, _toon[src])
	return inst

## Kit pieces stand on their base: a cell visual is centred on the cell, so it drops half a metre.
static func _on_cell_floor(inst: Node3D) -> Node3D:
	inst.position.y = -0.5
	return inst

static func _meshes(node: Node) -> Array[Node]:
	var out: Array[Node] = node.find_children("*", "MeshInstance3D", true, false)
	if node is MeshInstance3D: out.push_front(node)
	return out

## The piece's bounds in its own space, unscaled.
static func _aabb(inst: Node3D) -> AABB:
	var box := AABB()
	var first := true
	for mi: MeshInstance3D in _meshes(inst):
		var local := _local_to(inst, mi) * mi.get_aabb()
		box = local if first else box.merge(local)
		first = false
	return box

static func _local_to(root: Node3D, node: Node3D) -> Transform3D:
	var t := Transform3D.IDENTITY
	var n: Node = node
	while n != root:
		t = (n as Node3D).transform * t
		n = n.get_parent()
	return t
