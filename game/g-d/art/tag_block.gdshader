// THROWAWAY (bake-off lane G-D): the tag-block's surface. Stone grain and a light-from-above gradient on the brief's tag
// color (gray until acquired), and a carved glyph on the front face, a filled diamond for red and a ring for green, so
// the two colors differ by shape as well as hue. Active blocks glow, most strongly in the glyph. Emission is always on,
// so toggling a block never compiles a shader variant.
shader_type spatial;
render_mode diffuse_toon, specular_toon;

uniform vec3 base_color : source_color = vec3(0.878, 0.29, 0.227);
uniform vec3 gray : source_color = vec3(0.6);
uniform float glyph_kind = 0.0; // 0: filled diamond (red), 1: ring (green)
uniform float revealed = 0.0;
uniform float glow = 0.0;

varying vec3 local_pos;
varying vec3 local_normal;

void vertex() {
	local_pos = VERTEX;
	local_normal = NORMAL;
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

void fragment() {
	vec3 color = mix(gray, base_color, revealed);
	vec3 an = abs(local_normal);
	vec2 face = an.z > 0.5 ? local_pos.xy : (an.x > 0.5 ? local_pos.zy : local_pos.xz);
	float grain = noise(face * 9.0) * 0.6 + noise(face * 27.0) * 0.4;
	color *= 1.0 + 0.24 * (grain - 0.5);
	color *= 0.88 + 0.24 * clamp(local_pos.y, 0.0, 1.0);
	float g = 0.0;
	if (local_normal.z > 0.5) {
		vec2 c = local_pos.xy - vec2(0.0, 0.5);
		if (glyph_kind < 0.5) {
			float d = abs(c.x) + abs(c.y);
			g = 1.0 - smoothstep(0.22, 0.24, d);
		} else {
			float d = length(c);
			g = (1.0 - smoothstep(0.25, 0.27, d)) * smoothstep(0.14, 0.16, d);
		}
	}
	ALBEDO = mix(color, color * 0.5, g);
	EMISSION = base_color * revealed * glow * (0.25 + 8.0 * g);
}
