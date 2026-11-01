shader_type canvas_item;
render_mode unshaded;

// Shared numerical tint data. Each retained chunk owns 33x33 vertex texels.
uniform sampler2D tint_field : filter_linear, repeat_disable;
uniform float slot_count = 7.0;
uniform vec2 exterior_x = vec2(1.0, 0.0);
uniform vec2 exterior_y = vec2(0.0, 1.0);
uniform vec2 exterior_origin = vec2(0.0);
varying vec2 terrain_point;

void vertex() {
	vec2 world_point = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
	terrain_point = exterior_x * world_point.x + exterior_y * world_point.y + exterior_origin;
}

void fragment() {
	// Fragment lookup keeps each tile inside its own slot, including edge vertices
	// beside an unloaded neighbor. GLSL mod matches CPU posmod for negatives.
	vec2 cell_point = terrain_point / 64.0;
	vec2 chunk = floor(cell_point / 32.0);
	vec2 vertex = cell_point - chunk * 32.0;
	vec2 texel = mod(chunk, vec2(slot_count)) * 33.0 + vertex;
	vec2 field_uv = (texel + vec2(0.5)) / (slot_count * 33.0);
	COLOR *= texture(tint_field, field_uv);
}
