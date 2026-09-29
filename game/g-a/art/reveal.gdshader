// THROWAWAY (bake-off lane G-A): the reveal for tagged walls and platforms (docs/bakeoff/mechanic.md, Reveal).
// tag-wall and tag-platform are painted neutral light gray. saturation 0: plain gray (#8c8c8c-ish, unacquired color);
// saturation 1: tinted with the cell's color (acquired); glow brightens the lit face and edges (active, pulsed by a
// tween) while the fill keeps its one color, so a red wall is the same red in every state that shows red.
// The piece is lit like the rock around it: the sunlit face (left of a wall, top of a platform) is lighter, the far
// edge is in shadow, and a wall standing on rock darkens where it meets the ground.
shader_type canvas_item;
uniform float saturation = 0.0;
uniform float glow = 0.0;
uniform vec4 tint : source_color = vec4(1.0);
uniform float side = 256.0;        // the sprite's region size in texture pixels (VERTEX spans -side/2..side/2)
uniform bool vertical = true;      // a wall (lit across its width) or a platform (lit from its top)
uniform float base = 0.0;          // 1 when rock lies under this cell (a wall's foot)
varying vec2 local;
void vertex() { local = VERTEX / side + 0.5; }
void fragment() {
	vec4 t = texture(TEXTURE, UV);
	float across = vertical ? local.x : local.y;            // 0 on the lit face, 1 on the shadowed one
	float form = mix(1.12, 0.72, smoothstep(0.0, 1.0, across));
	float lit_edge = 1.0 - smoothstep(0.0, 0.12, across);   // a bright lip on the lit face
	float dark_edge = smoothstep(0.86, 1.0, across);         // and a dark one on the far face
	float foot = base * smoothstep(0.7, 1.0, local.y);       // contact shadow where a wall meets the rock
	float lum = dot(t.rgb, vec3(0.299, 0.587, 0.114));
	vec3 gray = vec3(lum * 0.7);
	vec3 colored = t.rgb * tint.rgb * 1.25;
	vec3 col = mix(gray, colored, saturation) * form * (1.0 - 0.45 * foot) * (1.0 - 0.35 * dark_edge);
	col += (0.18 + glow) * lit_edge * mix(vec3(1.0, 0.85, 0.7), tint.rgb + 0.35, saturation);
	col += glow * 0.35 * tint.rgb * (1.0 - foot);
	COLOR = vec4(col, t.a * COLOR.a);
}
