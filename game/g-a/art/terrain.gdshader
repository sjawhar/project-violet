// THROWAWAY (bake-off lane G-A, glow-up round 1): turns the grid of square stone cells into rock masses.
// Collision stays the grid's; this only changes what is drawn inside each cell.
// - Open sides (next to empty space) are eroded by a few noisy pixels and open top corners are rounded, so edges
//   read as broken rock instead of ruled lines. The walkable top is never eroded except at its rounded corners.
// - The mass darkens smoothly from its lit top down (a field interpolated across cells), so the foreground reads
//   as a dark silhouette under a lit lip; the ground darkens where a block rises out of it (ambient occlusion).
// - A warm rim picks out the sunlit top and, faintly, the open sides.
// - Form (glow-up round 8): the sunset is to the left, so a mass's left face takes a warm lit band and its right face
//   falls into a cool shadow over about a cell; the rock just under a sand crust is in the crust's shadow; and a mass
//   that rises above the ground darkens toward its base at the ground line and just below it, so it stands on the ground.
// - The rock is one wide cliff-face painting laid over the whole level in level space (glow-up round 7), so a mass
//   shows one continuous stretch of strata instead of a tile per cell; it repeats only every 30-odd cells. A surface
//   cell gets a sand crust of wandering thickness over it.
shader_type canvas_item;
uniform float side = 64.0;         // the cell quad's size in pixels (VERTEX spans -side/2..side/2)
uniform vec4 open = vec4(0.0);     // x left, y top, z right, w bottom: 1 where the neighbour cell is empty
uniform vec2 cell = vec2(0.0);     // the cell's grid position, so the noise runs on across cells
uniform vec4 air = vec4(0.0);      // depth under the open air, at the corners: x top-left, y top-right, z bottom-left, w bottom-right
uniform vec2 foot = vec2(0.0);     // x left, y right: 1 on a surface cell at the foot of rock (or a tagged wall) rising beside it
uniform vec2 run = vec2(3.0);      // x left, y right: cells of rock between this cell and the open air on that side (capped at 3)
uniform float ground_y = 0.0;      // the ground line's row: where the ground's walkable top is
uniform float raised = 0.0;        // 1 on a cell of a mass that rises above the ground line, down to the line
varying vec2 local;                // 0..1 across the cell, y down

void vertex() { local = VERTEX / side + 0.5; }

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}
float fbm(vec2 p) { return 0.6 * noise(p) + 0.3 * noise(p * 2.7) + 0.1 * noise(p * 7.1); }

uniform sampler2D rock_face : source_color, repeat_enable, filter_linear_mipmap;  // the rock-face painting
const float ROCK_SCALE = 1.5;      // screen pixels per painting pixel
const float TS = 64.0;             // screen pixels per cell
const vec3 SAND = vec3(0.82, 0.58, 0.33);
const vec3 GRASS = vec3(0.50, 0.38, 0.22);  // dry grass, rock-and-ochre toned (no green outside tagged cells)

