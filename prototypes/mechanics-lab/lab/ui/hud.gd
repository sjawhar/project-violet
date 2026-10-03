## THROWAWAY — Violet mechanics lab, presentation component.
## Top-left run info (experiment/model/profile/deaths/time) with the model
## label pulled out large and prominent, a resonance indicator that adapts
## to the active model (window ring / selected swatch / breath bar), a
## subtle full-screen resonance vignette so the resonating color reads from
## anywhere on screen, a brief centered profile-swap toast (Tab/LB), a 1.5s
## room title card, and the H control-hints overlay (no separate class in
## the contract; folded in here). Drop into
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

const COLOR_PALETTE := {
	"red": Color8(0xE5, 0x55, 0x3F), "green": Color8(0x4C, 0xC2, 0x7A),
	"yellow": Color8(0xF2, 0xC9, 0x4C), "blue": Color8(0x4A, 0x90, 0xE2),
}
const RESONANCE_NEUTRAL := Color8(0x9A, 0xA0, 0xA6)

## Tick-based animation constants (update_state runs once per physics tick,
## DESIGN.md's fixed 1/60s, so a fixed dt here stays in lockstep with it
## rather than drifting against a separate render-frame delta).
const TICK_DT := 1.0 / 60.0
const RESONANCE_VIGNETTE_MAX_ALPHA := 0.16
const RESONANCE_VIGNETTE_BREATH_AMPLITUDE := 0.3
const RESONANCE_VIGNETTE_BREATH_FREQ := 0.9
const RESONANCE_VIGNETTE_LERP_SPEED := 6.0

const PROFILE_TOAST_LABELS := {
	"tuned": "Tuned movement",
	"bakeoff": "Bake-off movement",
	"tuned_walljump": "Tuned + wall jump",
}

## Always-visible bottom bar naming the keys THIS experiment needs, so a
## player never has to find H to learn how to switch, resonate or use blue.
const CONTROLS_MODEL_KEYS := {
	"none": "Tab: compare with bake-off movement   F1: tuning sliders",
	"ability_window": "Using an ability makes its color resonate",
	"pick_color": "Q: switch color (only that color's ability works)",
	"hold_breath": "Q: choose color   Hold E: resonate",
}
const CONTROLS_ABILITY_KEYS := {
	"dash": "Shift: dash (red)",
	"double_jump": "Space in the air: double jump (green)",
	"stomp": "Down in the air: stomp (yellow)",
	"blink": "L: blink (blue)",
	"swing": "Hold L near a blue ring: swing (blue)",
}

var _resonance_vignette: TextureRect
var _vignette_alpha := 0.0
var _vignette_color: Color = RESONANCE_NEUTRAL

var _model_label: Label
var _info_label: Label
var _resonance: _ResonanceIndicator
var _title_card: Control
var _title_card_experiment: Label
var _title_card_title: Label
var _title_card_hint: Label
var _hints_panel: Control
var _title_card_tween: Tween

var _profile_toast: Control
var _profile_toast_label: Label
var _profile_toast_tween: Tween

var _experiment: Dictionary = {}
var _controls_bar: Label


