// THROWAWAY (bake-off lane G-A, glow-up round 3): how Violet reads in the painted world, applied to her whole drawn
// silhouette (a CanvasGroup around the rig, so part seams inside her are not outlined). Her parts are unchanged:
// - a thin dark shadow-violet outline, so she stands off the sky, the sand and walls of her scarf's color;
// - her body values pulled down a little, so she sits darker than the peach sky;
// - a warm rim on the edges facing the low sunset key light.
shader_type canvas_item;
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_linear;
uniform vec2 light_dir = vec2(-0.55, -0.83);         // towards the key light, in screen space (y down)
uniform vec4 outline_color : source_color = vec4(0.12, 0.07, 0.16, 0.9);
uniform vec4 rim_color : source_color = vec4(1.0, 0.76, 0.42, 1.0);
uniform float outline_px = 2.0;
uniform float rim_px = 4.0;
uniform float body_value = 0.82;

void fragment() {
	vec4 c = textureLod(screen_texture, SCREEN_UV, 0.0);
	float a = c.a;
	vec3 col = a > 0.0001 ? c.rgb / a : vec3(0.0);   // the group's buffer is premultiplied
	float around = 0.0;
	for (int i = 0; i < 8; i++) {
		float ang = float(i) * 0.785398;
		around = max(around, textureLod(screen_texture, SCREEN_UV + vec2(cos(ang), sin(ang)) * outline_px * SCREEN_PIXEL_SIZE, 0.0).a);
	}
	float toward = textureLod(screen_texture, SCREEN_UV + normalize(light_dir) * rim_px * SCREEN_PIXEL_SIZE, 0.0).a;
	float rim = a * (1.0 - toward);
	col = col * body_value;
	col = mix(col, rim_color.rgb, clamp(rim, 0.0, 1.0) * 0.9);
	float halo = clamp(around - a, 0.0, 1.0) * outline_color.a;
	float out_a = a + halo * (1.0 - a);
	vec3 out_rgb = out_a > 0.0001 ? (col * a + outline_color.rgb * halo * (1.0 - a)) / out_a : vec3(0.0);
	COLOR = vec4(out_rgb, out_a);
}
