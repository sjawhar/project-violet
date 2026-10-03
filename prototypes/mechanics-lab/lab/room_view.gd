# THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md.
#
# Minimal placeholder room renderer: flat-colored rectangles per cell kind.
# Walls are hatched, platforms get a flat highlight strip (visually distinct
# per DESIGN.md); a resonating color's tagged geometry draws as a faint
# dashed outline instead of filled. lab/juice/* replaces per-tile drawing
# with real art later; this node (and its setup() call site in main.gd) can
# simply be deleted once that lands.
extends Node2D

const PALETTE := {
	"background": Color("#1F2430"),
	"solid": Color("#3A4150"),
	"solid_edge": Color("#5A6375"),
	"red": Color("#E5553F"),
	"green": Color("#4CC27A"),
	"yellow": Color("#F2C94C"),
	"blue": Color("#4A90E2"),
	"neutral": Color("#9AA0A6"),
	"hazard": Color("#9B5DE5"),
	"hazard_tip": Color("#E8D9FF"),
	"goal": Color("#FFFFFF"),
	"side_exit": Color("#F2994A"),
}

var _room: RoomData
var _resonating_fn: Callable
## Round 2 extension: "" is fine (field tests before the chapter prototype
## never had an unacquired color on screen), so this stays an optional
## third argument rather than a required one. `c -> bool`: whether the
## player currently has color `c`, per docs/bakeoff/mechanic.md's reveal --
## tagged geometry of a color not yet acquired renders grayscale.
var _has_color_fn: Callable

func setup(room: RoomData, resonating_fn: Callable, has_color_fn: Callable = Callable()) -> void:
	_room = room
	_resonating_fn = resonating_fn
	_has_color_fn = has_color_fn
	# Player juice's Scarf tail is absolute z_index -1 (behind the player's
	# own body, which sits at the default 0) so it trails *behind* the
	# player per DESIGN.md. Without this, this node's own default z_index
	# (0, tied with the body) draws its opaque background rect over the
	# tail every frame, hiding the scarf's entire trailing ribbon behind
	# the room -- only its neck wrap (absolute z_index 1) ever showed.
	z_index = -2
	set_process(true)
	queue_redraw()

func _has_color(c: String) -> bool:
	return not _has_color_fn.is_valid() or bool(_has_color_fn.call(c))

func _process(_delta: float) -> void:
	queue_redraw()

func _draw() -> void:
	if _room == null:
		return
	var ts: float = _room.tile_size_px
	draw_rect(Rect2(Vector2.ZERO, Vector2(_room.cols, _room.rows) * ts), PALETTE["background"])
	var resonating: Array = _resonating_fn.call() if _resonating_fn.is_valid() else []
	for row in range(_room.rows):
		var row_kinds: Array = _room.grid[row]
		for col in range(_room.cols):
			var kind: String = row_kinds[col]
			if kind == "empty" or kind == "start":
				continue
			var pos := Vector2(col, row) * ts
			var rect := Rect2(pos, Vector2(ts, ts))
			_draw_cell(kind, pos, rect, ts, Vector2i(col, row), resonating)

func _draw_cell(kind: String, pos: Vector2, rect: Rect2, ts: float, cell: Vector2i, resonating: Array) -> void:
	match kind:
		"solid":
			draw_rect(rect, PALETTE["solid"])
			draw_rect(Rect2(pos, Vector2(ts, 4.0)), PALETTE["solid_edge"])
		"hazard":
			draw_rect(rect, PALETTE["hazard"])
			var spikes := 3
			for i in range(spikes):
				var x0: float = pos.x + i * ts / float(spikes)
				var w: float = ts / float(spikes)
				var tip := Vector2(x0 + w * 0.5, pos.y + ts * 0.35)
				draw_colored_polygon(PackedVector2Array([
					Vector2(x0, pos.y + ts), tip, Vector2(x0 + w, pos.y + ts),
				]), PALETTE["background"])
				draw_circle(tip, maxf(w * 0.12, 2.0), PALETTE["hazard_tip"])
		"goal":
			draw_rect(rect, Color(1.0, 1.0, 1.0, 0.12))
			draw_rect(rect.grow(-8.0), PALETTE["goal"])
		"side_exit":
			# Visibly distinct from "goal" (a diamond in side_exit's own
			# amber, vs. a plain white square): DESIGN.md requires a side
			# room's exit to be marked, not merely functional.
			draw_rect(rect, Color(1.0, 1.0, 1.0, 0.1))
			var c := pos + Vector2(ts, ts) * 0.5
			var r := ts * 0.3
			draw_colored_polygon(PackedVector2Array([
				c + Vector2(0, -r), c + Vector2(r, 0), c + Vector2(0, r), c + Vector2(-r, 0),
			]), PALETTE["side_exit"])
		"cracked":
			if not _room.broken.get(cell, false):
				draw_rect(rect, PALETTE["solid"])
				draw_line(pos, pos + Vector2(ts, ts), PALETTE["background"], 2.0)
				draw_line(pos + Vector2(ts, 0.0), pos + Vector2(0.0, ts), PALETTE["background"], 2.0)
		"anchor":
			var center := pos + Vector2(ts, ts) * 0.5
			var anchor_color: Color = PALETTE["blue"] if _has_color("blue") else PALETTE["neutral"]
			draw_arc(center, ts * 0.34, 0.0, TAU, 32, anchor_color, 3.0)
			draw_circle(center, ts * 0.16, anchor_color)
		_:
			if kind.begins_with("orb_"):
				var oc: String = kind.substr(4)
				draw_circle(pos + Vector2(ts, ts) * 0.5, ts * 0.22, PALETTE.get(oc, PALETTE["neutral"]))
			elif kind.begins_with("wall_") or kind.begins_with("platform_"):
				var is_wall := kind.begins_with("wall_")
				var color_name: String = kind.substr(kind.find("_") + 1)
				var acquired := _has_color(color_name)
				var base_color: Color = PALETTE.get(color_name, PALETTE["neutral"]) if acquired else PALETTE["neutral"]
				if acquired and resonating.has(color_name):
					draw_rect(rect, Color(base_color.r, base_color.g, base_color.b, 0.16))
					_draw_dashed_rect(rect, base_color)
				else:
					draw_rect(rect, base_color)
					if is_wall:
						_draw_hatch(rect)
					else:
						draw_rect(Rect2(pos, Vector2(ts, 6.0)), Color(1.0, 1.0, 1.0, 0.35))

func _draw_hatch(rect: Rect2) -> void:
	var step: float = rect.size.x / 4.0
	var i := -1
	while i < 5:
		var x: float = rect.position.x + i * step
		draw_line(Vector2(x, rect.position.y + rect.size.y), Vector2(x + rect.size.y, rect.position.y), Color(0.0, 0.0, 0.0, 0.25), 2.0)
		i += 1

func _draw_dashed_rect(rect: Rect2, color: Color) -> void:
	var dash := 8.0
	var gap := 6.0
	var corners: Array[Vector2] = [
		rect.position,
		rect.position + Vector2(rect.size.x, 0.0),
		rect.position + rect.size,
		rect.position + Vector2(0.0, rect.size.y),
	]
	for i in range(4):
		var a: Vector2 = corners[i]
		var b: Vector2 = corners[(i + 1) % 4]
		var total := a.distance_to(b)
		if total <= 0.0:
			continue
		var dir := (b - a) / total
		var t := 0.0
		while t < total:
			var seg_end: float = minf(t + dash, total)
			draw_line(a + dir * t, a + dir * seg_end, color, 2.0)
			t += dash + gap
