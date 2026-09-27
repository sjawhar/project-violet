extends Node2D
## THROWAWAY color-tag check. godot --headless --path game/g-c res://tests/validate_tags.tscn [-- --mutate]
## Builds the level with the default art, runs TagValidator, prints each problem to stderr and
## `tag-check: N problem(s)`; exits 0 iff N == 0. --mutate first removes one tag: that run must fail.
func _ready() -> void:
	var game := Game2D.new(); game.name = "Game"; add_child(game)
	if OS.get_cmdline_user_args().has("--mutate"):
		var victim: Node = get_tree().get_nodes_in_group("resonance")[0]
		print("mutate: removed the tag on %s" % victim.get_parent().get_path())
		victim.get_parent().remove_child(victim); victim.free()
	var problems := TagValidator.validate(game.level, get_tree())
	for p in problems: printerr(p)
	print("tag-check: %d problem(s)" % problems.size())
	get_tree().quit(0 if problems.is_empty() else 1)
