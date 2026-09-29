// THROWAWAY (bake-off lane G-D): the tag-block's surface, glyph-stone in the brief's tag color (gray until acquired).
// Each block is a dressed stone: grain, faces lit from above, edges worn darker. A glowing inlay runs up the middle of
// every front face and joins the blocks above and below (beside, on a platform) into one carved channel, with a node on each block, a diamond
// for red and a ring for green (the shapes are the colour-blind cue), sized a little differently on each block. The
// inlay glows softly once the color is acquired and brightly while it is active. Emission is always on, so toggling a
// block never compiles a shader variant.
shader_type spatial;
render_mode diffuse_toon, specular_toon;

uniform vec3 base_color : source_color = vec3(0.878, 0.29, 0.227);
uniform vec3 gray : source_color = vec3(0.6);
uniform float glyph_kind = 0.0; // 0: diamond (red), 1: ring (green)
uniform float horizontal = 0.0; // 1 for platforms: the channel runs across, joining the blocks beside
uniform float revealed = 0.0;
uniform float glow = 0.0;

varying vec3 local_pos;
varying vec3 local_normal;
varying vec3 block_origin;

void vertex() {
	local_pos = VERTEX;
	local_normal = NORMAL;
	block_origin = NODE_POSITION_WORLD;
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
	// Face coordinates, 0-1 across the face.
	vec2 face = an.z > 0.5 ? vec2(local_pos.x + 0.5, local_pos.y) : (an.x > 0.5 ? vec2(local_pos.z + 0.5, local_pos.y) : local_pos.xz + 0.5);
	float grain = noise(face * 7.0 + block_origin.xy * 3.1) * 0.55 + noise(face * 23.0) * 0.45;
	color *= 1.0 + 0.3 * (grain - 0.5);
	color *= 0.86 + 0.28 * clamp(local_pos.y, 0.0, 1.0);
	float edge = min(min(face.x, 1.0 - face.x), min(face.y, 1.0 - face.y));
	color *= 0.72 + 0.28 * smoothstep(0.0, 0.14, edge);
	float inlay = 0.0;
	if (local_normal.z > 0.5) {
		vec2 c = local_pos.xy - vec2(0.0, 0.5);
		float size = 0.17 + 0.07 * hash(block_origin.xy);
		float node;
		if (glyph_kind < 0.5) {
			node = 1.0 - smoothstep(size, size + 0.02, abs(c.x) + abs(c.y));
		} else {
			float d = length(c);
			node = (1.0 - smoothstep(size, size + 0.02, d)) * smoothstep(size - 0.09, size - 0.07, d);
		}
		float channel = 1.0 - smoothstep(0.022, 0.034, abs(horizontal > 0.5 ? c.y : c.x));
		inlay = max(node, channel);
	}
	vec3 carved = color * 0.45;
	ALBEDO = mix(color, carved, inlay);
	EMISSION = base_color * revealed * (inlay * (0.9 + 5.0 * glow) + 0.15 * glow);
}
