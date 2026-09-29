// THROWAWAY (bake-off lane G-C): tag reveal for tagged cells (docs/bakeoff/mechanic.md, Reveal).
// The tag-wall and tag-platform textures are untinted pale gray; their grey value is the shading. saturation 0: plain
// gray (unacquired); saturation 1: the cell's colour (acquired); glow brightens it (active, pulsed by a tween). The
// colour is locked: the texture's base grey maps to exactly the tag colour, brightening scales value instead of adding
// the tint (which washed red out to salmon), and it is pre-saturated against the world saturation post effect so the
// tag red and green read the same whether one or two colours are acquired. Each colour also carries its own shape
// cue for red-green colour-blind players: chevrons on red, waves on green, visible in grey too.
shader_type canvas_item;
global uniform float world_saturation;
uniform float saturation = 0.0;
uniform float glow = 0.0;
uniform vec4 tint : source_color = vec4(1.0);
uniform int pattern = 0; // 1 chevrons (red), 2 waves (green)
const float BASE_GREY = 0.84; // tag-wall.svg's base fill #d6d6d6
const vec3 LUMA = vec3(0.299, 0.587, 0.114);
void fragment() {
	vec4 t = texture(TEXTURE, UV);
	float shade = t.r / BASE_GREY;
	vec2 px = UV * vec2(textureSize(TEXTURE, 0));
	float band = 0.0;
	if (pattern == 1) band = fract((abs(fract(px.x / 128.0) - 0.5) * 128.0 + px.y) / 96.0);
	if (pattern == 2) band = fract((px.y + 16.0 * sin(px.x / 128.0 * 6.2832)) / 96.0);
	float cue = (pattern > 0 && band < 0.2) ? 1.0 : 0.0;
	vec3 gray = vec3(0.62 * shade + 0.12 * cue);
	vec3 colored = tint.rgb * shade * (1.0 + 0.3 * glow) + cue * 0.16 * (vec3(1.0) - tint.rgb);
	float s = max(world_saturation, 0.35);
	float g = dot(colored, LUMA);
	colored = clamp(vec3(g) + (colored - vec3(g)) / s, 0.0, 1.0);
	COLOR = vec4(mix(gray, colored, saturation), t.a * COLOR.a);
}
