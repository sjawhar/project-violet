class_name SpriteCharacter2D
extends Node2D
## The painted Violet in 2D (violet-sprites v1): a body Sprite2D and a scarf Sprite2D drawn over it, showing the frame
## CharacterAnimator picks from the parent Player2D's state. Each layer's anchor pixel sits on this node's origin, the
## player's ground point; scaled so idle frame 0 is 1.6 tiles tall, mirrored for facing left; the gray scarf is
## multiplied by the active color. THROWAWAY.
const SCARF_COLORS := {"red": Color("#e04a3a"), "green": Color("#3fbf6a"), "": Color(0.55, 0.55, 0.55)}
var sprites: VioletSprites
var animator: CharacterAnimator
var player: Player2D
var body := Sprite2D.new()
var scarf := Sprite2D.new()

## The character for SPRITES, or null after a push_error when it lacks an animation CharacterAnimator needs.
static func create(sprites_: VioletSprites) -> SpriteCharacter2D:
	if not CharacterAnimator.check(sprites_): return null
	return SpriteCharacter2D.new(sprites_)

## Use create(), which checks the animations first.
func _init(sprites_: VioletSprites) -> void:
	sprites = sprites_; name = "Character"
	animator = CharacterAnimator.new(sprites)
	for pair: Array in [[body, "Body"], [scarf, "Scarf"]]:  # the scarf after the body, so it draws over it
		var sprite: Sprite2D = pair[0]
		sprite.name = pair[1]; sprite.centered = false
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS  # ~1000 px frames drawn ~100 px tall
		add_child(sprite)

func _ready() -> void:
	var node := get_parent()
	while node != null and node is not Player2D: node = node.get_parent()  # the art may wrap her, e.g. in a CanvasGroup
	player = node as Player2D
	assert(player != null, "SpriteCharacter2D must be inside the Player2D")
	Resonance.changed.connect(_color_scarf); _color_scarf()
	show_frame(animator.frame(), player.facing)

func _process(delta: float) -> void:
	animator.advance(delta, player.dash_ticks_left > 0, player.is_on_floor(), player.velocity.y < 0.0,
		player.double_jump_used, absf(player.velocity.x) > 1.0)
	show_frame(animator.frame(), player.facing)

## Shows FRAME with each layer's anchor pixel on this node's origin. The frames face right; facing left (-1) mirrors
## the root with a negative x scale (character-rig.md).
func show_frame(frame: VioletSprites.Frame, facing: int) -> void:
	scale = Vector2(facing, 1.0) * (1.6 * Player2D.TILE / sprites.height_px)
	for pair: Array in [[body, frame.body], [scarf, frame.scarf]]:
		var sprite: Sprite2D = pair[0]; var layer: VioletSprites.Layer = pair[1]
		sprite.texture = layer.texture
		sprite.offset = -layer.anchor

func _color_scarf() -> void:
	scarf.modulate = SCARF_COLORS[Resonance.active]
