# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# "Ability triggers resonance (2019 design)": abilities always usable once
# acquired; using one makes its color resonate for profile.resonance_ticks
# from that tick; a new color replaces the old one (not additive).
class_name AbilityWindowResonanceModel
extends ResonanceModel

var _active_color: String = ""
var _ticks_left: int = 0

func _init() -> void:
	model_name = &"ability_window"

func on_ability_used(color: String) -> void:
	_active_color = color
	_ticks_left = _profile.resonance_ticks

func tick() -> void:
	if _ticks_left > 0:
		_ticks_left -= 1
		if _ticks_left == 0:
			_active_color = ""

func is_resonating(color: String) -> bool:
	return _ticks_left > 0 and color == _active_color

func hud_state() -> Dictionary:
	var frac := -1.0
	if _ticks_left > 0 and _profile.resonance_ticks > 0:
		frac = float(_ticks_left) / float(_profile.resonance_ticks)
	return {"model": model_name, "colors": resonating_colors(), "selected": _active_color, "timer_frac": frac, "breath_frac": -1.0}
