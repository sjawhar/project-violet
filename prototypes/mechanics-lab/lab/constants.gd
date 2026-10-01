# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
class_name LabConstants
extends RefCounted

const TILE_SIZE_PX := 64.0
## Resonance colors, in switch-cycle order.
const COLORS: Array[String] = ["red", "green", "yellow", "blue"]
## Custom AABB-vs-grid movement moves in sub-steps of at most this many px
## per axis per tick, so fast motion (dash, high fall speed) can't tunnel
## through a one-tile-thick wall.
const MAX_SUBSTEP_PX := 8.0
## Ability color -> action name that triggers it.
const ABILITY_ACTION := {
	"dash": "dash",
	"double_jump": "jump",
}
## Ability name -> the color it belongs to (and resonates on use).
const ABILITY_COLOR := {
	"dash": "red",
	"double_jump": "green",
	"stomp": "yellow",
	"blink": "blue",
	"swing": "blue",
}
