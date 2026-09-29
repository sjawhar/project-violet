// THROWAWAY (bake-off lane G-C): tag reveal for tagged cells (docs/bakeoff/mechanic.md, Reveal).
// The tag-wall and tag-platform textures are untinted pale gray; their grey value is the shading. saturation 0: plain
// gray (unacquired); saturation 1: the cell's colour (acquired); glow brightens it (active, pulsed by a tween). The
// colour is locked: the texture's base grey maps to exactly the tag colour, brightening scales value instead of adding
// the tint, and it is pre-saturated against the world saturation post effect. On top, the scene's low sun from the
// left: each wall or platform is lit as one object (brighter toward its sunlit top, a warm rim on its open left side,
// a cool shaded right side, a bright top edge, a darker foot), using its run and open sides that art/vector_art.gd
// passes per cell. The colour cue that does not rely on hue is a glyph carved into the surface on every other cell:
// a chevron on red, a double wave on green, visible in grey too.
shader_type canvas_item;
global uniform float world_saturation;
uniform float saturation = 0.0;
uniform float glow = 0.0;
uniform vec4 tint : source_color = vec4(1.0);
uniform int pattern = 0; // 1 chevron (red), 2 waves (green)
uniform vec4 open_sides = vec4(0.0); // left, right, top, bottom: 1 where the side faces open air
uniform vec2 run_v = vec2(0.0, 1.0); // this cell's index in its vertical run, and the run's length
uniform vec2 run_h = vec2(0.0, 1.0); // the same horizontally
const float BASE_GREY = 0.84; // tag-wall.svg's base fill #d6d6d6
const float CELL_PX = 256.0; // texture pixels per game cell
const vec3 LUMA = vec3(0.299, 0.587, 0.114);
const vec3 SUN = vec3(1.0, 0.86, 0.62);
const vec3 DUSK = vec3(0.36, 0.3, 0.52);
float carve(vec2 p, int kind) {
	float d = 1.0;
	if (kind == 1) d = abs(p.y - (0.64 - abs(p.x - 0.5) * 0.7));
	if (kind == 2) d = min(abs(p.y - (0.42 + 0.07 * sin(p.x * 6.2832))), abs(p.y - (0.62 + 0.07 * sin(p.x * 6.2832))));
	float inside = step(0.16, p.x) * step(p.x, 0.84);
	return smoothstep(0.034, 0.018, d) * inside;
}
void fragment() {
	vec4 t = texture(TEXTURE, UV);
	vec2 local = fract(UV * vec2(textureSize(TEXTURE, 0)) / CELL_PX);
	float v = (run_v.x + local.y) / run_v.y;
	float light = 1.08 - 0.24 * v;
	light += 0.3 * open_sides.z * smoothstep(0.07, 0.0, local.y);
	light -= 0.14 * open_sides.w * smoothstep(0.8, 1.0, local.y);
	float rim = open_sides.x * smoothstep(0.1, 0.0, local.x);
	float shade = open_sides.y * smoothstep(0.72, 1.0, local.x);
	bool glyph_cell = mod(run_v.x + run_h.x, 2.0) < 0.5;
	float cut = glyph_cell ? carve(local, pattern) : 0.0;
	float lip = glyph_cell ? carve(local - vec2(0.0, 0.03), pattern) * (1.0 - cut) : 0.0;
	float value = (t.r / BASE_GREY) * light * (1.0 - 0.32 * cut + 0.14 * lip) * (1.0 - 0.28 * shade);
	vec3 gray = vec3(0.62 * value);
	vec3 colored = tint.rgb * value * (1.0 + 0.3 * glow);
	float s = max(world_saturation, 0.35);
	float g = dot(colored, LUMA);
	colored = clamp(vec3(g) + (colored - vec3(g)) / s, 0.0, 1.0);
	vec3 rgb = mix(gray, colored, saturation);
	rgb = mix(rgb, rgb * DUSK * 1.6, 0.35 * shade);
	rgb += SUN * 0.3 * rim;
	COLOR = vec4(rgb, COLOR.a); // COLOR.a is already the texture's alpha times the modulate
}
