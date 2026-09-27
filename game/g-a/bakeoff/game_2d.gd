class_name Game2D
extends Node2D
## The playable level: backdrop, world, player, camera, saturation post effect, restart/quit. THROWAWAY.
@export var level_path := "res://levels/level01.greybox.json"
@export var art: GreyboxArt
var level: Greybox
var player: Player2D
var start := Vector2.ZERO

func _ready() -> void:
	Resonance.reset()
	level = Greybox.load_file(level_path)
	if art == null: art = GreyboxArt.new()
	add_child(art.make_backdrop(level))
	var world := Node2D.new(); world.name = "World"; add_child(world)
	var info := GreyboxBuilder2D.build(level, world, art)
	start = info["start"]
	player = Player2D.new(); player.name = "Player"; player.position = start; add_child(player)
	for group in ["goal", "orb_red", "orb_green", "hazard"]:
		for area: Area2D in get_tree().get_nodes_in_group(group):
			if is_ancestor_of(area): area.body_entered.connect(func(b: Node2D): if b == player: player.on_area(area))
	art.attach_character(player)
	var camera := Camera2D.new(); camera.name = "Camera"
	camera.position_smoothing_enabled = false
	camera.limit_left = 0; camera.limit_top = 0
	camera.limit_right = level.width * level.tile_px; camera.limit_bottom = level.height * level.tile_px
	player.add_child(camera)
	var post := CanvasLayer.new(); post.name = "Saturation"
	var rect := ColorRect.new(); rect.set_anchors_preset(Control.PRESET_FULL_RECT); rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var mat := ShaderMaterial.new(); mat.shader = preload("res://art/saturation.gdshader"); rect.material = mat
	post.add_child(rect); add_child(post)
	player.reached_goal.connect(_on_goal)
	# Play resets to the start with colors kept (mechanic.md). Deferred so a replay runner still sees where the hazard was.
	player.touched_hazard.connect(_respawn, CONNECT_DEFERRED)

func _on_goal() -> void:
	if has_node("GoalLayer"): return
	var layer := CanvasLayer.new(); layer.name = "GoalLayer"; layer.layer = 2
	var label := Label.new(); label.text = "GOAL — R to restart"; label.position = Vector2(860, 480)
	label.add_theme_font_size_override("font_size", 48)
	layer.add_child(label); add_child(layer)

func _respawn() -> void:
	player.position = start; player.velocity = Vector2.ZERO; player.dash_ticks_left = 0; player.died = false

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("restart"): get_tree().reload_current_scene()
	elif event.is_action_pressed("quit"): get_tree().quit()
