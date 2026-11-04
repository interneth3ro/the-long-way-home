shader_type canvas_item;
render_mode unshaded;

uniform sampler2D earth_art : source_color, filter_linear, repeat_disable;
uniform sampler2D green_art : source_color, filter_linear, repeat_disable;
// Runtime R8 IDs, not color: exact level-zero fetches, no sRGB or mipmaps.
uniform sampler2D material_ids : filter_nearest, repeat_disable;
uniform sampler2D phase_field : filter_nearest, repeat_disable;
uniform sampler2D c1_field : filter_linear, repeat_disable;
uniform int diagnostic = 0;
varying vec2 local_point;

void vertex() {
    local_point = VERTEX;
}

float green_at(ivec2 cell) {
    int id = int(round(texelFetch(material_ids, cell + ivec2(1), 0).r * 255.0));
    return float(id > 0);
}

float coverage(vec2 p) {
    vec2 q = (p - vec2(32.0)) / 64.0;
    ivec2 cell = ivec2(floor(q));
    vec2 f = fract(q);
    vec2 w = f * f * (vec2(3.0) - 2.0 * f);
    float north = mix(green_at(cell), green_at(cell + ivec2(1, 0)), w.x);
    float south = mix(green_at(cell + ivec2(0, 1)), green_at(cell + ivec2(1)), w.x);
    float value = mix(north, south, w.y);
    // Candidate A, a=5/32. No continuous protection multiplier P.
    return smoothstep(5.0 / 32.0, 27.0 / 32.0, value);
}

vec3 window_sample(sampler2D art, vec2 lattice, vec2 p) {
    // Frozen C1 SHA-256 phases already encode absolute lattice coordinates.
    vec3 phase = texelFetch(phase_field, ivec2(lattice) + ivec2(1), 0).rgb;
    float scale_value = 0.8 + 0.2 * phase.b;
    vec2 uv = vec2(0.35) + 0.3 * phase.rg + (p - lattice * 512.0) / 2048.0 * scale_value;
    return textureGrad(art, uv, dFdx(local_point) / 2048.0 * scale_value,
        dFdy(local_point) / 2048.0 * scale_value).rgb;
}

vec3 material_sample(sampler2D art, vec2 p) {
    vec2 lattice = floor(p / 512.0);
    vec2 f = fract(p / 512.0);
    vec2 w = f * f * (vec2(3.0) - 2.0 * f);
    vec3 north = mix(window_sample(art, lattice, p), window_sample(art, lattice + vec2(1, 0), p), w.x);
    vec3 south = mix(window_sample(art, lattice + vec2(0, 1), p), window_sample(art, lattice + vec2(1), p), w.x);
    return mix(north, south, w.y);
}

void fragment() {
    float amount = coverage(local_point);
    // C1 red coverage is deliberately unused. G/B retain C1 macro/detail shading.
    vec3 field = texture(c1_field, (local_point / 16.0 + vec2(4.5)) / 137.0).rgb;
    vec3 earth = material_sample(earth_art, local_point);
    vec3 green = material_sample(green_art, local_point);
    green = mix(vec3(0.10, 0.18, 0.025), green, 0.45 + 0.55 * field.b);
    vec3 color = mix(earth, green, amount);
    color *= 0.91 + 0.18 * field.g;
    color *= mix(vec3(1), vec3(0.96 + 0.08 * field.b, 1, 1.025 - 0.05 * field.b), amount);
    if (diagnostic == 1) { color = vec3(amount); }
    if (diagnostic == 2) {
        ivec2 cell = ivec2(floor(local_point / 64.0));
        float id = texelFetch(material_ids, cell + ivec2(1), 0).r * 255.0;
        color = vec3(id / 4.0, float(id > 0.5), 0.0);
    }
    COLOR = vec4(color, 1);
}
