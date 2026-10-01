## THROWAWAY — verification-only. Runs the demo scene headless (no video
## encoding) and prints internal juice/UI state at key ticks, so squash/
## stretch, scarf color, HUD text and the tuning panel can be confirmed fast
## on a heavily contended machine without waiting on Movie Maker.
extends Node

var _demo: Node
var _tick := 0
const CHECKPOINTS := [2, 54, 56, 58, 62, 124, 126, 128, 132, 216, 218, 220, 226, 333, 335, 337, 341, 660, 700]


func _ready() -> void:
	var packed: PackedScene = load("res://demo/demo.tscn")
	_demo = packed.instantiate()
	add_child(_demo)


func _physics_process(_delta: float) -> void:
	_tick += 1
	if _tick in CHECKPOINTS:
		var juice = _demo.get_node("PlayerJuice")
		var hud = _demo.get_node("LabHud")
		var tuning = _demo.get_node("TuningPanel")
		var player = _demo.get_node("LabPlayer")
		print("TICK ", _tick, " state=", player.state, " squash=", juice._squash,
			" scarf_color=", juice._scarf._current_color, " hud_text=", hud._info_label.text,
			" tuning_visible=", tuning._root.visible)
	if _tick >= 700:
		get_tree().quit()
