shader_type canvas_item;
render_mode unshaded;

uniform sampler2D earth_art : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D green_art : source_color, filter_linear_mipmap, repeat_disable;
// Numerical fields: no source_color conversion and no mipmaps.
uniform sampler2D region_field : filter_linear, repeat_disable;
uniform sampler2D phase_field : filter_nearest, repeat_disable;
uniform sampler2D tint_field : filter_linear, repeat_disable;
uniform bool normal_tint = false;
uniform int diagnostic = 0;
varying vec2 local_point;

void vertex() {
    // CanvasItem VERTEX is local pixel space. Never hash a floating world point.
    local_point = VERTEX;
}

vec3 window_sample(sampler2D art, vec2 lattice, vec2 p) {
    // CPU-authored SHA-256 identities: metadata grid covers local lattice -1..5.
    vec3 phase = texture(phase_field, (lattice + vec2(1.5)) / 7.0).rgb;
    float scale_value = 0.8 + 0.2 * phase.b;
    vec2 uv = vec2(0.35) + 0.3 * phase.rg + (p - lattice * 512.0) / 2048.0 * scale_value;
    // Interior windows stay in .10..90. Explicit gradients exclude phase jumps.
    return textureGrad(art, uv, dFdx(local_point) / 2048.0 * scale_value,
        dFdy(local_point) / 2048.0 * scale_value).rgb;
}

vec3 material_sample(sampler2D art, vec2 p) {
    vec2 lattice = floor(p / 512.0);
    vec2 f = fract(p / 512.0);
    vec2 blend = f * f * (vec2(3.0) - 2.0 * f);
    vec3 north = mix(window_sample(art, lattice, p), window_sample(art, lattice + vec2(1.0, 0.0), p), blend.x);
    vec3 south = mix(window_sample(art, lattice + vec2(0.0, 1.0), p), window_sample(art, lattice + vec2(1.0), p), blend.x);
    return mix(north, south, blend.y);
}

void fragment() {
    vec3 field = texture(region_field, (local_point / 16.0 + vec2(4.5)) / 137.0).rgb;
    vec3 earth = material_sample(earth_art, local_point);
    vec3 green = material_sample(green_art, local_point);
    // Density field controls detail contrast, not gameplay vegetation/population.
    green = mix(vec3(0.10, 0.18, 0.025), green, 0.45 + 0.55 * field.b);
    vec3 color = mix(earth, green, field.r);
    color *= 0.91 + 0.18 * field.g;
    color *= mix(vec3(1.0), vec3(0.96 + 0.08 * field.b, 1.0, 1.025 - 0.05 * field.b), field.r);
    if (normal_tint) {
        color *= texture(tint_field, (local_point / 64.0 + vec2(0.5)) / 33.0).rgb;
    }
    if (diagnostic == 1) { color = vec3(field.r); }
    if (diagnostic == 2) { color = vec3(field.g); }
    if (diagnostic == 3) { color = vec3(field.b); }
    COLOR = vec4(color, 1.0);
}
