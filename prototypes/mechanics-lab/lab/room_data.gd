# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# Parsed `violet-lab-room` v1 content (see lab/room_loader.gd). Collision
# queries here are the single source of truth the custom AABB mover
# (lab/player.gd) consults every sub-step, so replays stay deterministic.
class_name RoomData
extends RefCounted

var id := ""
var title := ""
var hint := ""
var tile_size_px := 64.0
var cols := 0
var rows := 0
## grid[row][col] = kind string ("empty", "solid", "start", "goal", "hazard",
## "wall_<color>", "platform_<color>", "orb_<color>", "cracked", "anchor").
var grid: Array = []
var start_cell := Vector2i.ZERO
var goal_cell := Vector2i.ZERO
## [{"cell": Vector2i, "color": String}, ...]
var orbs: Array[Dictionary] = []
var cracked_cells: Array[Vector2i] = []
var anchor_cells: Array[Vector2i] = []
var side_exit_cells: Array[Vector2i] = []
## Round 2 extension: optional per-kind destination override, parsed from
## the room JSON's top-level "links" object ({"goal": room_id, "side_exit":
## room_id}). Empty/missing "goal" means the default: the next room in the
## current experiment's `rooms` list (lab/main.gd._on_player_reached_goal).
## "side_exit" has no default; a side_exit cell with no link is a room-data
## error (see lab/room_loader.gd).
var links: Dictionary = {}
## Cracked cells broken by stomp this life; cleared on respawn (RoomData is
## re-loaded/reset per respawn by the room controller, see lab/main.gd).
var broken: Dictionary = {}

func kind_at(col: int, row: int) -> String:
	if col < 0 or row < 0 or col >= cols or row >= rows:
		return "solid"
	return grid[row][col]

func cell_center_px(col: int, row: int) -> Vector2:
	return Vector2((col + 0.5) * tile_size_px, (row + 0.5) * tile_size_px)

func world_rect_px() -> Rect2:
	return Rect2(Vector2.ZERO, Vector2(cols * tile_size_px, rows * tile_size_px))

## Whether the given color's tagged geometry (wall or platform alike) at this
## cell has collision disabled right now. `resonating` is the resonance
## model's current list of resonating color names.
func is_solid(col: int, row: int, resonating: Array) -> bool:
	var kind := kind_at(col, row)
	match kind:
		"solid":
			return true
		"cracked":
			return not broken.get(Vector2i(col, row), false)
		_:
			if kind.begins_with("wall_") or kind.begins_with("platform_"):
				var color := kind.substr(kind.find("_") + 1)
				return not resonating.has(color)
			return false

func is_hazard(col: int, row: int) -> bool:
	return kind_at(col, row) == "hazard"

func is_goal(col: int, row: int) -> bool:
	return kind_at(col, row) == "goal"

func is_side_exit(col: int, row: int) -> bool:
	return kind_at(col, row) == "side_exit"

func orb_color_at(col: int, row: int) -> String:
	var kind := kind_at(col, row)
	if kind.begins_with("orb_"):
		return kind.substr(kind.find("_") + 1)
	return ""

func break_cracked(col: int, row: int) -> void:
	broken[Vector2i(col, row)] = true

func reset_broken() -> void:
	broken.clear()
