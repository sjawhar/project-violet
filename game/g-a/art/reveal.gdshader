// THROWAWAY (bake-off lane G-A): crystal reveal for tagged cells (docs/bakeoff/mechanic.md, Reveal).
// The crystal textures are untinted pale gray. saturation 0: plain gray (#8c8c8c-ish, unacquired color);
// saturation 1: tinted with the cell's color (acquired); glow adds the color on top (active, pulsed by a tween).
shader_type canvas_item;
uniform float saturation = 0.0;
uniform float glow = 0.0;
uniform vec4 tint : source_color = vec4(1.0);
void fragment() {
	vec4 t = texture(TEXTURE, UV);
	float lum = dot(t.rgb, vec3(0.299, 0.587, 0.114));
	vec3 gray = vec3(lum * 0.7);
	vec3 colored = t.rgb * tint.rgb * 1.25;
	COLOR = vec4(mix(gray, colored, saturation) + glow * tint.rgb, t.a * COLOR.a);
}
