# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# "Choose your color (bake-off)": `switch` cycles the acquired colors; the
# selected color always resonates; only its ability is usable.
class_name PickColorResonanceModel
extends ResonanceModel

var _selected: String = ""

func _init() -> void:
	model_name = &"pick_color"

func setup(player: LabPlayer, profile: PhysicsProfile) -> void:
	super.setup(player, profile)
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

func tick() -> void:
	_pick_first_acquired()

func is_resonating(color: String) -> bool:
	return _selected != "" and color == _selected

func can_use(color: String) -> bool:
	return color == _selected and super.can_use(color)

func hud_state() -> Dictionary:
	return {"model": model_name, "colors": resonating_colors(), "selected": _selected, "timer_frac": -1.0, "breath_frac": -1.0}
