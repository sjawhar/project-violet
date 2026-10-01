# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
class_name ResonanceModel
extends RefCounted

## "none" | "ability_window" | "pick_color" | "hold_breath".
var model_name: StringName = &""

var _player: LabPlayer
var _profile: PhysicsProfile

func setup(player: LabPlayer, profile: PhysicsProfile) -> void:
	_player = player
	_profile = profile

func on_ability_used(_color: String) -> void:
	pass

func on_switch_pressed() -> void:
	pass

func on_resonate_held(_held: bool) -> void:
	pass

## Advance one physics tick (timers, breath meter, ...).
func tick() -> void:
	pass

func is_resonating(_color: String) -> bool:
	return false

## Whether `color`'s ability may be used right now. Default: usable once
## acquired; pick_color narrows this to the selected color only.
func can_use(color: String) -> bool:
	return _player != null and _player.has_color(color)

func hud_state() -> Dictionary:
	return {"model": model_name, "colors": [], "selected": "", "timer_frac": -1.0, "breath_frac": -1.0}

## All currently resonating colors (LabConstants.COLORS order), for
## LabPlayer.resonance_changed and the room's collision/visual queries.
func resonating_colors() -> Array:
	var out: Array = []
	for c in LabConstants.COLORS:
		if is_resonating(c):
			out.append(c)
	return out
