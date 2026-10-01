# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# Base class for a resonance-color ability. lab/player.gd holds one instance
# per acquired ability (built by AbilityRegistry from experiments.json's
# `abilities` list) and drives it each physics tick:
#   - if an ability's physics_tick() returned true last tick, it still owns
#     movement: call physics_tick() again before any normal movement code.
#   - otherwise, on relevant input, call try_start(); if it returns true the
#     ability now owns movement starting next tick.
#   - on_landed() fires whenever LabPlayer transitions to on_floor, so an
#     ability can reset its "once per airborne period" state.
class_name Ability
extends RefCounted

## Resonance color this ability belongs to (see Constants.ABILITY_COLOR).
var color: String = ""

## `input` is the per-tick input snapshot LabPlayer builds (see
## LabPlayer._read_input): move_x/move_y (-1/0/1), jump_pressed/held/released,
## dash_pressed, ability_pressed, switch_pressed, resonate_held, facing.
## Returns true if this call activated the ability (it now owns movement).
func try_start(_player: LabPlayer, _input: Dictionary) -> bool:
	return false

## Called every physics tick while this ability owns movement. Returns true
## to keep owning movement next tick, false to hand control back.
func physics_tick(_player: LabPlayer) -> bool:
	return false

## Called whenever LabPlayer lands (on_floor becomes true).
func on_landed() -> void:
	pass
