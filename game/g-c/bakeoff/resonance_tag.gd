class_name ResonanceTag
extends Node
## Marks the parent body (CollisionObject2D or 3D) as color-tagged geometry. THROWAWAY.
@export var color: String
@export var kind: String
@export var cell: Vector2i
func _ready() -> void:
	add_to_group("resonance"); Resonance.changed.connect(_apply); _apply()
func _apply() -> void:
	var body := get_parent()
	var passable := Resonance.active == color
	body.collision_layer = 0 if passable else 1
	body.set_meta("resonance_passable", passable)
	for child in body.get_children():
		if child.has_method("set_resonance_look"): child.set_resonance_look(Resonance.has(color), passable)