func _ready() -> void:
	layer = 15
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)

	# Added first so it draws behind every other HUD element: a soft radial
	# gradient (transparent center, tinted edges) that fades in/out with
	# whether a color is resonating, so the player can tell from anywhere on
	# screen without a shader or hurting geometry readability.
	var gradient := Gradient.new()
	gradient.set_color(0, Color(1.0, 1.0, 1.0, 0.0))
	gradient.set_color(1, Color(1.0, 1.0, 1.0, 1.0))
	var gradient_tex := GradientTexture2D.new()
	gradient_tex.gradient = gradient
	gradient_tex.width = 256
	gradient_tex.height = 256
	gradient_tex.fill = GradientTexture2D.FILL_RADIAL
	gradient_tex.fill_from = Vector2(0.5, 0.5)
	gradient_tex.fill_to = Vector2(1.0, 0.5)
	_resonance_vignette = TextureRect.new()
	_resonance_vignette.texture = gradient_tex
	_resonance_vignette.stretch_mode = TextureRect.STRETCH_SCALE
	_resonance_vignette.set_anchors_preset(Control.PRESET_FULL_RECT)
	_resonance_vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_resonance_vignette.modulate = Color(_vignette_color.r, _vignette_color.g, _vignette_color.b, 0.0)
	root.add_child(_resonance_vignette)

	_model_label = Label.new()
	_model_label.position = Vector2(24, 16)
	_model_label.add_theme_font_size_override("font_size", 30)
	root.add_child(_model_label)

	_info_label = Label.new()
	_info_label.position = Vector2(24, 58)
	_info_label.add_theme_font_size_override("font_size", 18)
	root.add_child(_info_label)

	_resonance = _ResonanceIndicator.new()
	_resonance.position = Vector2(24, 150)
	root.add_child(_resonance)

	_controls_bar = Label.new()
	_controls_bar.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_controls_bar.offset_top = -74.0
	_controls_bar.autowrap_mode = TextServer.AUTOWRAP_WORD
	_controls_bar.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_controls_bar.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_controls_bar.add_theme_font_size_override("font_size", 20)
	var bar_style := StyleBoxFlat.new()
	bar_style.bg_color = Color(0.0, 0.0, 0.0, 0.5)
	_controls_bar.add_theme_stylebox_override("normal", bar_style)
	root.add_child(_controls_bar)

	_title_card = Control.new()
	_title_card.set_anchors_preset(Control.PRESET_FULL_RECT)
	_title_card.modulate.a = 0.0
	root.add_child(_title_card)
	# A CenterContainer (not set_anchors_preset(PRESET_CENTER) on the panel
	# directly) so the card stays truly centered as its content size changes
	# room to room: anchors-preset math bakes in offsets from the control's
	# size *at the moment it's called*, which here was zero (no children
	# yet) -- that pinned the panel's top-left corner at the viewport
	# center and let it grow only rightward, so any room with a long hint
	# or title overflowed off the right edge instead of being centered.
	var card_center := CenterContainer.new()
	card_center.set_anchors_preset(Control.PRESET_FULL_RECT)
	card_center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_title_card.add_child(card_center)
	var card_panel := PanelContainer.new()
	var card_style := StyleBoxFlat.new()
	card_style.bg_color = Color(0.0, 0.0, 0.0, 0.55)
	card_style.content_margin_left = 32.0
	card_style.content_margin_right = 32.0
	card_style.content_margin_top = 16.0
	card_style.content_margin_bottom = 16.0
	card_panel.add_theme_stylebox_override("panel", card_style)
	card_center.add_child(card_panel)
	var card_box := VBoxContainer.new()
	card_box.alignment = BoxContainer.ALIGNMENT_CENTER
	card_panel.add_child(card_box)
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
	# Several rooms' hints are long single sentences; without a wrap width
	# the Label (and the PanelContainer/VBoxContainer sizing to fit it)
	# grows past the 1920px viewport and the ends clip off both edges.
	# Capping the width and enabling word-wrap keeps the whole hint on
	# screen as 1-3 lines instead.
	_title_card_hint.custom_minimum_size.x = 1400.0
	_title_card_hint.autowrap_mode = TextServer.AUTOWRAP_WORD
	card_box.add_child(_title_card_hint)

	_profile_toast = Control.new()
	_profile_toast.set_anchors_preset(Control.PRESET_FULL_RECT)
	_profile_toast.modulate.a = 0.0
	root.add_child(_profile_toast)
	var toast_panel := PanelContainer.new()
	toast_panel.set_anchors_preset(Control.PRESET_CENTER)
	toast_panel.offset_top -= 220
	toast_panel.offset_bottom -= 220
	var toast_style := StyleBoxFlat.new()
	toast_style.bg_color = Color(0.0, 0.0, 0.0, 0.6)
	toast_style.content_margin_left = 28.0
	toast_style.content_margin_right = 28.0
	toast_style.content_margin_top = 12.0
	toast_style.content_margin_bottom = 12.0
	toast_panel.add_theme_stylebox_override("panel", toast_style)
	_profile_toast.add_child(toast_panel)
	_profile_toast_label = Label.new()
	_profile_toast_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_profile_toast_label.add_theme_font_size_override("font_size", 30)
	toast_panel.add_child(_profile_toast_label)

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


