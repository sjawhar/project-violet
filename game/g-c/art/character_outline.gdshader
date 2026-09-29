// THROWAWAY (bake-off lane G-C): how the character reads in the vector world. Drawn by a CanvasGroup around the
// character (art/vector_art.gd): hardens the soft alpha fringe of the painted parts, draws a dark violet outline
// round the whole silhouette (so the scarf holds against a wall of its own colour) and a warm rim where the low sun
// on the left catches the silhouette. The parts themselves are unchanged.
shader_type canvas_item;
render_mode unshaded;
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;
uniform vec4 outline_color : source_color = vec4(0.16, 0.12, 0.24, 1.0);
uniform vec4 rim_color : source_color = vec4(1.0, 0.83, 0.58, 1.0);
uniform float width = 2.0;
float alpha_at(vec2 uv) { return smoothstep(0.3, 0.6, textureLod(screen_texture, uv, 0.0).a); }
void fragment() {
	vec4 c = textureLod(screen_texture, SCREEN_UV, 0.0);
	if (c.a > 0.0001) c.rgb /= c.a;
	float a = smoothstep(0.3, 0.6, c.a);
	vec2 d = SCREEN_PIXEL_SIZE * width;
	float around = 0.0;
	for (int i = 0; i < 8; i++) {
		float ang = float(i) * 0.785398;
		around = max(around, alpha_at(SCREEN_UV + vec2(cos(ang), sin(ang)) * d));
	}
	float outline = clamp(around - a, 0.0, 1.0);
	float rim = a * (1.0 - alpha_at(SCREEN_UV - vec2(d.x * 1.5, 0.0)));
	vec3 rgb = mix(c.rgb, rim_color.rgb, rim * 0.6);
	COLOR = vec4(mix(outline_color.rgb, rgb, a), max(a, outline));
}
