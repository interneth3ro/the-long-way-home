shader_type canvas_item;
render_mode unshaded;

// Experimental TileData material only. Original PNGs remain byte-identical.
// Each source is one 128px tile, with atlas padding disabled for local UVs.
uniform sampler2D earth : source_color, filter_nearest, repeat_disable;
uniform sampler2D green : source_color, filter_nearest, repeat_disable;
uniform vec2 mirror = vec2(0.0);
uniform vec3 top;
uniform vec3 bottom;
uniform vec3 left;
uniform vec3 right;
varying vec4 vertex_tint;

void vertex() {
	vertex_tint = COLOR;
}

float edge_terrain(float t, vec3 peers) {
	if (t <= 0.5) {
		return mix(peers.x, peers.y, smoothstep(0.0, 0.5, t));
	}
	return mix(peers.y, peers.z, smoothstep(0.5, 1.0, t));
}

void fragment() {
	vec2 pixel = clamp(UV * 128.0 - 0.5, vec2(0.0), vec2(127.0));
	vec2 point = pixel / 127.0;
	vec2 art_uv = mix(UV, vec2(1.0) - UV, mirror);
	vec4 original = texture(TEXTURE, art_uv);
	vec2 distance_xy = min(pixel, vec2(127.0) - pixel);
	float distance_to_edge = min(distance_xy.x, distance_xy.y);
	float terrain;
	if (distance_xy.x <= distance_xy.y) {
		terrain = edge_terrain(point.y, point.x <= 0.5 ? left : right);
	} else {
		terrain = edge_terrain(point.x, point.y <= 0.5 ? top : bottom);
	}
	vec4 compatible = mix(texture(earth, UV), texture(green, UV), terrain);
	float correction = 1.0 - smoothstep(0.0, 8.0, distance_to_edge);
	COLOR = mix(original, compatible, correction) * vertex_tint;
}