## "Move ... · Jump ... · <model keys> · <one entry per ability> · <extra> ·
## R/Esc/H". An ability or model missing from the tables is a lab bug: fail
## loudly. `extra_controls` (round 2 extension; optional, e.g. the wall-jump
## trial's wall slide/jump hint, which isn't gated behind an `abilities`
## entry the way dash/double_jump/stomp/swing are) is appended verbatim.
func _controls_text(experiment: Dictionary) -> String:
	var parts: PackedStringArray = ["Move: arrows or A/D", "Jump: Space"]
	var model_keys: String = CONTROLS_MODEL_KEYS[String(experiment["model"])]
	if model_keys != "":
		parts.append(model_keys)
	for ability in experiment["abilities"]:
		parts.append(CONTROLS_ABILITY_KEYS[String(ability)])
	for extra in experiment.get("extra_controls", []):
		parts.append(String(extra))
	parts.append("R: restart   Esc: menu   H: all controls")
	return "   ·   ".join(parts)


## Shows a 1.5s title card for the room (title + hint), then fades it.
func show_room(experiment: Dictionary, room: Dictionary) -> void:
	_experiment = experiment
	_title_card_experiment.text = String(experiment.get("title", ""))
	_title_card_title.text = String(room.get("title", ""))
	_title_card_hint.text = String(room.get("hint", ""))
	_controls_bar.text = _controls_text(experiment)
	if _title_card_tween and _title_card_tween.is_valid():
		_title_card_tween.kill()
	_title_card.modulate.a = 1.0
	_title_card_tween = create_tween()
	_title_card_tween.tween_interval(1.5)
	_title_card_tween.tween_property(_title_card, "modulate:a", 0.0, 0.3)


## Shows a brief centered toast naming the movement profile now active
## (Tab/LB compare toggle): `profile_name` is "tuned" or "bakeoff".
func show_profile_toast(profile_name: String) -> void:
	_profile_toast_label.text = PROFILE_TOAST_LABELS.get(profile_name, profile_name)
	if _profile_toast_tween and _profile_toast_tween.is_valid():
		_profile_toast_tween.kill()
	_profile_toast.modulate.a = 1.0
	_profile_toast_tween = create_tween()
	_profile_toast_tween.tween_interval(0.9)
	_profile_toast_tween.tween_property(_profile_toast, "modulate:a", 0.0, 0.3)


## Refreshes the info readout, resonance indicator, and resonance vignette
## every tick.
func update_state(player: Node, model_state: Dictionary, deaths: int, time_s: float) -> void:
	var model: String = String(model_state.get("model", "none"))
	var model_label: String = MODEL_LABELS.get(model, model)
	var profile_name: String = String(model_state["profile_name"])
	var state_name: String = String(player.state) if player != null else ""
	_model_label.text = model_label
	_info_label.text = "%s\nprofile: %s   state: %s\nDeaths: %d   Time: %.1fs" % [
		_experiment.get("title", ""), profile_name, state_name, deaths, time_s,
	]
	_resonance.set_state(model_state)
	_update_vignette(model_state)


func _update_vignette(model_state: Dictionary) -> void:
	var colors: Array = model_state.get("colors", [])
	var active: bool = colors.size() > 0
	var target_alpha := 0.0
	if active:
		var color_key: String = String(colors[0])
		_vignette_color = COLOR_PALETTE.get(color_key, RESONANCE_NEUTRAL)
		# "Fading with the window/breath": scale intensity by whichever timed
		# resource is draining (ability_window's countdown, hold_breath's
		# meter), so the ambient cue visibly runs out alongside the HUD
		# indicator. pick_color has neither (-1 for both) and stays at full
		# intensity while its color is selected, since there's nothing to
		# drain.
		var timer_frac: float = float(model_state.get("timer_frac", -1.0))
		var breath_frac: float = float(model_state.get("breath_frac", -1.0))
		var frac := 1.0
		if timer_frac >= 0.0:
			frac = timer_frac
		elif breath_frac >= 0.0:
			frac = breath_frac
		var breath: float = 1.0 - RESONANCE_VIGNETTE_BREATH_AMPLITUDE * 0.5 * (1.0 - sin(Time.get_ticks_msec() / 1000.0 * TAU * RESONANCE_VIGNETTE_BREATH_FREQ))
		target_alpha = RESONANCE_VIGNETTE_MAX_ALPHA * clampf(frac, 0.0, 1.0) * breath
	_vignette_alpha = move_toward(_vignette_alpha, target_alpha, TICK_DT * RESONANCE_VIGNETTE_LERP_SPEED)
	_resonance_vignette.modulate = Color(_vignette_color.r, _vignette_color.g, _vignette_color.b, _vignette_alpha)


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
