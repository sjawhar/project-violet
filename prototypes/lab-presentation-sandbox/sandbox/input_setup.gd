## THROWAWAY — sandbox-only. Registers the handful of InputMap actions the
## demo's UI needs (tune/hints/mute). Everything else UI-navigable (menu,
## tuning panel sliders/buttons) rides Godot's built-in ui_* actions, which
## already have sane keyboard + gamepad bindings out of the box. Not part of
## the presentation contract; NOT copied by the integrator.
extends Node


func _enter_tree() -> void:
	_add_key_action("tune", KEY_F1)
	_add_key_action("hints", KEY_H)
	_add_key_action("mute", KEY_M)


func _add_key_action(action: StringName, keycode: Key) -> void:
	if InputMap.has_action(action):
		return
	InputMap.add_action(action)
	var ev := InputEventKey.new()
	ev.keycode = keycode
	InputMap.action_add_event(action, ev)
