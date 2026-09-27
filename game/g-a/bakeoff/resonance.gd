extends Node
## THROWAWAY (bake-off lane G-A): the test mechanic's color state (docs/bakeoff/mechanic.md).
signal changed
const COLORS := ["red", "green"]
var acquired: Array[String] = []
var active := ""
var abilities_disabled: PackedStringArray = []
func acquire(color: String) -> void:
	if color not in acquired: acquired.append(color)
	active = color; _emit()
func cycle() -> void:
	if acquired.size() < 2: return
	active = acquired[(acquired.find(active) + 1) % acquired.size()]; _emit()
func reset() -> void:
	acquired.clear(); active = ""; abilities_disabled = []; _emit()
func has(color: String) -> bool: return color in acquired
func can_dash() -> bool: return active == "red" and not abilities_disabled.has("dash")
func can_double_jump() -> bool: return active == "green" and not abilities_disabled.has("double_jump")
func world_saturation() -> float: return [0.35, 0.7, 1.0][acquired.size()]
func _emit() -> void:
	RenderingServer.global_shader_parameter_set("world_saturation", world_saturation()); changed.emit()
