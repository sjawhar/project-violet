class_name GreyboxArt
extends Resource
## Greybox visuals: flat squares per kind, a sand backdrop, and the painted protagonist once her sprites are in the
## project (else a STAND-IN capsule for the character).
## Lanes subclass it (PaintedArt in G-A, the flat-vector kit in G-C). THROWAWAY.
## Colors match tools/greybox (Task 1).
const COLORS := {
	"empty": Color8(245, 240, 230), "solid": Color8(90, 80, 70), "wall_red": Color8(200, 60, 50), "wall_green": Color8(60, 170, 90),
	"platform_red": Color8(230, 120, 110), "platform_green": Color8(120, 210, 150), "start": Color8(40, 120, 220), "goal": Color8(240, 200, 40),
	"orb_red": Color8(255, 30, 30), "orb_green": Color8(30, 220, 80), "hazard": Color8(20, 20, 20),
}
const SAND := Color("#d9b27c")
const GRAY := Color(0.55, 0.55, 0.55)

## A tagged cell's square: gray until its color is acquired, its color once acquired, brighter while active.
class TaggedSquare extends Polygon2D:
	var base: Color
	func set_resonance_look(revealed: bool, active: bool) -> void:
		color = base.lightened(0.35) if active else base if revealed else GRAY

func make_cell(kind: String, _cell: Vector2i, ts: float) -> Node2D:
	var square: Polygon2D
	if Greybox.TAGGED.has(kind):
		var tagged := TaggedSquare.new(); tagged.base = COLORS[kind]; tagged.color = GRAY
		square = tagged
	else:
		square = Polygon2D.new(); square.color = COLORS[kind]
	var h := ts / 2.0
	square.polygon = PackedVector2Array([Vector2(-h, -h), Vector2(h, -h), Vector2(h, h), Vector2(-h, h)])
	return square

func make_backdrop(level: Greybox) -> Node2D:
	var holder := Node2D.new(); holder.name = "Backdrop"; holder.z_index = -10
	var rect := ColorRect.new(); rect.color = SAND
	rect.size = Vector2(level.width * level.tile_px, level.height * level.tile_px)
	holder.add_child(rect)
	return holder

## The file whose presence swaps the STAND-IN for the painted protagonist: the violet-sprites v1 set from
## assets/bakeoff/protagonist/ copied to res://protagonist/, with its frames where its relative image paths point.
const SPRITES_PATH := "res://protagonist/sprites/violet.sprites.json"

## A sprite set that is there but does not load stops the game (exit 1) rather than falling back to the STAND-IN.
func attach_character(player: Node) -> void:
	if FileAccess.file_exists(SPRITES_PATH):
		var sprites := Sprites.load_file(SPRITES_PATH)
		var character := SpriteCharacter2D.create(sprites) if sprites != null else null
		if character == null:
			push_error("%s: the character sprites did not load (see the error above); quitting" % SPRITES_PATH)
			player.get_tree().quit(1)
			return
		player.add_child(character)
		return
	var tile := 64.0
	var w := 0.8 * tile; var h := 1.6 * tile; var r := w / 2.0
	var points := PackedVector2Array()
	for i in 13:  # top cap, then bottom cap: a capsule with its feet at the origin
		var a := PI + PI * i / 12.0
		points.append(Vector2(cos(a) * r, -h + r + sin(a) * r))
	for i in 13:
		var a := PI * i / 12.0
		points.append(Vector2(cos(a) * r, -r + sin(a) * r))
	var capsule := Polygon2D.new(); capsule.name = "StandIn"; capsule.polygon = points; capsule.color = Color("#7a4fb8")
	player.add_child(capsule)
	var label := Label.new(); label.name = "StandInLabel"; label.text = "STAND-IN"
	label.position = Vector2(-48, -h - 30); label.add_theme_color_override("font_color", Color.BLACK)
	player.add_child(label)
