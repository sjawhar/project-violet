class_name SpriteCharacter2D
extends Node2D
## The painted protagonist in 2D: the current frame's body layer, then its scarf layer drawn over it, each a Sprite2D
## placed so its anchor pixel sits on the parent Player2D's ground point (centered off, offset = -anchor). The frame
## follows the player's state (SpriteAnimator). Scaled so the character is 1.6 tiles tall, mirrored to the player's
## facing; the scarf layer is neutral gray, multiplied by the active colour (gray when none). THROWAWAY.
const SCARF_COLORS := {"red": Color("#e04a3a"), "green": Color("#3fbf6a"), "": Color(0.55, 0.55, 0.55)}
var sprites: Sprites
var animator: SpriteAnimator
var player: Player2D
var body := Sprite2D.new()
var scarf := Sprite2D.new()

## The character for SPRITES, or null after a push_error when the set lacks an animation SpriteAnimator needs.
static func create(sprites_: Sprites) -> SpriteCharacter2D:
	if not SpriteAnimator.check(sprites_): return null
	return SpriteCharacter2D.new(sprites_)

## Use create(), which checks the set first.
func _init(sprites_: Sprites) -> void:
	sprites = sprites_; name = "Character"
	animator = SpriteAnimator.new(sprites)
	for layer: Sprite2D in [body, scarf]:  # scarf added last, so it draws over the body
		layer.centered = false
		layer.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		add_child(layer)
	body.name = "Body"; scarf.name = "Scarf"

func _ready() -> void:
	player = get_parent() as Player2D
	if player == null: player = get_parent().get_parent() as Player2D  # inside the outline CanvasGroup
	assert(player != null, "SpriteCharacter2D must sit under the Player2D")
	Resonance.changed.connect(_color_scarf); _color_scarf()
	_apply()

func _process(delta: float) -> void:
	animator.advance(delta, player.dash_ticks_left > 0, player.is_on_floor(), player.velocity.y < 0.0,
		player.double_jump_used, absf(player.velocity.x) > 1.0)
	_apply()

func _apply() -> void:
	show_frame(animator.frame(), player.facing)

## Shows FRAME (layer name -> Sprites.Layer), mirrored for FACING (1 right, -1 left) about the root.
func show_frame(frame: Dictionary, facing: int) -> void:
	scale = Vector2(facing, 1.0) * (1.6 * Player2D.TILE / sprites.height_px)
	for pair: Array in [[body, frame["body"]], [scarf, frame["scarf"]]]:
		var sprite: Sprite2D = pair[0]; var layer: Sprites.Layer = pair[1]
		sprite.texture = layer.texture
		sprite.offset = -layer.anchor

func _color_scarf() -> void:
	scarf.modulate = SCARF_COLORS[Resonance.active]
