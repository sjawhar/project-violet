// THROWAWAY (bake-off lane G-A, glow-up round 1): turns the grid of square stone cells into rock masses.
// Collision stays the grid's; this only changes what is drawn inside each cell.
// - Open sides (next to empty space) are eroded by a few noisy pixels and open top corners are rounded, so edges
//   read as broken rock instead of ruled lines. The walkable top is never eroded except at its rounded corners.
// - The mass darkens smoothly from its lit top down (a field interpolated across cells), so the foreground reads
//   as a dark silhouette under a lit lip; the ground darkens where a block rises out of it (ambient occlusion).
// - A warm rim picks out the sunlit top and, faintly, the open sides.
shader_type canvas_item;
uniform float side = 256.0;        // the sprite's region size in texture pixels (VERTEX spans -side/2..side/2)
uniform vec4 open = vec4(0.0);     // x left, y top, z right, w bottom: 1 where the neighbour cell is empty
uniform vec2 cell = vec2(0.0);     // the cell's grid position, so the noise runs on across cells
uniform vec4 air = vec4(0.0);      // depth under the open air, at the corners: x top-left, y top-right, z bottom-left, w bottom-right
uniform vec2 foot = vec2(0.0);     // x left, y right: 1 on a surface cell at the foot of rock rising beside it
varying vec2 local;                // 0..1 across the cell, y down

void vertex() { local = VERTEX / side + 0.5; }

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}
float fbm(vec2 p) { return 0.6 * noise(p) + 0.3 * noise(p * 2.7) + 0.1 * noise(p * 7.1); }

void fragment() {
	vec4 c = texture(TEXTURE, UV);
	vec2 w = cell + local;
	float aa = 0.012;
	float alpha = 1.0;
	// Side and bottom erosion: 6-26 px of a 64 px cell, a slow wobble plus fine chipping along the edge.
	float cut_l = 0.10 + 0.22 * fbm(vec2(w.y * 1.1, cell.x * 3.1)) + 0.08 * noise(vec2(w.y * 9.0, cell.x));
	float cut_r = 0.10 + 0.22 * fbm(vec2(w.y * 1.1, cell.x * 3.1 + 17.0)) + 0.08 * noise(vec2(w.y * 9.0, cell.x + 5.0));
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
	float shade = mix(1.0, 0.26, smoothstep(0.6, 3.6, below));
	shade *= 0.94 + 0.10 * fbm(w * 0.9);                       // broad, slow value variation, not one flat fill
	float ao = max(foot.x * (1.0 - smoothstep(0.0, 0.85, length(local * vec2(1.0, 1.6)))),
		foot.y * (1.0 - smoothstep(0.0, 0.85, length((local - vec2(1.0, 0.0)) * vec2(1.0, 1.6)))));
	shade *= 1.0 - 0.5 * ao;
	// Warm rim: the sunlit top edge, and a thin glint on open sides.
	float rim_top = open.y * (1.0 - smoothstep(0.0, 0.09, local.y));
	float rim_side = max(open.x * (1.0 - smoothstep(cut_l, cut_l + 0.05, local.x)),
		open.z * (1.0 - smoothstep(cut_r, cut_r + 0.05, 1.0 - local.x))) * (1.0 - smoothstep(0.0, 1.5, below));
	vec3 col = c.rgb * shade + vec3(1.0, 0.70, 0.38) * (0.34 * rim_top + 0.22 * rim_side);
	COLOR = vec4(col, c.a * alpha * COLOR.a);
}
