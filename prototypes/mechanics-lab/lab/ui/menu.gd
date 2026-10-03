## THROWAWAY — Violet mechanics lab, presentation component.
## Keyboard/gamepad/mouse-navigable experiment list: title + question per
## row, a done marker once an experiment is finished. Gamepad/keyboard
## navigation rides Godot's built-in ui_up/ui_down/ui_accept focus actions.
## Drop into `prototypes/mechanics-lab/lab/ui/menu.gd` unchanged.
class_name LabMenu
extends Control

signal chosen(experiment_id)

## Round 2 extension: experiments.json entries may carry an optional
## "group" key; the first entry of a new group gets a heading label above
## it (the first group in the list gets none -- it's already first).
const GROUP_LABELS := {
	"round1": "Round 1 experiments",
}

var _list_box: VBoxContainer


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)

	var bg := ColorRect.new()
	bg.color = Color8(0x1F, 0x24, 0x30)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)

	var vbox := VBoxContainer.new()
	vbox.set_anchors_preset(Control.PRESET_FULL_RECT)
	vbox.offset_left = 120
	vbox.offset_top = 80
	vbox.offset_right = -120
	vbox.offset_bottom = -80
	add_child(vbox)

	var title := Label.new()
	title.text = "Violet — mechanics lab (throwaway)"
	title.add_theme_font_size_override("font_size", 40)
	vbox.add_child(title)

	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	vbox.add_child(scroll)
	_list_box = VBoxContainer.new()
	_list_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_list_box.add_theme_constant_override("separation", 16)
	scroll.add_child(_list_box)

	var controls := Label.new()
	controls.text = "Up/Down or stick: choose   Enter/Space/A: play   Esc/Start: menu   Tab/LB: compare movement   F1: tuning   H: hints   M: mute"
	controls.add_theme_font_size_override("font_size", 16)
	controls.modulate.a = 0.7
	controls.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vbox.add_child(controls)


## Rebuilds the list from `experiments.json`'s shape
## (`[{id, title, question, ...}]`) plus `done` (`{experiment_id: bool}`).
func show_experiments(list: Array, done: Dictionary) -> void:
	for child in _list_box.get_children():
		child.queue_free()
	var first_button: Button = null
	var last_group := ""
	var number := 0
	for experiment: Dictionary in list:
		var group := String(experiment.get("group", ""))
		if group != "" and group != last_group:
			_list_box.add_child(_build_heading(GROUP_LABELS.get(group, group)))
		last_group = group
		number += 1
		var row := _build_row(experiment, number, done)
		_list_box.add_child(row)
		if first_button == null:
			first_button = row
	if first_button:
		first_button.grab_focus()


func _build_heading(text: String) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 24)
	label.modulate.a = 0.85
	return label


func _build_row(experiment: Dictionary, number: int, done: Dictionary) -> Button:
	var btn := Button.new()
	btn.focus_mode = Control.FOCUS_ALL
	btn.custom_minimum_size = Vector2(0, 72)
	btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
	# A few questions (8/9's full 2019-puzzle quote) are long enough to run
	# past the button's right edge and off the visible screen without this:
	# Button doesn't wrap by default, so a single-line question just keeps
	# going and gets clipped. custom_minimum_size.y above is a floor, not a
	# cap, so wrapped rows grow taller automatically; shorter rows stay at 72.
	btn.autowrap_mode = TextServer.AUTOWRAP_WORD
	var mark: String = "✓  " if done.get(experiment.get("id"), false) else "    "
	btn.text = "%s%d. %s\n     %s" % [mark, number, String(experiment.get("title", "")), String(experiment.get("question", ""))]
	var experiment_id = experiment.get("id")
	btn.pressed.connect(func(): chosen.emit(experiment_id))
	return btn
