class_name Greybox
extends RefCounted
## A violet-greybox v1 level (docs/bakeoff/greybox-format.md). THROWAWAY bake-off code; dimension-agnostic.
const KINDS := ["empty", "solid", "wall_red", "wall_green", "platform_red", "platform_green", "start", "goal", "orb_red", "orb_green", "hazard"]
## Tagged kind -> [color, shape].
const TAGGED := {"wall_red": ["red", "wall"], "wall_green": ["green", "wall"], "platform_red": ["red", "platform"], "platform_green": ["green", "platform"]}
var tile_px: int
var width: int
var height: int
## One kind per cell, row-major (index = row * width + col).
var cells: Array[String] = []

static func load_file(path: String) -> Greybox:
	var text := FileAccess.get_file_as_string(path)
	assert(text != "", "%s: cannot read (%s)" % [path, error_string(FileAccess.get_open_error())])
	var data: Variant = JSON.parse_string(text)
	assert(data is Dictionary, "%s: not a JSON object" % path)
	assert(data.get("format") == "violet-greybox" and int(data.get("version", 0)) == 1, "%s: not a violet-greybox v1 file" % path)
	var legend: Dictionary = data["legend"]
	for ch: String in legend: assert(legend[ch] in KINDS, "%s: legend %s has unknown kind %s" % [path, ch, legend[ch]])
	var rows: Array = data["rows"]
	var level := Greybox.new()
	level.tile_px = int(data["tile_size_px"]); level.height = rows.size(); level.width = String(rows[0]).length()
	for r in rows.size():
		var row := String(rows[r])
		assert(row.length() == level.width, "%s: row %d has %d columns, expected %d" % [path, r, row.length(), level.width])
		for c in row.length():
			assert(legend.has(row[c]), "%s: row %d col %d: character %s is not in the legend" % [path, r, c, row[c]])
			level.cells.append(String(legend[row[c]]))
	return level

## Out of range reads as solid, so the level is closed on every side.
func kind_at(col: int, row: int) -> String:
	if col < 0 or row < 0 or col >= width or row >= height: return "solid"
	return cells[row * width + col]

func cells_of(kind: String) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for i in cells.size(): if cells[i] == kind: out.append(Vector2i(i % width, i / width))
	return out

func single(kind: String) -> Vector2i:
	var found := cells_of(kind)
	assert(found.size() == 1, "expected exactly one %s, found %d" % [kind, found.size()])
	return found[0]
