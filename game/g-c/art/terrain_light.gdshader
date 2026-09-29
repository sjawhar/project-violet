// THROWAWAY (bake-off lane G-C): the low sun on the playable rock (art/vector_art.gd sets it on every solid cell with a
// side open to the air). The sun sits low on the left behind the play layer, as in the backdrop: a warm rim along an
// open left face, warm light across an open top edge, and a cool dusk shade on an open right face. It brightens and
// tints the tile's own colours in place; it never lays a translucent layer over the rock.
shader_type canvas_item;
uniform vec4 open_sides = vec4(0.0); // left, right, top, bottom: 1 where the side faces open air
uniform float cell_px = 256.0; // texture pixels per game cell for this tile
const vec3 SUN = vec3(1.0, 0.82, 0.55);
const vec3 DUSK = vec3(0.55, 0.47, 0.72);
void fragment() {
	vec4 c = COLOR; // already the texture times the modulate
	vec2 local = fract(UV * vec2(textureSize(TEXTURE, 0)) / cell_px);
	float rim = open_sides.x * smoothstep(0.22, 0.0, local.x);
	float top = open_sides.z * smoothstep(0.2, 0.0, local.y);
	float shade = open_sides.y * smoothstep(0.62, 1.0, local.x);
	vec3 rgb = c.rgb;
	rgb = mix(rgb, rgb * 1.3 + SUN * 0.16, max(rim, top));
	rgb = mix(rgb, rgb * DUSK, shade * 0.7);
	COLOR = vec4(rgb, c.a);
}
