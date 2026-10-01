# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# Minimal placeholder HUD: plain text labels, no bars/rings/portraits.
# lab/ui/hud.gd (class_name LabHud extends CanvasLayer, same show_room/
# update_state methods) replaces this script on the same "HudLayer" node
# later; main.gd's call sites don't change.
extends CanvasLayer

const TITLE_CARD_TICKS := 90  # 1.5s @ 60 ticks/s

var _status_label: Label
var _title_label: Label
var _hint_label: Label
var _title_ticks_left := 0

func _ready() -> void:
	_status_label = Label.new()
	_status_label.add_theme_font_size_override("font_size", 20)
	_status_label.position = Vector2(16, 16)
	add_child(_status_label)

	_title_label = Label.new()
	_title_label.add_theme_font_size_override("font_size", 40)
	_title_label.position = Vector2(0, 360)
	_title_label.size = Vector2(1920, 60)
	_title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title_label.visible = false
	add_child(_title_label)

	_hint_label = Label.new()
	_hint_label.add_theme_font_size_override("font_size", 22)
	_hint_label.position = Vector2(0, 430)
	_hint_label.size = Vector2(1920, 40)
	_hint_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_hint_label.visible = false
	add_child(_hint_label)

## experiment/room are plain Dictionaries ({"title", "question", ...} /
## {"title", "hint", "id"}) so this matches lab/ui/hud.gd's exact signature.
func show_room(_experiment: Dictionary, room: Dictionary) -> void:
	_title_label.text = str(room.get("title", ""))
	_hint_label.text = str(room.get("hint", ""))
	_title_label.visible = true
	_hint_label.visible = true
	_title_ticks_left = TITLE_CARD_TICKS

## Called once per physics tick by main.gd so the title card timing is
## tick-exact rather than wall-clock.
func tick_title() -> void:
	if _title_ticks_left > 0:
		_title_ticks_left -= 1
		if _title_ticks_left == 0:
			_title_label.visible = false
			_hint_label.visible = false

func update_state(player: LabPlayer, model_state: Dictionary, deaths: int, time_s: float) -> void:
	var lines: PackedStringArray = []
	lines.append("Experiment: %s" % str(model_state.get("experiment_title", "")))
	var model_name := str(model_state.get("model", ""))
	lines.append("Model: %s" % ResonanceFactory.label(model_name))
	lines.append("Profile: %s" % str(model_state.get("profile_name", "")))
	lines.append("Deaths: %d    Time: %.1fs" % [deaths, time_s])
	lines.append("State: %s" % str(player.state))
	var colors: Array = model_state.get("colors", [])
	lines.append("Resonating: %s" % (", ".join(colors) if not colors.is_empty() else "-"))
	var selected := str(model_state.get("selected", ""))
	if selected != "":
		lines.append("Selected: %s" % selected)
	var timer_frac: float = model_state.get("timer_frac", -1.0)
	if timer_frac >= 0.0:
		lines.append("Window: %d%%" % int(round(timer_frac * 100.0)))
	var breath_frac: float = model_state.get("breath_frac", -1.0)
	if breath_frac >= 0.0:
		lines.append("Breath: %d%%" % int(round(breath_frac * 100.0)))
	_status_label.text = "\n".join(lines)