void fragment() {
	vec2 w = cell + local;
	vec3 rock = texture(rock_face, w * TS / (vec2(textureSize(rock_face, 0)) * ROCK_SCALE)).rgb;
	// A surface cell's sand crust: its top wanders up to a fifth of a cell above the cell (the quad extends that
	// far), in low drifts and small lumps, so the walkable top is not a ruled line; its bottom wanders too, with a
	// darker damp edge where it meets the rock.
	float crust_top = -(0.02 + 0.12 * fbm(vec2(w.x * 2.4, cell.y + 3.0)) + 0.12 * smoothstep(0.45, 0.85, noise(vec2(w.x * 0.9, 8.0))));
	float crust = 0.12 + 0.16 * fbm(vec2(w.x * 1.1, cell.y));
	float in_crust = open.y * (1.0 - smoothstep(crust - 0.02, crust, local.y));
	float crust_edge = open.y * (1.0 - smoothstep(0.0, 0.05, abs(local.y - crust)));
	vec3 sand = mix(rock * 1.05, SAND, 0.7) * mix(1.08, 0.86, clamp((local.y - crust_top) / (crust - crust_top), 0.0, 1.0));
	rock = mix(rock, sand, in_crust);  // painted grain from the rock beneath, lit at the top
	rock *= 1.0 - 0.3 * crust_edge;
	float aa = 0.012;
	float alpha = smoothstep(crust_top - aa, crust_top, local.y);  // above the cell only the crust's drifts show
	// Dry grass in clumps along a surface cell's top: thin slanted blades, about 2 px wide, rising from the crust.
	float clump = open.y * smoothstep(0.45, 0.75, noise(vec2(w.x * 1.1, cell.y * 5.0 + 21.0)));
	float rise = crust_top - local.y;                             // height above the crust's top, in cells
	float u = w.x * 20.0 + rise * 12.0 * (hash(vec2(floor(w.x * 3.0), 4.0)) - 0.5);
	float blade_h = clump * (0.08 + 0.30 * hash(vec2(floor(u), 13.0)));
	float blade = step(fract(u), 0.6) * step(0.0, rise) * (1.0 - smoothstep(blade_h - 0.01, blade_h, rise)) * step(0.3, hash(vec2(floor(u), 17.0)));
	alpha = max(alpha, blade);
	rock = mix(rock, GRASS * (0.8 + 0.5 * clamp(rise / 0.2, 0.0, 1.0)), blade);  // blades lighter toward their tips
	vec4 c = vec4(rock, 1.0);
	// Side and bottom erosion: 4-35 px of a 64 px cell, a slow wobble plus fine chipping along the edge; on the sides the
	// painting's dark (recessed) strata are cut deeper than its lit ones, so the silhouette steps out at each ledge.
	float ledge = 0.45 * (0.55 - dot(texture(rock_face, w * TS / (vec2(textureSize(rock_face, 0)) * ROCK_SCALE)).rgb, vec3(0.299, 0.587, 0.114)));
	float cut_l = max(0.06, 0.12 + 0.20 * fbm(vec2(w.y * 1.1, cell.x * 3.1)) + 0.08 * noise(vec2(w.y * 9.0, cell.x)) + ledge);
	float cut_r = max(0.06, 0.12 + 0.20 * fbm(vec2(w.y * 1.1, cell.x * 3.1 + 17.0)) + 0.08 * noise(vec2(w.y * 9.0, cell.x + 5.0)) + ledge);
	float cut_b = 0.06 + 0.08 * fbm(vec2(w.x * 5.0, cell.y * 2.3 + 41.0));
	alpha *= mix(1.0, smoothstep(cut_l, cut_l + aa, local.x), open.x);
	alpha *= mix(1.0, smoothstep(cut_r, cut_r + aa, 1.0 - local.x), open.z);
	alpha *= mix(1.0, smoothstep(cut_b, cut_b + aa, 1.0 - local.y), open.w);
	// Rounded top corners where the top and a side are both open.
	float r = 0.55 + 0.15 * fbm(w * 3.0);
	float d_tl = length(max(vec2(r) - local, 0.0));
	float d_tr = length(max(vec2(r) - vec2(1.0 - local.x, local.y), 0.0));
	alpha *= mix(1.0, 1.0 - smoothstep(r - aa, r, d_tl), open.x * open.y);
	alpha *= mix(1.0, 1.0 - smoothstep(r - aa, r, d_tr), open.z * open.y);
	// Dark foreground mass: full value at the open surface, falling off over about two cells into the rock.
	float below = mix(mix(air.x, air.y, local.x), mix(air.z, air.w, local.x), local.y);
	float shade = mix(1.0, 0.36, smoothstep(0.2, 3.4, below));
	shade *= 0.94 + 0.10 * fbm(w * 0.9);                       // broad, slow value variation, not one flat fill
	float ao = max(foot.x * (1.0 - smoothstep(0.0, 0.85, length(local * vec2(1.0, 1.6)))),
		foot.y * (1.0 - smoothstep(0.0, 0.85, length((local - vec2(1.0, 0.0)) * vec2(1.0, 1.6)))));
	shade *= 1.0 - 0.5 * ao;
	float d_left = run.x + local.x, d_right = run.y + (1.0 - local.x);   // distance to the open face on each side, in cells
	float shadow_side = 1.0 - smoothstep(0.0, 1.8, d_right);
	float lit_side = 1.0 - smoothstep(0.0, 0.8, d_left);
	shade *= 1.0 - 0.5 * shadow_side;
	shade *= 1.0 - 0.38 * open.y * smoothstep(crust, crust + 0.03, local.y) * (1.0 - smoothstep(crust, crust + 0.3, local.y));
	float base = raised * (w.y < ground_y ? 1.0 - smoothstep(0.0, 1.1, ground_y - w.y) : 1.0 - smoothstep(0.0, 0.35, w.y - ground_y));
	shade *= 1.0 - 0.55 * base;
	// Warm rim: the sunlit top edge, and a thin glint on open sides.
	float rim_top = open.y * (1.0 - smoothstep(0.0, 0.09, local.y - crust_top));
	float rim_side = max(open.x * (1.0 - smoothstep(cut_l, cut_l + 0.05, local.x)),
		open.z * (1.0 - smoothstep(cut_r, cut_r + 0.05, 1.0 - local.x))) * (1.0 - smoothstep(0.0, 1.5, below));
	vec3 col = c.rgb * shade * mix(vec3(1.0), vec3(0.82, 0.80, 1.0), shadow_side) + vec3(1.0, 0.70, 0.38) * (0.22 * rim_top + 0.22 * rim_side + 0.20 * lit_side * (1.0 - smoothstep(0.0, 2.5, below)));
	COLOR = vec4(col, c.a * alpha * COLOR.a);
}
