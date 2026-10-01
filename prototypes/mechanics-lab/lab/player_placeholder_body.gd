# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# Minimal placeholder body: a plain rounded rectangle + facing mark, drawn
# under LabPlayer.visual_root. The presentation agent's lab/juice/player_juice.gd
# (bind(player)) replaces this node entirely; nothing else references it by
# name, so deleting it and adding PlayerJuice under visual_root is a clean swap.
extends Node2D

const BODY_COLOR := Color("#E8E3D8")
const FACE_COLOR := Color("#1F2430")

var _player: LabPlayer

func _ready() -> void:
	_player = get_parent().get_parent() as LabPlayer
	set_process(true)

func _process(_delta: float) -> void:
	queue_redraw()

func _draw() -> void:
	if _player == null:
		return
	var size: Vector2 = _player.box_size_px
	if size == Vector2.ZERO:
		return
	var top_left := Vector2(-size.x * 0.5, -size.y)
	draw_rect(Rect2(top_left, size), BODY_COLOR)
	var face_x: float = size.x * 0.28 * float(_player.facing)
	draw_circle(Vector2(face_x, -size.y * 0.75), maxf(size.x * 0.1, 2.0), FACE_COLOR)
