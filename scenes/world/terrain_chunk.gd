class_name TerrainChunk
extends Node2D

# Disposable presentation only. No authoritative simulation lives here.
const EARTH_TEXTURES: Array[Texture2D] = [
	preload("res://assets/environment/exterior/weathered_earth_provisional/a_base_soil.png"),
	preload("res://assets/environment/exterior/weathered_earth_provisional/b_compacted_soil.png"),
	preload("res://assets/environment/exterior/weathered_earth_provisional/c_dusty_patches.png"),
	preload("res://assets/environment/exterior/weathered_earth_provisional/d_subtle_gravel.png")]
const VERTEX_WIDTH: int = WorldCoordinates.CHUNK_TILES + 1
const SAMPLE_WIDTH: int = WorldCoordinates.CHUNK_TILES + 2
const TEXTURE_UVS := PackedVector2Array([Vector2.ZERO, Vector2.RIGHT, Vector2.ONE, Vector2.DOWN])

var _colors: PackedColorArray
var _weights: PackedVector3Array
var _details: Array[Dictionary] = []
var state_revision: int = -1


func configure(coordinate: Vector2i, generator: PlanetGenerator, state: PlanetWorldState) -> void:
	state_revision = state.revision
	position = Vector2(coordinate) * WorldCoordinates.CHUNK_SIZE
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	_colors.resize(VERTEX_WIDTH * VERTEX_WIDTH)
	_weights.resize(VERTEX_WIDTH * VERTEX_WIDTH)
	# One-cell halo: shared vertices average the same four original tile-center
	# samples on either side of ANY chunk edge. Original state/mask order remains.
	var samples := PackedColorArray()
	samples.resize(SAMPLE_WIDTH * SAMPLE_WIDTH)
	var origin := coordinate * WorldCoordinates.CHUNK_TILES
	for y in range(SAMPLE_WIDTH):
		for x in range(SAMPLE_WIDTH):
			samples[y * SAMPLE_WIDTH + x] = generator.sample_color(origin + Vector2i(x - 1, y - 1), state)
	for y in range(VERTEX_WIDTH):
		for x in range(VERTEX_WIDTH):
			var index := y * VERTEX_WIDTH + x
			var color := (samples[y * SAMPLE_WIDTH + x] + samples[y * SAMPLE_WIDTH + x + 1]
				+ samples[(y + 1) * SAMPLE_WIDTH + x] + samples[(y + 1) * SAMPLE_WIDTH + x + 1]) / 4.0
			# Normalize the provisional family's base RGB so legacy colors, stored
			# modifications and authored crash-site overlays still control the tint.
			_colors[index] = Color(color.r * 255.0 / 156.0, color.g * 255.0 / 141.0,
				color.b * 255.0 / 121.0, color.a)
			_weights[index] = generator.weathered_earth_weights(origin + Vector2i(x, y))
	_details.clear()
	for y in range(WorldCoordinates.CHUNK_TILES):
		for x in range(WorldCoordinates.CHUNK_TILES):
			var tile := coordinate * WorldCoordinates.CHUNK_TILES + Vector2i(x, y)
			var detail := generator.sample_detail(tile, state)
			if not detail.is_empty():
				detail.position -= position
				_details.append(detail)
	queue_redraw()


func _draw() -> void:
	for y in range(WorldCoordinates.CHUNK_TILES):
		for x in range(WorldCoordinates.CHUNK_TILES):
			var point := Vector2(x, y) * WorldCoordinates.TERRAIN_SIZE
			var size := float(WorldCoordinates.TERRAIN_SIZE)
			var vertices := PackedVector2Array([point, point + Vector2(size, 0),
				point + Vector2(size, size), point + Vector2(0, size)])
			var index := y * VERTEX_WIDTH + x
			var indices := PackedInt32Array([index, index + 1, index + VERTEX_WIDTH + 1, index + VERTEX_WIDTH])
			var colors := PackedColorArray([_colors[indices[0]], _colors[indices[1]],
				_colors[indices[2]], _colors[indices[3]]])
			draw_polygon(vertices, colors, TEXTURE_UVS, EARTH_TEXTURES[0])
			# Three quiet, broad treatments alpha-composite over opaque Base Soil.
			# Shared vertex alphas interpolate continuously; no per-cell RNG choice.
			for treatment in range(3):
				var visible_weight := 0.0
				for corner in range(4):
					colors[corner] = _colors[indices[corner]]
					var weight: float = _weights[indices[corner]][treatment]
					colors[corner].a *= weight
					visible_weight = maxf(visible_weight, weight)
				if visible_weight > 0.0:
					draw_polygon(vertices, colors, TEXTURE_UVS, EARTH_TEXTURES[treatment + 1])
	# Low ground details render below all Y-sorted authored objects and Dave.
	for detail in _details:
		var point: Vector2 = detail.position
		match int(detail.kind):
			0:
				draw_circle(point, 7.0, Color(0.39, 0.42, 0.41))
				draw_line(point + Vector2(-4, -2), point + Vector2(3, -3), Color(0.49, 0.50, 0.46), 2.0)
			1:
				draw_circle(point, 9.0, Color(0.23, 0.29, 0.20))
				draw_circle(point + Vector2(5, -4), 5.0, Color(0.32, 0.38, 0.24))
			2:
				draw_line(point + Vector2(-5, 3), point + Vector2(1, -9), Color(0.42, 0.39, 0.31), 3.0)
				draw_line(point + Vector2(1, 0), point + Vector2(7, -6), Color(0.42, 0.39, 0.31), 2.0)
