// THROWAWAY (bake-off lane G-A): the world saturation post effect (docs/bakeoff/mechanic.md, Reveal).
shader_type canvas_item;
uniform sampler2D screen : hint_screen_texture;
global uniform float world_saturation;
void fragment() { vec4 c = texture(screen, SCREEN_UV); float g = dot(c.rgb, vec3(0.299, 0.587, 0.114)); COLOR = vec4(mix(vec3(g), c.rgb, world_saturation), 1.0); }
