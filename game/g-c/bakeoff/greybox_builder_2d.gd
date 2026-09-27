class_name GreyboxBuilder2D
extends RefCounted
## Builds a Greybox level as 2D physics bodies and areas (docs/bakeoff/greybox-format.md). THROWAWAY.
## Solid and tagged cells: StaticBody2D on layer 1. Goal, orbs and hazards: Area2D watching layer 2 (the player).
const AREA_KINDS := ["goal", "orb_red", "orb_green", "hazard"]

static func build(level: Greybox, root: Node2D, art: GreyboxArt) -> Dictionary:
	var info := {}
	var ts := float(level.tile_px)
	for r in level.height:
		for c in level.width:
			var kind := level.kind_at(c, r)
			if kind == "empty": continue
			var cell := Vector2i(c, r)
			var pos := Vector2((c + 0.5) * ts, (r + 0.5) * ts)
			if kind == "start":
				info["start"] = Vector2(pos.x, (r + 1) * ts)  # feet on the cell floor
				continue
			var node: CollisionObject2D
			if kind == "solid" or Greybox.TAGGED.has(kind):
				var body := StaticBody2D.new()
				body.collision_layer = 1; body.collision_mask = 0
				node = body
			elif kind in AREA_KINDS:
				var area := Area2D.new()
				area.collision_layer = 0; area.collision_mask = 2
				area.set_meta("kind", kind); area.add_to_group(kind)
				node = area
			else:
				assert(false, "cell %s: no builder for kind %s" % [cell, kind])
			node.name = "%s_%d_%d" % [kind, c, r]
			node.position = pos
			var shape := CollisionShape2D.new()
			var rect := RectangleShape2D.new(); rect.size = Vector2(ts, ts); shape.shape = rect
			node.add_child(shape)
			node.add_child(art.make_cell(kind, cell, ts))
			if Greybox.TAGGED.has(kind):
				var tag := ResonanceTag.new()
				tag.name = "ResonanceTag"
				tag.color = Greybox.TAGGED[kind][0]; tag.kind = Greybox.TAGGED[kind][1]; tag.cell = cell
				node.add_child(tag)
			root.add_child(node)
	return info
