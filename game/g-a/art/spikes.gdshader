// THROWAWAY (bake-off lane G-A, glow-up round 5): the pit spikes pick up the scene's warm light at their tips and
// sink into the chasm's shadow at their base.
shader_type canvas_item;
uniform vec4 lit : source_color = vec4(1.0, 0.78, 0.52, 1.0);
uniform vec4 shade : source_color = vec4(0.16, 0.10, 0.18, 1.0);
void fragment() {
	vec4 t = texture(TEXTURE, UV);
	float up = 1.0 - UV.y;                                   // 1 at the tips, 0 at the base
	vec3 col = mix(t.rgb * shade.rgb * 2.2, t.rgb * lit.rgb * 1.25, smoothstep(0.15, 0.85, up));
	COLOR = vec4(col, t.a * COLOR.a);
}
