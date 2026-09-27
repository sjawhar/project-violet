class_name RigCharacter3D
extends Node3D
## The protagonist rig in 3D: one Sprite3D per slot in the player's XY plane, in draw order, posed by Rig every frame
## from the parent Player3D's state (RigAnimator). Skeleton space is y up like the world, so nothing flips but the
## facing; pixel_size makes the setup pose 1.6 m tall, feet on the player's origin. Sprites are shaded, so the sun and
## the crystal lights reach the character; the scarf slots take the active color. THROWAWAY.
const SCARF_SLOTS := ["scarf1", "scarf2", "scarf3"]
const SCARF_COLORS := {"red": Color("#e04a3a"), "green": Color("#3fbf6a"), "": Color(0.55, 0.55, 0.55)}
## Metres between successive slots along z, toward the camera, so the draw order also holds in depth; render_priority
## orders the transparent sprites first.
const LAYER_GAP := 0.002
var rig: Rig
var animator: RigAnimator
var player: Player3D
var _sprites := {}  ## slot name -> Sprite3D
var _texture_scale := {}  ## slot name -> Vector2 from the texture's pixels to the attachment's width and height
var _pixel_size: float

func _init(rig_: Rig) -> void:
	rig = rig_; name = "Character"
	animator = RigAnimator.new(rig)
	_pixel_size = 1.6 / rig.height_px
	for i in rig.slots.size():
		var slot := rig.slots[i]
		var texture: Texture2D = load(slot.image)
		assert(texture != null, "rig slot %s: cannot load %s" % [slot.name, slot.image])
		var sprite := Sprite3D.new(); sprite.name = slot.name; sprite.texture = texture
		sprite.pixel_size = _pixel_size; sprite.shaded = true; sprite.render_priority = i
		sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		sprite.position.z = i * LAYER_GAP
		add_child(sprite)
		_sprites[slot.name] = sprite
		_texture_scale[slot.name] = slot.size / texture.get_size()
	for slot_name: String in SCARF_SLOTS: assert(_sprites.has(slot_name), "the rig has no %s slot" % slot_name)

func _ready() -> void:
	player = get_parent() as Player3D
	assert(player != null, "RigCharacter3D must be a child of the Player3D")
	Resonance.changed.connect(_color_scarf); _color_scarf()
	_apply()

func _process(delta: float) -> void:
	animator.advance(delta, player.dash_ticks_left > 0, player.is_on_floor(), player.velocity.y > 0.0,
		player.double_jump_used, absf(player.velocity.x) > 1.0 / 64.0)  # Player2D's 1 px/s, in metres
	_apply()

func _apply() -> void:
	# Facing mirrors each sprite about the player's vertical axis (x and angle negated, image flipped) rather than
	# scaling the node by -1 in x, which would turn the shaded sprites' normals away from the lights.
	var mirror := player.facing * (1 if rig.facing == "right" else -1)
	var pose := animator.pose()
	for slot_name: String in _sprites:
		var t: Transform2D = pose[slot_name]
		var sprite: Sprite3D = _sprites[slot_name]
		sprite.position.x = mirror * t.origin.x * _pixel_size
		sprite.position.y = (t.origin.y - rig.feet_y_px) * _pixel_size
		sprite.rotation.z = mirror * t.get_rotation()
		sprite.flip_h = mirror < 0
		var s: Vector2 = t.get_scale() * _texture_scale[slot_name]
		sprite.scale = Vector3(s.x, s.y, 1.0)

func _color_scarf() -> void:
	for slot_name: String in SCARF_SLOTS: (_sprites[slot_name] as Sprite3D).modulate = SCARF_COLORS[Resonance.active]
