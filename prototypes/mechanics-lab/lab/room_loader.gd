# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# Parses `violet-lab-room` v1 (shape of docs/bakeoff/greybox-format.md plus
# "title"/"hint"). Kinds: empty solid start goal hazard wall_<c> platform_<c>
# orb_<c> (c in red/green/yellow/blue) cracked anchor side_exit. Round 2
# extension: an optional top-level "links" object ({"goal": room_id,
# "side_exit": room_id}) overrides a "goal"/"side_exit" cell's default
# destination; see RoomData.links and lab/main.gd._on_player_reached_goal.
class_name RoomLoader
extends RefCounted

const VALID_PREFIXED_COLORS: Array[String] = ["red", "green", "yellow", "blue"]
const VALID_PLAIN_KINDS: Array[String] = ["empty", "solid", "start", "goal", "hazard", "cracked", "anchor", "side_exit"]

static func _is_valid_kind(kind: String) -> bool:
	if VALID_PLAIN_KINDS.has(kind):
		return true
	for prefix in ["wall_", "platform_", "orb_"]:
		if kind.begins_with(prefix) and VALID_PREFIXED_COLORS.has(kind.substr(prefix.length())):
			return true
	return false

## `room_id` names the file (res://rooms/<room_id>.room.json) and becomes RoomData.id.
static func load_room(room_id: String) -> RoomData:
	var path := "res://rooms/%s.room.json" % room_id
	if not FileAccess.file_exists(path):
		push_error("RoomLoader: no such room file: " + path)
		return null
	var text := FileAccess.get_file_as_string(path)
	var parsed: Variant = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("RoomLoader: %s did not parse to a JSON object" % path)
		return null
	var data: Dictionary = parsed
	if data.get("format", "") != "violet-lab-room":
		push_error("RoomLoader: %s has wrong format %s" % [path, data.get("format", "<missing>")])
		return null
	if int(data.get("version", 0)) != 1:
		push_error("RoomLoader: %s has unsupported version %s" % [path, data.get("version", "<missing>")])
		return null

	var room := RoomData.new()
	room.id = room_id
	room.title = str(data.get("title", room_id))
	room.hint = str(data.get("hint", ""))
	room.tile_size_px = float(data.get("tile_size_px", 64))
	var links: Dictionary = data.get("links", {})
	for key in links:
		room.links[str(key)] = str(links[key])

	var legend: Dictionary = data.get("legend", {})
	var rows_strs: Array = data.get("rows", [])
	room.rows = rows_strs.size()
	room.cols = 0 if room.rows == 0 else (rows_strs[0] as String).length()

	var found_start := false
	var found_goal := false
	for row_idx in range(room.rows):
		var row_str: String = rows_strs[row_idx]
		if row_str.length() != room.cols:
			push_error("RoomLoader: %s row %d has length %d, expected %d" % [path, row_idx, row_str.length(), room.cols])
		var row_kinds: Array[String] = []
		row_kinds.resize(room.cols)
		for col_idx in range(row_str.length()):
			var ch := row_str.substr(col_idx, 1)
			var kind: String = legend.get(ch, "")
			if kind == "":
				push_error("RoomLoader: %s cell (%d,%d) char '%s' not in legend" % [path, col_idx, row_idx, ch])
				kind = "solid"
			elif not _is_valid_kind(kind):
				push_error("RoomLoader: %s cell (%d,%d) has unknown kind '%s'" % [path, col_idx, row_idx, kind])
				kind = "solid"
			row_kinds[col_idx] = kind
			var cell := Vector2i(col_idx, row_idx)
			match kind:
				"start":
					room.start_cell = cell
					found_start = true
				"goal":
					room.goal_cell = cell
					found_goal = true
				"cracked":
					room.cracked_cells.append(cell)
				"anchor":
					room.anchor_cells.append(cell)
				"side_exit":
					room.side_exit_cells.append(cell)
				_:
					if kind.begins_with("orb_"):
						room.orbs.append({"cell": cell, "color": kind.substr(4)})
		room.grid.append(row_kinds)

	if not found_start:
		push_error("RoomLoader: %s has no start cell" % path)
	if not found_goal:
		push_error("RoomLoader: %s has no goal cell" % path)
	if not room.side_exit_cells.is_empty() and not room.links.has("side_exit"):
		push_error("RoomLoader: %s has a side_exit cell but no links.side_exit destination" % path)
	return room
