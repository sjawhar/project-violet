# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# Name -> Ability script, so LabPlayer builds its ability set from
# experiments.json's `abilities: [...]` list by name alone. Wave 2 drops in
# stomp/blink/swing by adding one line each here (plus the script file);
# nothing else needs to change.
class_name AbilityRegistry
extends RefCounted

const REGISTRY := {
	"dash": preload("res://lab/abilities/dash.gd"),
	"double_jump": preload("res://lab/abilities/double_jump.gd"),
	"stomp": preload("res://lab/abilities/stomp.gd"),
	"blink": preload("res://lab/abilities/blink.gd"),
	"swing": preload("res://lab/abilities/swing.gd"),
}

static func create(ability_name: String) -> Ability:
	if not REGISTRY.has(ability_name):
		push_error("AbilityRegistry: unknown ability '%s'" % ability_name)
		return null
	return REGISTRY[ability_name].new()
