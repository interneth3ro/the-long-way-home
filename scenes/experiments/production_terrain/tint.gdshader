shader_type canvas_item;
render_mode unshaded;

// Linear numerical tint data, not a source_color artwork texture.
uniform sampler2D tint_field : filter_linear, repeat_disable;
uniform vec2 field_origin = vec2(-2048.0);
uniform vec2 field_size = vec2(65.0);
uniform float terrain_size = 64.0;
uniform bool shading_enabled = false;
varying vec4 terrain_tint;

void vertex() {
	vec2 world_point = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
	vec2 field_vertex = (world_point - field_origin) / terrain_size;
	vec2 field_uv = (field_vertex + vec2(0.5)) / field_size;
	terrain_tint = shading_enabled ? textureLod(tint_field, field_uv, 0.0) : vec4(1.0);
}

void fragment() {
	COLOR *= terrain_tint;
}
