class_name GreyboxArt3D
extends Resource
## Greybox visuals for the 3D lane: toon-shaded unit cubes per kind, crystal lights on tagged cells, a desert
## environment and a STAND-IN capsule for the character. KitArt3D subclasses it once the desert kit exists. THROWAWAY.
## Colors match tools/greybox (Task 1); sky, sand and crystal colors come from docs/bakeoff/desert-biome-brief.md.
const COLORS := {
	"empty": Color8(245, 240, 230), "solid": Color8(90, 80, 70), "wall_red": Color8(200, 60, 50), "wall_green": Color8(60, 170, 90),
	"platform_red": Color8(230, 120, 110), "platform_green": Color8(120, 210, 150), "start": Color8(40, 120, 220), "goal": Color8(240, 200, 40),
	"orb_red": Color8(255, 30, 30), "orb_green": Color8(30, 220, 80), "hazard": Color8(20, 20, 20),
}
const CRYSTAL := {"red": Color("#e04a3a"), "green": Color("#3fbf6a")}
const GRAY := Color(0.55, 0.55, 0.55)
const SAND := Color("#d9b27c")
const SKY_TOP := Color("#3f7f8c")
const SKY_HORIZON := Color("#f2c49b")
const SHADOW_VIOLET := Color("#5a4a7a")
const STAND_IN := Color("#7a4fb8")

## One material per untagged kind, shared by every cube of that kind.
var _materials := {}

## A tagged cell's cube and crystal light: gray and dark until its color is acquired, its color with a soft light
## once acquired, emissive with a pulsing bright light while active.
class TaggedBox extends MeshInstance3D:
	var base: Color
	var material: StandardMaterial3D
	var light: OmniLight3D
	var pulse: Tween
	func set_resonance_look(revealed: bool, active: bool) -> void:
		material.albedo_color = base if revealed else GRAY
		material.emission_enabled = active
		if pulse: pulse.kill(); pulse = null
		light.light_energy = 2.0 if active else 0.6 if revealed else 0.0
		if active:
			pulse = create_tween().set_loops()
			pulse.tween_property(light, "light_energy", 1.2, 0.5).set_trans(Tween.TRANS_SINE)
			pulse.tween_property(light, "light_energy", 2.0, 0.5).set_trans(Tween.TRANS_SINE)

## Keeps the environment's saturation adjustment on Resonance.world_saturation() (mechanic.md, Reveal).
class SaturatedEnvironment extends WorldEnvironment:
	func _ready() -> void:
		Resonance.changed.connect(_apply); _apply()
	func _apply() -> void:
		environment.adjustment_saturation = Resonance.world_saturation()

static func toon(color: Color) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON; mat.specular_mode = BaseMaterial3D.SPECULAR_TOON
	return mat

func make_cell(kind: String, _cell: Vector2i) -> Node3D:
	if Greybox.TAGGED.has(kind):
		var color: String = Greybox.TAGGED[kind][0]
		var tagged := TaggedBox.new(); tagged.base = COLORS[kind]
		var box := BoxMesh.new(); box.size = Vector3.ONE; tagged.mesh = box
		tagged.material = toon(GRAY); tagged.material.emission = CRYSTAL[color]; tagged.material.emission_energy_multiplier = 0.6
		tagged.material_override = tagged.material
		tagged.light = OmniLight3D.new(); tagged.light.name = "Crystal"
		tagged.light.light_color = CRYSTAL[color]; tagged.light.omni_range = 4.0; tagged.light.light_energy = 0.0
		tagged.light.position.z = 0.9  # in front of the cube, so it lights the player's plane rather than the cube's inside
		tagged.add_child(tagged.light)
		return tagged
	var inst := MeshInstance3D.new()
	match kind:
		"orb_red", "orb_green":
			var sphere := SphereMesh.new(); sphere.radius = 0.3; sphere.height = 0.6; inst.mesh = sphere
		"goal":
			var gate := CylinderMesh.new(); gate.top_radius = 0.35; gate.bottom_radius = 0.35; gate.height = 1.0; inst.mesh = gate
		"hazard":
			var spikes := PrismMesh.new(); spikes.size = Vector3(1.0, 0.6, 0.8); inst.mesh = spikes; inst.position.y = -0.2
		_:
			var box := BoxMesh.new(); box.size = Vector3.ONE; inst.mesh = box
	if not _materials.has(kind):
		var mat := toon(COLORS[kind])
		if kind in ["orb_red", "orb_green", "goal"]: mat.emission_enabled = true; mat.emission = COLORS[kind]
		_materials[kind] = mat
	inst.material_override = _materials[kind]
	return inst

func make_backdrop(level: Greybox) -> Node3D:
	var holder := Node3D.new(); holder.name = "Backdrop"
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = SKY_TOP; sky_mat.sky_horizon_color = SKY_HORIZON
	sky_mat.ground_horizon_color = SKY_HORIZON; sky_mat.ground_bottom_color = SAND
	var sky := Sky.new(); sky.sky_material = sky_mat
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY; env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; env.ambient_light_color = SHADOW_VIOLET  # violet shadows (brief)
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.adjustment_enabled = true
	var world_env := SaturatedEnvironment.new(); world_env.name = "Environment"; world_env.environment = env
	holder.add_child(world_env)
	var sun := DirectionalLight3D.new(); sun.name = "Sun"
	sun.light_color = Color("#ffd9a8"); sun.rotation_degrees = Vector3(-50, 30, 0); sun.shadow_enabled = true
	holder.add_child(sun)
	var ground := MeshInstance3D.new(); ground.name = "Sand"
	var plane := PlaneMesh.new(); plane.size = Vector2(level.width + 80, 60); ground.mesh = plane
	ground.position = Vector3(level.width / 2.0, 0, -20)
	ground.material_override = toon(SAND)
	holder.add_child(ground)
	return holder

func attach_character(player: Node) -> void:
	var capsule := MeshInstance3D.new(); capsule.name = "StandIn"
	var mesh := CapsuleMesh.new(); mesh.radius = 0.4; mesh.height = 1.6; capsule.mesh = mesh
	capsule.position.y = 0.8  # feet at the origin
	capsule.material_override = toon(STAND_IN)
	player.add_child(capsule)
	var label := Label3D.new(); label.name = "StandInLabel"; label.text = "STAND-IN"
	label.position.y = 2.0; label.font_size = 64; label.pixel_size = 0.01; label.billboard = BaseMaterial3D.BILLBOARD_ENABLED; label.modulate = Color.BLACK; label.outline_modulate = Color.WHITE
	player.add_child(label)
