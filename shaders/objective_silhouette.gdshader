shader_type canvas_item;
render_mode unshaded;

uniform bool outline_enabled = false;
// Source texels: 5 * 0.16 * 1.25 = 1 screen pixel at camera zoom 1.
uniform float outline_width : hint_range(0.0, 8.0, 0.25) = 5.0;
uniform vec4 outline_color : source_color = vec4(0.65, 0.43, 0.19, 0.55);
varying vec4 vertex_color;

void vertex() {
	vertex_color = COLOR;
	// Expand the quad, then remap UVs below so edge-touching alpha is not clipped.
	VERTEX += (UV * 2.0 - 1.0) * outline_width;
}

vec4 source_at(sampler2D source_texture, vec2 uv) {
	if (any(lessThan(uv, vec2(0.0))) || any(greaterThan(uv, vec2(1.0)))) {
		return vec4(0.0);
	}
	return texture(source_texture, uv);
}

void fragment() {
	vec2 size = 1.0 / TEXTURE_PIXEL_SIZE;
	vec2 uv = (UV * (size + 2.0 * outline_width) - outline_width) / size;
	vec4 base = source_at(TEXTURE, uv);
	float coverage = 0.0;
	if (outline_enabled) {
		for (int i = 0; i < 8; i++) {
			float angle = float(i) * 0.78539816339;
			vec2 step_uv = vec2(cos(angle), sin(angle)) * TEXTURE_PIXEL_SIZE * outline_width;
			coverage = max(coverage, source_at(TEXTURE, uv + step_uv).a);
		}
	}
	// Ignore faint source specks, soften the silhouette, composite behind original RGBA.
	float rim = smoothstep(0.08, 0.45, coverage) * outline_color.a;
	float alpha = base.a + rim * (1.0 - base.a);
	vec3 rgb = (base.rgb * base.a + outline_color.rgb * rim * (1.0 - base.a)) / max(alpha, 0.00001);
	COLOR = vec4(rgb, alpha) * vertex_color;
}
