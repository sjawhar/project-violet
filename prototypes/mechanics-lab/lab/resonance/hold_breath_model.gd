# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# "Hold to resonate": abilities always usable; `switch` cycles the selected
# color; holding `resonate` makes the selected color resonate, draining a
# breath meter of profile.breath_ticks; breath refills at 2x drain speed
# when not held.
class_name HoldBreathResonanceModel
extends ResonanceModel

var _selected: String = ""
var _breath_left: int = 0
var _held := false

func _init() -> void:
	model_name = &"hold_breath"

func setup(player: LabPlayer, profile: PhysicsProfile) -> void:
	super.setup(player, profile)
	_breath_left = profile.breath_ticks
	_pick_first_acquired()

func _acquired_in_order() -> Array:
	var out: Array = []
	for c in LabConstants.COLORS:
		if _player.has_color(c):
			out.append(c)
	return out

func _pick_first_acquired() -> void:
	if _selected != "" and _player.has_color(_selected):
		return
	var acquired := _acquired_in_order()
	_selected = acquired[0] if not acquired.is_empty() else ""

func on_switch_pressed() -> void:
	var acquired := _acquired_in_order()
	if acquired.is_empty():
		return
	var idx: int = acquired.find(_selected)
	_selected = acquired[(idx + 1) % acquired.size()]

func on_resonate_held(held: bool) -> void:
	_held = held

func tick() -> void:
	_pick_first_acquired()
	if _held and _selected != "" and _breath_left > 0:
		_breath_left = max(0, _breath_left - 1)
		if _breath_left == 0:
			_held = false
	else:
		_breath_left = min(_profile.breath_ticks, _breath_left + 2)

func is_resonating(color: String) -> bool:
	return _held and _breath_left > 0 and _selected != "" and color == _selected

func hud_state() -> Dictionary:
	var breath_frac := 0.0
	if _profile.breath_ticks > 0:
		breath_frac = float(_breath_left) / float(_profile.breath_ticks)
	return {"model": model_name, "colors": resonating_colors(), "selected": _selected, "timer_frac": -1.0, "breath_frac": breath_frac}
