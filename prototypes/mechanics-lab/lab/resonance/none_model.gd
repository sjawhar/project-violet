# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# `feel` experiment: nothing ever resonates; abilities usable once acquired.
class_name NoneResonanceModel
extends ResonanceModel

func _init() -> void:
	model_name = &"none"

func is_resonating(_color: String) -> bool:
	return false

func hud_state() -> Dictionary:
	return {"model": model_name, "colors": [], "selected": "", "timer_frac": -1.0, "breath_frac": -1.0}
