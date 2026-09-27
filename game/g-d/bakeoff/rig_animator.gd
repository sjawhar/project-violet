class_name RigAnimator
extends RefCounted
## Picks the character's animation from the player's movement state and keeps its clock (plan Task 7 Step 19, with
## the Rig reader in place of spine-godot). THROWAWAY bake-off code; dimension-agnostic (G-D copies it unchanged).
## Priority: dash; airborne: double_jump once the double jump is used, else jump while rising, else fall; the landing
## frame starts land, which plays once to its end; then run while moving, else idle. Every other animation loops for
## as long as its state lasts (character-rig.md: every animation in the subset loops).
const ANIMATIONS := ["idle", "run", "jump", "fall", "land", "dash", "double_jump"]
var rig: Rig
var animation := "idle"
var time := 0.0
var _was_on_floor := true

func _init(rig_: Rig) -> void:
	rig = rig_
	for anim_name: String in ANIMATIONS: assert(rig.has_animation(anim_name), "the rig has no %s animation" % anim_name)

## Advances by DELTA seconds with the player's state as of this frame.
func advance(delta: float, dashing: bool, on_floor: bool, rising: bool, double_jumped: bool, moving: bool) -> void:
	var next: String
	if dashing: next = "dash"
	elif not on_floor: next = "double_jump" if double_jumped else "jump" if rising else "fall"
	elif not _was_on_floor or (animation == "land" and time < rig.duration("land")): next = "land"
	elif moving: next = "run"
	else: next = "idle"
	_was_on_floor = on_floor
	if next == animation: time += delta
	else: animation = next; time = 0.0

## Rig.pose for the current animation and time.
func pose() -> Dictionary:
	return rig.pose(animation, time)
