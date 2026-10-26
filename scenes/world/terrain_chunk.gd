class_name TerrainChunk
extends Node2D

# Disposable presentation only. No authoritative simulation lives here.
var _colors: PackedColorArray
var _details: Array[Dictionary] = []
var state_revision: int = -1


func configure(coordinate: Vector2i, generator: PlanetGenerator, state: PlanetWorldState) -> void:
	state_revision = state.revision
	position = Vector2(coordinate) * WorldCoordinates.CHUNK_SIZE
	_colors.resize(WorldCoordinates.CHUNK_TILES * WorldCoordinates.CHUNK_TILES)
	_details.clear()
	for y in range(WorldCoordinates.CHUNK_TILES):
		for x in range(WorldCoordinates.CHUNK_TILES):
			var tile := coordinate * WorldCoordinates.CHUNK_TILES + Vector2i(x, y)
			_colors[y * WorldCoordinates.CHUNK_TILES + x] = generator.sample_color(tile, state)
			var detail := generator.sample_detail(tile, state)
			if not detail.is_empty():
				detail.position -= position
				_details.append(detail)
	queue_redraw()


func _draw() -> void:
	for y in range(WorldCoordinates.CHUNK_TILES):
		for x in range(WorldCoordinates.CHUNK_TILES):
			draw_rect(Rect2(Vector2(x, y) * WorldCoordinates.TERRAIN_SIZE,
				Vector2.ONE * WorldCoordinates.TERRAIN_SIZE),
				_colors[y * WorldCoordinates.CHUNK_TILES + x])
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
