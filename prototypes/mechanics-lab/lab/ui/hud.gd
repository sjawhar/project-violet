## THROWAWAY — Violet mechanics lab, presentation component.
## Top-left run info (experiment/model/profile/deaths/time), a resonance
## indicator that adapts to the active model (window ring / selected swatch
## / breath bar), a 1.5s room title card, and the H control-hints overlay
## (no separate class in the contract; folded in here). Drop into
## `prototypes/mechanics-lab/lab/ui/hud.gd` unchanged.
class_name LabHud
extends CanvasLayer

const MODEL_LABELS := {
	"none": "No resonance",
	"ability_window": "Ability triggers resonance (2019 design)",
	"pick_color": "Choose your color (bake-off)",
	"hold_breath": "Hold to resonate",
}
const HINTS_TEXT := "Controls
left/right/up/down — A/D/W/S & arrows, or left stick + d-pad
jump — Space, K / A (bottom)
dash — Shift, J / X (left)
ability — L, C / B (right)
switch — Q, I / Y (top)
resonate (hold) — E, O / RB
restart — R / Back · Select
menu — Esc / Start
compare (profile toggle) — Tab / LB
tune (panel) — F1
hints — H
mute — M"

var _info_label: Label
var _resonance: _ResonanceIndicator
var _title_card: Control
var _title_card_experiment: Label
var _title_card_title: Label
var _title_card_hint: Label
var _hints_panel: Control
var _title_card_tween: Tween

var _experiment: Dictionary = {}


func _ready() -> void:
	layer = 15
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)

	_info_label = Label.new()
	_info_label.position = Vector2(24, 20)
	_info_label.add_theme_font_size_override("font_size", 20)
	root.add_child(_info_label)

	_resonance = _ResonanceIndicator.new()
	_resonance.position = Vector2(24, 120)
	root.add_child(_resonance)

	_title_card = Control.new()
	_title_card.set_anchors_preset(Control.PRESET_FULL_RECT)
	_title_card.modulate.a = 0.0
	root.add_child(_title_card)
	var card_box := VBoxContainer.new()
	card_box.set_anchors_preset(Control.PRESET_CENTER)
	card_box.alignment = BoxContainer.ALIGNMENT_CENTER
	_title_card.add_child(card_box)
	_title_card_experiment = Label.new()
	_title_card_experiment.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title_card_experiment.add_theme_font_size_override("font_size", 22)
	card_box.add_child(_title_card_experiment)
	_title_card_title = Label.new()
	_title_card_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title_card_title.add_theme_font_size_override("font_size", 48)
	card_box.add_child(_title_card_title)
	_title_card_hint = Label.new()
	_title_card_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title_card_hint.add_theme_font_size_override("font_size", 22)
	card_box.add_child(_title_card_hint)

	_hints_panel = PanelContainer.new()
	_hints_panel.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	_hints_panel.offset_top = -340
	_hints_panel.offset_left = 24
	_hints_panel.offset_bottom = -24
	_hints_panel.offset_right = 420
	_hints_panel.visible = false
	root.add_child(_hints_panel)
	var hints_label := Label.new()
	hints_label.text = HINTS_TEXT
	_hints_panel.add_child(hints_label)


func _unhandled_input(event: InputEvent) -> void:
	if InputMap.has_action(&"hints") and event.is_action_pressed(&"hints"):
		_hints_panel.visible = not _hints_panel.visible


## Shows a 1.5s title card for the room (title + hint), then fades it.
func show_room(experiment: Dictionary, room: Dictionary) -> void:
	_experiment = experiment
	_title_card_experiment.text = String(experiment.get("title", ""))
	_title_card_title.text = String(room.get("title", ""))
	_title_card_hint.text = String(room.get("hint", ""))
	if _title_card_tween and _title_card_tween.is_valid():
		_title_card_tween.kill()
	_title_card.modulate.a = 1.0
	_title_card_tween = create_tween()
	_title_card_tween.tween_interval(1.5)
	_title_card_tween.tween_property(_title_card, "modulate:a", 0.0, 0.3)


## Refreshes the info readout and resonance indicator every tick.
func update_state(player: Node, model_state: Dictionary, deaths: int, time_s: float) -> void:
	var model: String = String(model_state.get("model", "none"))
	var model_label: String = MODEL_LABELS.get(model, model)
	var profile_name: String = String(_experiment.get("profile", ""))
	var state_name: String = String(player.state) if player != null else ""
	_info_label.text = "%s\n%s\nprofile: %s   state: %s\nDeaths: %d   Time: %.1fs" % [
		_experiment.get("title", ""), model_label, profile_name, state_name, deaths, time_s,
	]
	_resonance.set_state(model_state)


## Custom-drawn resonance indicator: a countdown ring for `ability_window`,
## a color swatch for `pick_color`, a breath bar for `hold_breath`.
class _ResonanceIndicator:
	extends Control

	const NEUTRAL := Color8(0x9A, 0xA0, 0xA6)
	const PALETTE := {
		"red": Color8(0xE5, 0x55, 0x3F), "green": Color8(0x4C, 0xC2, 0x7A),
		"yellow": Color8(0xF2, 0xC9, 0x4C), "blue": Color8(0x4A, 0x90, 0xE2),
	}

	var _state: Dictionary = {}

	func _ready() -> void:
		custom_minimum_size = Vector2(160, 160)

	func set_state(state: Dictionary) -> void:
		_state = state
		queue_redraw()

	func _color_for(key) -> Color:
		return PALETTE.get(String(key), NEUTRAL)

	func _draw() -> void:
		var model: String = String(_state.get("model", "none"))
		match model:
			"ability_window":
				var colors: Array = _state.get("colors", [])
				var c: Color = _color_for(colors[0]) if colors.size() > 0 else NEUTRAL
				var timer_frac: float = float(_state.get("timer_frac", -1.0))
				draw_arc(Vector2(40, 40), 32, 0, TAU, 48, Color(1, 1, 1, 0.15), 6.0, true)
				if timer_frac >= 0.0:
					draw_arc(Vector2(40, 40), 32, -PI / 2, -PI / 2 + TAU * timer_frac, 48, c, 6.0, true)
			"pick_color":
				var selected = _state.get("selected", null)
				draw_rect(Rect2(0, 0, 48, 48), _color_for(selected) if selected != null else NEUTRAL)
			"hold_breath":
				var selected = _state.get("selected", null)
				var breath_frac: float = float(_state.get("breath_frac", -1.0))
				draw_rect(Rect2(0, 0, 48, 48), _color_for(selected) if selected != null else NEUTRAL)
				if breath_frac >= 0.0:
					draw_rect(Rect2(0, 64, 140, 18), Color(1, 1, 1, 0.15))
					draw_rect(Rect2(0, 64, 140 * breath_frac, 18), _color_for(selected) if selected != null else NEUTRAL)
			_:
				pass
