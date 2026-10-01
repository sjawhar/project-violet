extends Node3D
## THROWAWAY helper for tests/sprite_test.gd: attaches the character from --sprites=PATH to a player the way the game
## does (GreyboxArt3D.attach_sprites), then exits 0. Sprites that do not load make attach_sprites quit with 1.
func _ready() -> void:
	var path := ""
	for a in OS.get_cmdline_user_args(): if a.begins_with("--sprites="): path = a.substr(10)
	var player := Player3D.new(); add_child(player)
	GreyboxArt3D.attach_sprites(player, path)
	if player.has_node("Character"): get_tree().quit(0)
