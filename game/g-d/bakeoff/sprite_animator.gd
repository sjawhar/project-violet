class_name SpriteAnimator
extends RefCounted
## Picks the character's animation from the player's movement state and keeps its clock. THROWAWAY bake-off code;
## dimension-agnostic. Priority: dash; airborne: double_jump once the double jump is used, else jump while rising, else
## fall; the landing frame starts land, which plays to its end; then run while moving, else idle. Sprites.frame loops
## idle and run and holds the others on their last frame.
const ANIMATIONS := ["idle", "run", "jump", "fall", "land", "dash", "double_jump"]
var sprites: Sprites
var animation := "idle"
var time := 0.0
var _was_on_floor := true

## False after a push_error when SPRITES lack one of ANIMATIONS; a SpriteAnimator needs them all.
static func check(sprites_: Sprites) -> bool:
	for anim_name: String in ANIMATIONS:
		if not sprites_.has_animation(anim_name):
			push_error("%s: the sprites have no %s animation" % [sprites_.source, anim_name])
			return false
	return true

func _init(sprites_: Sprites) -> void:
	sprites = sprites_

## Advances by DELTA seconds with the player's state as of this frame.
func advance(delta: float, dashing: bool, on_floor: bool, rising: bool, double_jumped: bool, moving: bool) -> void:
	var next: String
	if dashing: next = "dash"
	elif not on_floor: next = "double_jump" if double_jumped else "jump" if rising else "fall"
	elif not _was_on_floor or (animation == "land" and time < sprites.duration("land")): next = "land"
	elif moving: next = "run"
	else: next = "idle"
	_was_on_floor = on_floor
	if next == animation: time += delta
	else: animation = next; time = 0.0

func frame() -> Sprites.Frame:
	return sprites.frame(animation, time)
