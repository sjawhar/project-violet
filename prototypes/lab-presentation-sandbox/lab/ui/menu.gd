## THROWAWAY — Violet mechanics lab, presentation component.
## Keyboard/gamepad/mouse-navigable experiment list: title + question per
## row, a done marker once an experiment is finished. Gamepad/keyboard
## navigation rides Godot's built-in ui_up/ui_down/ui_accept focus actions.
## Drop into `prototypes/mechanics-lab/lab/ui/menu.gd` unchanged.
class_name LabMenu
extends Control

signal chosen(experiment_id)

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


## Rebuilds the list from `experiments.json`'s shape
## (`[{id, title, question, ...}]`) plus `done` (`{experiment_id: bool}`).
func show_experiments(list: Array, done: Dictionary) -> void:
	for child in _list_box.get_children():
		child.queue_free()
	var first_button: Button = null
	for experiment in list:
		var row := _build_row(experiment, done)
		_list_box.add_child(row)
		if first_button == null:
			first_button = row
	if first_button:
		first_button.grab_focus()


func _build_row(experiment: Dictionary, done: Dictionary) -> Button:
	var btn := Button.new()
	btn.focus_mode = Control.FOCUS_ALL
	btn.custom_minimum_size = Vector2(0, 72)
	btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
	var mark: String = "✓  " if done.get(experiment.get("id"), false) else "    "
	btn.text = "%s%s\n     %s" % [mark, String(experiment.get("title", "")), String(experiment.get("question", ""))]
	var experiment_id = experiment.get("id")
	btn.pressed.connect(func(): chosen.emit(experiment_id))
	return btn
