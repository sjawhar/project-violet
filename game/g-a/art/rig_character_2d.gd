class_name RigCharacter2D
extends Node2D
## The protagonist rig in 2D: one Sprite2D per slot, in draw order, posed by Rig every frame from the parent
## Player2D's state (RigAnimator). Scaled so the setup pose is 1.6 tiles tall, feet on the player's origin, flipped
## to the player's facing; the scarf slots take the active color. THROWAWAY.
const SCARF_SLOTS := ["scarf1", "scarf2", "scarf3"]
const SCARF_COLORS := {"red": Color("#e04a3a"), "green": Color("#3fbf6a"), "": Color(0.55, 0.55, 0.55)}
var rig: Rig
var animator: RigAnimator
var player: Player2D
var _sprites := {}  ## slot name -> Sprite2D
var _texture_scale := {}  ## slot name -> Vector2 from the texture's pixels to the attachment's width and height

## The character for RIG, or null after a push_error when the rig lacks an animation RigAnimator needs, a scarf slot, or
## a loadable part image.
static func create(rig_: Rig) -> RigCharacter2D:
	if not RigAnimator.check(rig_): return null
	var names: Array = rig_.slots.map(func(slot: Rig.Slot) -> String: return slot.name)
	for slot_name: String in SCARF_SLOTS:
		if slot_name not in names: push_error("%s: the rig has no %s slot" % [rig_.source, slot_name]); return null
	var textures := {}
	for slot in rig_.slots:
		textures[slot.name] = load(slot.image)
		if textures[slot.name] is not Texture2D: push_error("%s: slot %s's image %s does not load as a texture" % [rig_.source, slot.name, slot.image]); return null
	return RigCharacter2D.new(rig_, textures)

## Use create(), which checks the rig first.
func _init(rig_: Rig, textures: Dictionary) -> void:
	rig = rig_; name = "Character"
	animator = RigAnimator.new(rig)
	for slot in rig.slots:
		var texture: Texture2D = textures[slot.name]
		var sprite := Sprite2D.new(); sprite.name = slot.name; sprite.texture = texture
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		add_child(sprite)
		_sprites[slot.name] = sprite
		_texture_scale[slot.name] = slot.size / texture.get_size()

func _ready() -> void:
	player = get_parent() as Player2D
	assert(player != null, "RigCharacter2D must be a child of the Player2D")
	Resonance.changed.connect(_color_scarf); _color_scarf()
	_apply()

func _process(delta: float) -> void:
	animator.advance(delta, player.dash_ticks_left > 0, player.is_on_floor(), player.velocity.y < 0.0,
		player.double_jump_used, absf(player.velocity.x) > 1.0)
	_apply()

func _apply() -> void:
	# The rig faces right; facing left mirrors the root with a negative x scale (character-rig.md).
	scale = Vector2(player.facing, 1.0) * (1.6 * Player2D.TILE / rig.height_px)
	var pose := animator.pose()
	for slot_name: String in _sprites:
		var t: Transform2D = pose[slot_name]
		var sprite: Sprite2D = _sprites[slot_name]
		# Skeleton space is y up; the canvas is y down, so y and angles flip.
		sprite.position = Vector2(t.origin.x, rig.feet_y_px - t.origin.y)
		sprite.rotation = -t.get_rotation()
		sprite.scale = t.get_scale() * _texture_scale[slot_name]

func _color_scarf() -> void:
	for slot_name: String in SCARF_SLOTS: (_sprites[slot_name] as Sprite2D).modulate = SCARF_COLORS[Resonance.active]
