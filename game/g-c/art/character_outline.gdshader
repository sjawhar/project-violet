// THROWAWAY (bake-off lane G-C): how the character reads in the vector world. Drawn by a CanvasGroup around the
// character (art/vector_art.gd): hardens the soft alpha fringe of the painted parts, draws a dark violet outline
// round the whole silhouette and a thin light halo outside it, so the scarf holds against a wall of its own colour
// (the halo) and against the pale sand and sky (the dark line), and a warm rim where the low sun on the left
// catches the silhouette. The parts themselves are unchanged.
shader_type canvas_item;
render_mode unshaded;
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_linear;
uniform vec4 outline_color : source_color = vec4(0.16, 0.12, 0.24, 1.0);
uniform vec4 halo_color : source_color = vec4(1.0, 0.94, 0.84, 0.85);
uniform vec4 rim_color : source_color = vec4(1.0, 0.83, 0.58, 1.0);
uniform float width = 1.6;
float alpha_at(vec2 uv) { return smoothstep(0.3, 0.6, textureLod(screen_texture, uv, 0.0).a); }
float ring(vec2 uv, vec2 d) {
	float m = 0.0;
	for (int i = 0; i < 12; i++) {
		float ang = float(i) * 0.5236;
		m = max(m, alpha_at(uv + vec2(cos(ang), sin(ang)) * d));
	}
	return m;
}
void fragment() {
	vec4 c = textureLod(screen_texture, SCREEN_UV, 0.0);
	if (c.a > 0.0001) c.rgb /= c.a;
	float a = smoothstep(0.3, 0.6, c.a);
	vec2 d = SCREEN_PIXEL_SIZE * width;
	float near = ring(SCREEN_UV, d);
	float far = ring(SCREEN_UV, d * 2.2);
	float outline = clamp(near - a, 0.0, 1.0);
	float halo = clamp(far - max(near, a), 0.0, 1.0);
	float rim = a * (1.0 - alpha_at(SCREEN_UV - vec2(d.x * 2.6, 0.0)));
	vec3 rgb = mix(c.rgb, rim_color.rgb, rim * 0.8);
	vec3 col = mix(outline_color.rgb, rgb, a);
	col = mix(col, halo_color.rgb, halo);
	COLOR = vec4(col, max(max(a, outline), halo * halo_color.a));
}
