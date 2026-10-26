shader_type canvas_item;

uniform bool edge_enabled = true;
uniform vec3 edge_color : source_color = vec3(0.72, 0.67, 0.57);
uniform float edge_strength : hint_range(0.0, 0.6, 0.01) = 0.35;
uniform float edge_width_pixels : hint_range(0.0, 1.5, 0.05) = 0.9;

// Explicit transparent bounds prevent wrapping/clamped border alpha from
// becoming a false neighbor. The sprite's geometry and UVs stay unchanged.
float bounded_alpha(sampler2D sprite_texture, vec2 uv) {
	vec2 inside = step(vec2(0.0), uv) * step(uv, vec2(1.0));
	return texture(sprite_texture, clamp(uv, vec2(0.0), vec2(1.0))).a
		* inside.x * inside.y;
}

void fragment() {
	// Derivatives are evaluated before branching. Offsets track viewport pixels
	// through sprite scaling and camera zoom; no snapping or time modulation.
	vec2 dx = dFdx(UV) * edge_width_pixels;
	vec2 dy = dFdy(UV) * edge_width_pixels;
	if (edge_enabled && edge_strength > 0.0 && edge_width_pixels > 0.0) {
		float alpha = texture(TEXTURE, UV).a;
		float inner_alpha = alpha;
		inner_alpha = min(inner_alpha, bounded_alpha(TEXTURE, UV + dx));
		inner_alpha = min(inner_alpha, bounded_alpha(TEXTURE, UV - dx));
		inner_alpha = min(inner_alpha, bounded_alpha(TEXTURE, UV + dy));
		inner_alpha = min(inner_alpha, bounded_alpha(TEXTURE, UV - dy));
		vec2 diagonal_a = (dx + dy) * 0.70710678;
		vec2 diagonal_b = (dx - dy) * 0.70710678;
		inner_alpha = min(inner_alpha, bounded_alpha(TEXTURE, UV + diagonal_a));
		inner_alpha = min(inner_alpha, bounded_alpha(TEXTURE, UV - diagonal_a));
		inner_alpha = min(inner_alpha, bounded_alpha(TEXTURE, UV + diagonal_b));
		inner_alpha = min(inner_alpha, bounded_alpha(TEXTURE, UV - diagonal_b));

		// Highlight only the inner alpha edge. Suppress faint source fringe;
		// leave interior texture detail and the original output alpha intact.
		float edge = (alpha - inner_alpha) * smoothstep(0.5, 0.95, alpha);
		COLOR.rgb = mix(COLOR.rgb, edge_color, edge * edge_strength);
	}
}
