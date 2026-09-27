class_name GreyboxBuilder3D
extends RefCounted
## Builds a Greybox level as 3D physics bodies and areas on the z = 0 plane (docs/bakeoff/greybox-format.md:
## cell (col, row) -> centre (col + 0.5, H - row - 0.5, 0) in metres, y up). THROWAWAY.
## Solid and tagged cells: StaticBody3D on layer 1. Goal, orbs and hazards: Area3D watching layer 2 (the player).
const AREA_KINDS := ["goal", "orb_red", "orb_green", "hazard"]

static func build(level: Greybox, root: Node3D, art: GreyboxArt3D) -> Dictionary:
	var info := {}
	for r in level.height:
		for c in level.width:
			var kind := level.kind_at(c, r)
			if kind == "empty": continue
			var cell := Vector2i(c, r)
			var pos := Vector3(c + 0.5, level.height - r - 0.5, 0)
			if kind == "start":
				info["start"] = Vector3(pos.x, pos.y - 0.5, 0)  # feet on the cell floor
				continue
			var node: CollisionObject3D
			if kind == "solid" or Greybox.TAGGED.has(kind):
				var body := StaticBody3D.new()
				body.collision_layer = 1; body.collision_mask = 0
				node = body
			elif kind in AREA_KINDS:
				var area := Area3D.new()
				area.collision_layer = 0; area.collision_mask = 2
				area.set_meta("kind", kind); area.add_to_group(kind)
				node = area
			else:
				assert(false, "cell %s: no builder for kind %s" % [cell, kind])
			node.name = "%s_%d_%d" % [kind, c, r]
			node.position = pos
			var shape := CollisionShape3D.new()
			var box := BoxShape3D.new(); box.size = Vector3.ONE; shape.shape = box
			node.add_child(shape)
			node.add_child(art.make_cell(kind, cell))
			if Greybox.TAGGED.has(kind):
				var tag := ResonanceTag.new()
				tag.name = "ResonanceTag"
				tag.color = Greybox.TAGGED[kind][0]; tag.kind = Greybox.TAGGED[kind][1]; tag.cell = cell
				node.add_child(tag)
			root.add_child(node)
	return info
