# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# Minimal placeholder menu: a plain text list, navigated with the lab's own
# up/down + jump actions (keyboard and gamepad both already bound to those
# in project.godot; avoids Godot's built-in ui_accept/ui_cancel, which have
# no default gamepad binding in 4.7.2). lab/ui/menu.gd (class_name LabMenu
# extends Control, same show_experiments/chosen contract) replaces this
# script on the same "MenuRoot" node later; main.gd's call sites don't
# change. Handles any number of experiments.
extends Control

signal chosen(experiment_id: String)

var _experiments: Array = []
var _done: Dictionary = {}
var _selected := 0
var _label: Label

func _ready() -> void:
	_label = Label.new()
	_label.add_theme_font_size_override("font_size", 26)
	_label.position = Vector2(80, 60)
	_label.size = Vector2(1700, 960)
	add_child(_label)
	set_process(true)

func show_experiments(experiments: Array, done: Dictionary) -> void:
	_experiments = experiments
	_done = done
	_selected = clampi(_selected, 0, maxi(0, _experiments.size() - 1))
	_redraw()

func _process(_delta: float) -> void:
	if not visible or _experiments.is_empty():
		return
	if Input.is_action_just_pressed("down"):
		_selected = (_selected + 1) % _experiments.size()
		_redraw()
	elif Input.is_action_just_pressed("up"):
		_selected = (_selected - 1 + _experiments.size()) % _experiments.size()
		_redraw()
	elif Input.is_action_just_pressed("jump") or Input.is_action_just_pressed("ability"):
		var exp: Dictionary = _experiments[_selected]
		chosen.emit(str(exp.get("id", "")))

func _redraw() -> void:
	var lines: PackedStringArray = [
		"VIOLET MECHANICS LAB",
		"",
		"Up/Down (or stick/d-pad) to choose, Jump (Space/K/A) to play.",
		"",
	]
	for i in range(_experiments.size()):
		var e: Dictionary = _experiments[i]
		var id := str(e.get("id", ""))
		var mark := "> " if i == _selected else "  "
		var done_mark := "  [done]" if _done.get(id, false) else ""
		lines.append("%s%s%s" % [mark, str(e.get("title", id)), done_mark])
		if i == _selected:
			lines.append("      %s" % str(e.get("question", "")))
	_label.text = "\n".join(lines)
