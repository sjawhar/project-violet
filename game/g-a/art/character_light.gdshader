// THROWAWAY (bake-off lane G-A, glow-up round 10): how Violet reads in the painted world, applied to her whole drawn
// silhouette (a CanvasGroup around the rig, so the seams between her parts get no edge treatment). Her parts, rig and
// scale are unchanged. No outline:
// - her body is graded darker and cooler, so she reads as a dark shape against the peach sky and the pale sand;
//   saturated pixels (the scarf in its active color) keep their color;
// - a warm rim, graded over a few pixels, on the edges facing the low sunset to the left.
shader_type canvas_item;
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_linear;
uniform vec2 light_dir = vec2(-0.8, -0.6);           // towards the sunset, in screen space (y down)
uniform vec3 body_tint = vec3(0.50, 0.50, 0.66);     // darker and cooler
uniform vec4 rim_color : source_color = vec4(1.0, 0.62, 0.30, 1.0);
uniform float rim_px = 8.0;

void fragment() {
	vec4 c = textureLod(screen_texture, SCREEN_UV, 0.0);
	float a = c.a;
	vec3 col = a > 0.0001 ? c.rgb / a : vec3(0.0);   // the group's buffer is premultiplied
	float hi = max(col.r, max(col.g, col.b)), lo = min(col.r, min(col.g, col.b));
	float keep = smoothstep(0.18, 0.40, hi > 0.0001 ? (hi - lo) / hi : 0.0);
	col = mix(col * body_tint, col, keep);
	// How much of her lies between this pixel and the sun, over rim_px: none at a sun-facing edge, all well inside.
	float toward = 0.0;
	for (int k = 1; k <= 3; k++)
		toward += textureLod(screen_texture, SCREEN_UV + normalize(light_dir) * rim_px * float(k) / 3.0 * SCREEN_PIXEL_SIZE, 0.0).a;
	float rim = clamp(1.0 - toward / 3.0, 0.0, 1.0);
	col += rim_color.rgb * rim * 1.1;
	COLOR = vec4(col, a);
}
