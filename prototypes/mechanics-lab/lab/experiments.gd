# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# Loads res://experiments.json: [{id, title, question, model, profile,
# abilities: [...], acquired: [...], rooms: [room ids]}]. Shared by the menu
# (lab/menu_plain.gd) and tests/replay_runner.gd.
class_name ExperimentsData
extends RefCounted

const PATH := "res://experiments.json"

static func load_all() -> Array:
	if not FileAccess.file_exists(PATH):
		push_error("ExperimentsData: missing %s" % PATH)
		return []
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	if typeof(parsed) != TYPE_ARRAY:
		push_error("ExperimentsData: %s did not parse to a JSON array" % PATH)
		return []
	return parsed

static func find(experiments: Array, id: String) -> Dictionary:
	for e: Dictionary in experiments:
		if e.get("id", "") == id:
			return e
	return {}
