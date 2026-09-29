// THROWAWAY (bake-off lane G-C): an edge light for the dark foreground silhouettes (art/vector_art.gd): where a shape's
// edge faces the low sun on the left or the sky above, a band of warm dusk light, so the near plane is lit like the rest
// of the scene instead of being a flat cut-out.
shader_type canvas_item;
uniform vec4 rim_color : source_color = vec4(0.62, 0.42, 0.44, 1.0);
uniform float width_px = 5.0;
void fragment() {
	vec4 c = COLOR; // already the texture times the modulate
	vec2 px = TEXTURE_PIXEL_SIZE * width_px;
	float open_left = 1.0 - texture(TEXTURE, UV - vec2(px.x, 0.0)).a;
	float open_top = 1.0 - texture(TEXTURE, UV - vec2(0.0, px.y)).a;
	float rim = clamp(max(open_left, open_top * 0.7), 0.0, 1.0);
	COLOR = vec4(mix(c.rgb, rim_color.rgb, rim * 0.85), c.a);
}
