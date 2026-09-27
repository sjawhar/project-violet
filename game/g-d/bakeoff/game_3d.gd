class_name Game3D
extends Node3D
## The playable level in 3D: environment, world, player, follow camera, restart/quit. THROWAWAY.
## World saturation (mechanic.md, Reveal) is the environment's adjustment_saturation, set by GreyboxArt3D's backdrop.
@export var level_path := "res://levels/level01.greybox.json"
@export var art: GreyboxArt3D
## Camera offset from the rig and its vertical field of view: at 32 m with fov 30 the frame spans about 30 x 17 m,
## the whole 16 m level height (mechanic.md, Controls).
const CAMERA_OFFSET := Vector3(0, 2.5, 32)
const CAMERA_FOV := 30.0
## Half the visible width: the rig's x stays in [HALF_VIEW, width - HALF_VIEW], so the frame never leaves the level.
const HALF_VIEW := 15.0
var level: Greybox
var player: Player3D
var start := Vector3.ZERO
var camera_rig: Node3D

func _ready() -> void:
	Resonance.reset()
	level = Greybox.load_file(level_path)
	if art == null: art = GreyboxArt3D.new()
	add_child(art.make_backdrop(level))
	var world := Node3D.new(); world.name = "World"; add_child(world)
	var info := GreyboxBuilder3D.build(level, world, art)
	start = info["start"]
	player = Player3D.new(); player.name = "Player"; player.level_height = level.height; player.position = start; add_child(player)
	for group in ["goal", "orb_red", "orb_green", "hazard"]:
		for area: Area3D in get_tree().get_nodes_in_group(group):
			if is_ancestor_of(area): area.body_entered.connect(func(b: Node3D): if b == player: player.on_area(area))
	art.attach_character(player)
	camera_rig = Node3D.new(); camera_rig.name = "CameraRig"; add_child(camera_rig)
	var camera := Camera3D.new(); camera.name = "Camera"; camera.fov = CAMERA_FOV; camera.position = CAMERA_OFFSET
	camera_rig.add_child(camera)
	_follow()
	camera.look_at(camera_rig.global_position)
	player.reached_goal.connect(_on_goal)
	# Play resets to the start with colors kept (mechanic.md). Deferred so a replay runner still sees where the hazard was.
	player.touched_hazard.connect(_respawn, CONNECT_DEFERRED)

func _process(_delta: float) -> void:
	_follow()

## The rig tracks the player's x, clamped to the level, at the level's mid-height; the camera looks at the rig.
func _follow() -> void:
	camera_rig.position = Vector3(clampf(player.position.x, HALF_VIEW, level.width - HALF_VIEW), level.height / 2.0, 0)

func _on_goal() -> void:
	if has_node("GoalLayer"): return
	var layer := CanvasLayer.new(); layer.name = "GoalLayer"; layer.layer = 2
	var label := Label.new(); label.text = "GOAL — R to restart"; label.position = Vector2(860, 480)
	label.add_theme_font_size_override("font_size", 48)
	layer.add_child(label); add_child(layer)

func _respawn() -> void:
	player.position = start; player.velocity = Vector3.ZERO; player.dash_ticks_left = 0; player.died = false

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("restart"): get_tree().reload_current_scene()
	elif event.is_action_pressed("quit"): get_tree().quit()
