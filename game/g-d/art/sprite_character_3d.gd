class_name SpriteCharacter3D
extends Node3D
## The painted Violet in 3D (violet-sprites v1, docs/bakeoff/character-rig.md): a body Sprite3D and a scarf Sprite3D in
## the player's XY plane, showing the frame SpriteAnimator picks from the parent Player3D's state. Each layer's anchor
## pixel sits on the player's ground point; pixel_size makes 1.6 m out of height_px. The scarf is drawn over the body,
## and its neutral gray takes the active color. Sprites are shaded, so the sun and the scene lights reach the character.
## Facing left mirrors both layers about the root, each sprite flipped and moved rather than the root scaled by -1,
## because a negative scale turns the shaded Sprite3Ds' normals away from the sun. THROWAWAY.
const SCARF_COLORS := {"red": Color("#e04a3a"), "green": Color("#3fbf6a"), "": Color(0.55, 0.55, 0.55)}
## The scarf sits this far in front of the body, and sorts after it, so it is drawn over it.
const LAYER_GAP := 0.002
var sprites: Sprites
var animator: SpriteAnimator
var player: Player3D
var body: Sprite3D
var scarf: Sprite3D
var _pixel_size: float

## The character for SPRITES, or null after a push_error when they lack an animation SpriteAnimator needs.
static func create(sprites_: Sprites) -> SpriteCharacter3D:
	if not SpriteAnimator.check(sprites_): return null
	return SpriteCharacter3D.new(sprites_)

## Use create(), which checks the sprites first.
func _init(sprites_: Sprites) -> void:
	sprites = sprites_; name = "Character"
	animator = SpriteAnimator.new(sprites)
	_pixel_size = 1.6 / sprites.height_px
	body = _layer_sprite("Body", 0)
	scarf = _layer_sprite("Scarf", 1)
	scarf.position.z = LAYER_GAP

func _layer_sprite(layer_name: String, priority: int) -> Sprite3D:
	var sprite := Sprite3D.new(); sprite.name = layer_name
	sprite.pixel_size = _pixel_size; sprite.shaded = true; sprite.render_priority = priority
	sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	add_child(sprite)
	return sprite

func _ready() -> void:
	player = get_parent() as Player3D
	assert(player != null, "SpriteCharacter3D must be a child of the Player3D")
	Resonance.changed.connect(_color_scarf); _color_scarf()
	_apply()

func _process(delta: float) -> void:
	animator.advance(delta, player.dash_ticks_left > 0, player.is_on_floor(), player.velocity.y > 0.0,
		player.double_jump_used, absf(player.velocity.x) > 1.0 / 64.0)  # Player2D's 1 px/s, in metres
	_apply()

func _apply() -> void:
	var frame := animator.frame()
	_place(body, frame.body)
	_place(scarf, frame.scarf)

## Shows LAYER on SPRITE with its anchor pixel on the root. The sprite is centred, so its centre sits (size / 2 -
## anchor) image pixels from the root, with the image's y-down turned y-up and x mirrored when facing left.
func _place(sprite: Sprite3D, layer: Sprites.Layer) -> void:
	sprite.texture = layer.texture
	sprite.flip_h = player.facing < 0
	var size := layer.texture.get_size()
	sprite.position.x = player.facing * (size.x / 2.0 - layer.anchor.x) * _pixel_size
	sprite.position.y = (layer.anchor.y - size.y / 2.0) * _pixel_size

func _color_scarf() -> void:
	scarf.modulate = SCARF_COLORS[Resonance.active]
