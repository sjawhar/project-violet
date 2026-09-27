extends Node
## THROWAWAY (bake-off lane G-A): registers the mechanic's key bindings (docs/bakeoff/mechanic.md, Controls).
const BINDINGS := {
	"left": [KEY_A, KEY_LEFT], "right": [KEY_D, KEY_RIGHT], "jump": [KEY_SPACE], "dash": [KEY_SHIFT],
	"switch": [KEY_Q], "restart": [KEY_R], "quit": [KEY_ESCAPE],
}
func _enter_tree() -> void:
	for action: String in BINDINGS:
		if not InputMap.has_action(action): InputMap.add_action(action)
		for key: Key in BINDINGS[action]:
			var ev := InputEventKey.new(); ev.physical_keycode = key
			InputMap.action_add_event(action, ev)
