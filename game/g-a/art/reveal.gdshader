// THROWAWAY (bake-off lane G-A): the reveal for tagged walls and platforms (docs/bakeoff/mechanic.md, Reveal).
// saturation 0: plain gray (#8c8c8c-ish, unacquired color); saturation 1: tinted with the cell's color (acquired); glow
// brightens the lit face and edges (active, pulsed by a tween) while the fill keeps its one color, so a red wall is the
// same red in every state that shows red.
// The piece is carved from the same rock as the terrain (glow-up round 9): its grain is the rock-face painting's value,
// laid in level space (turned upright on a wall, so a column reads as one carved monolith rather than stacked planks).
// It is lit like the rock around it: a bright lip on the sunlit face (left of a wall, top of a platform), a darker
// core falling into shadow on the far face, and a contact shadow where a wall meets the ground. Its open edges are worn
// by a few noisy pixels, and an open end (the top of a column, the ends of a slab) is broken off in a rough shape
// instead of running on to the frame edge. Collision is the grid's; this only changes what is drawn inside the cell.
shader_type canvas_item;
uniform float saturation = 0.0;
uniform float glow = 0.0;
uniform vec4 tint : source_color = vec4(1.0);
uniform float side = 256.0;        // the sprite's region size in texture pixels (VERTEX spans -side/2..side/2)
uniform bool vertical = true;      // a wall (lit across its width) or a platform (lit from its top)
uniform float base = 0.0;          // 1 when rock lies under this cell (a wall's foot)
uniform vec2 cell = vec2(0.0);     // the cell's grid position, so the grain and wear run on across cells
uniform vec4 ends = vec4(0.0);     // x left, y top, z right, w bottom: 1 where the neighbour is not part of this piece
uniform sampler2D rock_face : source_color, repeat_enable, filter_linear_mipmap;
const float ROCK_SCALE = 1.5;      // screen pixels per painting pixel, as in terrain.gdshader
const float TS = 64.0;
varying vec2 local;
void vertex() { local = VERTEX / side + 0.5; }

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}
float fbm(vec2 p) { return 0.6 * noise(p) + 0.3 * noise(p * 2.7) + 0.1 * noise(p * 7.1); }

void fragment() {
	vec2 w = cell + local;
	vec2 g_uv = (vertical ? w.yx + vec2(7.3, 0.0) : w) * TS / (vec2(textureSize(rock_face, 0)) * ROCK_SCALE);
	float lum = dot(texture(rock_face, g_uv).rgb, vec3(0.299, 0.587, 0.114));
	float stone = clamp(0.80 + 1.4 * (lum - 0.55), 0.36, 1.05);   // the painting's value, lifted to the pale stone's range
	vec2 along = vertical ? vec2(w.x * 9.0, w.y * 1.3) : vec2(w.x * 1.3, w.y * 9.0);
	stone *= 0.82 + 0.30 * fbm(along) ;                      // loose brush strokes running along the piece
	stone *= 0.90 + 0.16 * fbm(w * 2.2 + 40.0);              // and broad value breaks, so no two cells match
	float across = vertical ? local.x : local.y;            // 0 on the lit face, 1 on the shadowed one
	float form = mix(1.02, 0.60, smoothstep(0.08, 0.95, across));  // a darker core falling into the far face
	float lit_edge = 1.0 - smoothstep(0.0, 0.14, across);   // a bright lip on the lit face
	float dark_edge = smoothstep(0.84, 1.0, across);         // and a dark one on the far face
	float foot = base * smoothstep(0.55, 1.0, local.y);      // contact shadow where a wall meets the rock
	// Worn edges: 2-9 px chipped off each open side, varying along it.
	float aa = 0.015;
	float wear_l = 0.03 + 0.08 * fbm(vec2(w.y * 3.0, cell.x * 5.1)) + 0.03 * noise(vec2(w.y * 15.0, cell.x));
	float wear_r = 0.03 + 0.08 * fbm(vec2(w.y * 3.0, cell.x * 5.1 + 9.0)) + 0.03 * noise(vec2(w.y * 15.0, cell.x + 3.0));
	float wear_t = 0.03 + 0.08 * fbm(vec2(w.x * 3.0, cell.y * 5.1 + 21.0)) + 0.03 * noise(vec2(w.x * 15.0, cell.y));
	float wear_b = 0.03 + 0.08 * fbm(vec2(w.x * 3.0, cell.y * 5.1 + 33.0)) + 0.03 * noise(vec2(w.x * 15.0, cell.y + 7.0));
	float alpha = 1.0;
	if (vertical) {  // a column's sides are always worn; its broken top is cut much deeper
		alpha *= smoothstep(wear_l, wear_l + aa, local.x) * smoothstep(wear_r, wear_r + aa, 1.0 - local.x);
		float brk = 0.18 + 0.30 * fbm(vec2(w.x * 4.0, cell.y + 5.0)) + 0.12 * abs(local.x - 0.45);
		alpha *= mix(1.0, smoothstep(brk, brk + aa, local.y), ends.y);
	} else {         // a slab's top and bottom are worn; its free ends are broken off
		alpha *= smoothstep(wear_t, wear_t + aa, local.y) * smoothstep(wear_b, wear_b + aa, 1.0 - local.y);
		float brk_l = 0.08 + 0.22 * fbm(vec2(w.y * 4.0, cell.x + 5.0));
		float brk_r = 0.08 + 0.22 * fbm(vec2(w.y * 4.0, cell.x + 11.0));
		alpha *= mix(1.0, smoothstep(brk_l, brk_l + aa, local.x), ends.x) * mix(1.0, smoothstep(brk_r, brk_r + aa, 1.0 - local.x), ends.z);
	}
	vec3 gray = vec3(stone * 0.7);
	vec3 colored = vec3(stone) * tint.rgb * 1.25;
	vec3 col = mix(gray, colored, saturation) * form * (1.0 - 0.5 * foot) * (1.0 - 0.35 * dark_edge);
	col += (0.18 + glow) * lit_edge * mix(vec3(1.0, 0.85, 0.7), tint.rgb + 0.35, saturation);
	col += glow * 0.30 * tint.rgb * (1.0 - foot) * (1.0 - 0.5 * across);
	COLOR = vec4(col, texture(TEXTURE, UV).a * alpha * COLOR.a);
}
