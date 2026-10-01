## THROWAWAY — Violet mechanics lab, presentation component.
## Generic live-tuning panel built entirely from `PhysicsProfile.TUNABLES` —
## no per-field code, so it works unchanged against the real profile. F1
## toggles visibility. Drop into
## `prototypes/mechanics-lab/lab/ui/tuning_panel.gd` unchanged.
class_name TuningPanel
extends CanvasLayer

signal changed

## Transcribed verbatim from the design contract's physics-profile table
## (`local://mechanics-lab-design.md`), so the "Tuned"/"Bake-off" quick-apply
## buttons work standalone even before the core agent's own preset
## resources (`lab/profiles/*.tres`) exist.
const BAKEOFF_PRESET := {
	"run_speed": 8.0, "ground_accel_time": 0.0, "ground_decel_time": 0.0,
	"air_accel_mult": 1.0, "turn_accel_mult": 1.0, "jump_height": 3.0,
	"jump_time_to_apex": 0.3875, "min_jump_height": 3.0, "fall_gravity_mult": 1.0,
	"apex_hang_speed": 0.0, "apex_hang_mult": 1.0, "max_fall_speed": 1000.0,
	"fast_fall_speed": 1000.0, "coyote_ticks": 0.0, "buffer_ticks": 0.0,
	"corner_correct_px": 0.0, "box_w": 0.8, "box_h": 1.6, "dash_speed": 30.0,
	"dash_ticks": 12.0, "dash_freeze_ticks": 0.0, "dash_end_speed": 0.0,
	"dash_eight_way": 0.0, "double_jump_height": 3.0, "wall_jump": 0.0,
	"wall_slide_speed": 0.0, "wall_jump_push": 0.0, "resonance_ticks": 90.0,
	"breath_ticks": 120.0,
}
const TUNED_PRESET := {
	"run_speed": 9.0, "ground_accel_time": 0.09, "ground_decel_time": 0.06,
	"air_accel_mult": 0.7, "turn_accel_mult": 1.6, "jump_height": 3.25,
	"jump_time_to_apex": 0.38, "min_jump_height": 1.1, "fall_gravity_mult": 1.7,
	"apex_hang_speed": 2.5, "apex_hang_mult": 0.5, "max_fall_speed": 18.0,
	"fast_fall_speed": 26.0, "coyote_ticks": 6.0, "buffer_ticks": 7.0,
	"corner_correct_px": 14.0, "box_w": 0.7, "box_h": 1.45, "dash_speed": 24.0,
	"dash_ticks": 10.0, "dash_freeze_ticks": 3.0, "dash_end_speed": 9.0,
	"dash_eight_way": 0.0, "double_jump_height": 2.4, "wall_jump": 0.0,
	"wall_slide_speed": 5.0, "wall_jump_push": 9.0, "resonance_ticks": 90.0,
	"breath_ticks": 120.0,
}

var _profile: Resource
var _root: Control
var _rows_box: VBoxContainer
var _value_labels: Dictionary = {}
var _sliders: Dictionary = {}


func _ready() -> void:
	layer = 20
	_root = PanelContainer.new()
	_root.visible = false
	_root.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	_root.offset_left = -440
	_root.offset_right = -20
	_root.offset_top = 20
	_root.offset_bottom = -20
	add_child(_root)

	var outer := VBoxContainer.new()
	_root.add_child(outer)

	var title := Label.new()
	title.text = "Tuning (F1)"
	title.add_theme_font_size_override("font_size", 22)
	outer.add_child(title)

	var buttons := HBoxContainer.new()
	outer.add_child(buttons)
	var tuned_btn := Button.new()
	tuned_btn.text = "Tuned"
	tuned_btn.pressed.connect(func(): _apply_preset(TUNED_PRESET))
	buttons.add_child(tuned_btn)
	var bakeoff_btn := Button.new()
	bakeoff_btn.text = "Bake-off"
	bakeoff_btn.pressed.connect(func(): _apply_preset(BAKEOFF_PRESET))
	buttons.add_child(bakeoff_btn)
	var copy_btn := Button.new()
	copy_btn.text = "Copy settings"
	copy_btn.pressed.connect(_on_copy_settings)
	buttons.add_child(copy_btn)

	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(420, 900)
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	outer.add_child(scroll)
	_rows_box = VBoxContainer.new()
	_rows_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_rows_box)


func _unhandled_input(event: InputEvent) -> void:
	if InputMap.has_action(&"tune") and event.is_action_pressed(&"tune"):
		_root.visible = not _root.visible


## Binds a `PhysicsProfile` and (re)builds one slider per `TUNABLES` entry.
func bind(profile: Resource) -> void:
	_profile = profile
	for child in _rows_box.get_children():
		child.queue_free()
	_sliders.clear()
	_value_labels.clear()
	for tunable in profile.TUNABLES:
		_rows_box.add_child(_build_row(tunable))


func _build_row(tunable: Dictionary) -> Control:
	var row := VBoxContainer.new()
	var header := HBoxContainer.new()
	row.add_child(header)
	var name_label := Label.new()
	name_label.text = tunable.label
	name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(name_label)
	var value_label := Label.new()
	value_label.custom_minimum_size = Vector2(90, 0)
	value_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	header.add_child(value_label)
	_value_labels[tunable.name] = value_label

	var slider := HSlider.new()
	slider.min_value = tunable.min
	slider.max_value = tunable.max
	slider.step = tunable.step
	slider.set_value_no_signal(_profile.get(tunable.name))
	slider.value_changed.connect(_on_slider_changed.bind(tunable.name))
	row.add_child(slider)
	_sliders[tunable.name] = slider

	_update_value_label(tunable.name, tunable.unit)
	return row


func _on_slider_changed(value: float, field_name: StringName) -> void:
	_profile.set(field_name, value)
	_update_value_label_from_tunables(field_name)
	changed.emit()


func _update_value_label_from_tunables(field_name: StringName) -> void:
	for tunable in _profile.TUNABLES:
		if tunable.name == field_name:
			_update_value_label(field_name, tunable.unit)
			return


func _update_value_label(field_name: StringName, unit: String) -> void:
	var value: float = _profile.get(field_name)
	var label: Label = _value_labels[field_name]
	var text: String = str(int(round(value))) if absf(value - round(value)) < 0.0005 else ("%.2f" % value)
	if unit != "":
		text += " " + unit
	label.text = text


func _apply_preset(preset: Dictionary) -> void:
	_profile.apply_dict(preset)
	for field_name in _sliders:
		var slider: HSlider = _sliders[field_name]
		slider.set_value_no_signal(_profile.get(field_name))
	for tunable in _profile.TUNABLES:
		_update_value_label(tunable.name, tunable.unit)
	changed.emit()


func _on_copy_settings() -> void:
	DisplayServer.clipboard_set(JSON.stringify(_profile.to_dict()))
