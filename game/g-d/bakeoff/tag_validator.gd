class_name TagValidator
extends RefCounted
## Every tagged cell in the level has exactly one tagged body with the right color and kind; no body is
## tagged where the level has none; every tagged body has a visual that reacts. Empty result = OK. THROWAWAY.
static func validate(level: Greybox, tree: SceneTree) -> PackedStringArray:
	var problems: PackedStringArray = []; var seen := {}
	for tag in tree.get_nodes_in_group("resonance"):
		var body: Node = tag.get_parent(); var actual := "%s_%s" % [tag.kind, tag.color]
		var expected := level.kind_at(tag.cell.x, tag.cell.y)
		if expected != actual: problems.append("%s: tagged %s but the level has %s at %s" % [body.get_path(), actual, expected, tag.cell])
		var key := "%d,%d" % [tag.cell.x, tag.cell.y]
		if seen.has(key): problems.append("%s: second tag for cell %s" % [body.get_path(), tag.cell])
		seen[key] = true
		if body.get_children().filter(func(c): return c.has_method("set_resonance_look")).is_empty():
			problems.append("%s: no visual implements set_resonance_look" % body.get_path())
	for kind in Greybox.TAGGED:
		for cell in level.cells_of(kind):
			if not seen.has("%d,%d" % [cell.x, cell.y]): problems.append("cell %s: level has %s but the scene has no tagged body there" % [cell, kind])
	return problems
