// THROWAWAY (bake-off lane G-C): aerial perspective for a backdrop layer (art/vector_art.gd). Pulls the layer's colours
// toward the horizon haze and flattens their contrast by an amount that grows with the layer's distance, so the mid
// mesas sit behind the near dunes and both behind the playfield. Alpha is kept, so the layer behind still shows.
shader_type canvas_item;
uniform vec4 haze : source_color = vec4(0.87, 0.72, 0.68, 1.0);
uniform float amount = 0.25;
void fragment() {
	COLOR = vec4(mix(COLOR.rgb, haze.rgb, amount), COLOR.a); // COLOR is already the texture times the modulate
}
