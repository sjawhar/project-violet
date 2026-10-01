# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
class_name ResonanceFactory
extends RefCounted

const REGISTRY := {
	"none": preload("res://lab/resonance/none_model.gd"),
	"ability_window": preload("res://lab/resonance/ability_window_model.gd"),
	"pick_color": preload("res://lab/resonance/pick_color_model.gd"),
	"hold_breath": preload("res://lab/resonance/hold_breath_model.gd"),
}

const LABELS := {
	"none": "No resonance",
	"ability_window": "Ability triggers resonance (2019 design)",
	"pick_color": "Choose your color (bake-off)",
	"hold_breath": "Hold to resonate",
}

static func create(model_name: String) -> ResonanceModel:
	if not REGISTRY.has(model_name):
		push_error("ResonanceFactory: unknown model '%s'" % model_name)
		return null
	return REGISTRY[model_name].new()

static func label(model_name: String) -> String:
	return LABELS.get(model_name, model_name)
