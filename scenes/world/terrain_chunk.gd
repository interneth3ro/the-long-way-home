class_name TerrainChunk
extends Node2D

# Disposable presentation only. No authoritative simulation lives here.
const BASE_SOIL: Texture2D = preload("res://assets/environment/exterior/weathered_earth_provisional/a_base_soil.png")
const GROUND_TEXTURES: Array[Texture2D] = [BASE_SOIL,
	preload("res://assets/environment/exterior/low_green_ground_cover_provisional/a_balanced_cover.png"),
	preload("res://assets/environment/exterior/low_green_ground_cover_provisional/b_moss_dominant.png"),
	preload("res://assets/environment/exterior/low_green_ground_cover_provisional/c_exposed_earth.png"),
	preload("res://assets/environment/exterior/low_green_ground_cover_provisional/d_fine_grass.png")]
const VERTEX_WIDTH: int = WorldCoordinates.CHUNK_TILES + 1
const SAMPLE_WIDTH: int = WorldCoordinates.CHUNK_TILES + 2
# Packed-array construction is a runtime initializer, not a constant expression.
# Share one UV array across chunks rather than rebuilding it during drawing.
static var _texture_uvs := PackedVector2Array([Vector2.ZERO, Vector2.RIGHT, Vector2.ONE, Vector2.DOWN])

var _colors: PackedColorArray
var _ground_materials: PackedByteArray
var _details: Array[Dictionary] = []
var state_revision: int = -1
var _draw_legacy_ground: bool = true


func configure(coordinate: Vector2i, generator: PlanetGenerator, state: PlanetWorldState,
		draw_legacy_ground: bool = true) -> void:
	_draw_legacy_ground = draw_legacy_ground
	state_revision = state.revision
	position = Vector2(coordinate) * WorldCoordinates.CHUNK_SIZE
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	_colors.resize(VERTEX_WIDTH * VERTEX_WIDTH)
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
			_colors[index] = _earth_tint(color)
	_details.clear()
	if _draw_legacy_ground:
		_ground_materials.resize(WorldCoordinates.CHUNK_TILES * WorldCoordinates.CHUNK_TILES)
	for y in range(WorldCoordinates.CHUNK_TILES):
		for x in range(WorldCoordinates.CHUNK_TILES):
			var tile := coordinate * WorldCoordinates.CHUNK_TILES + Vector2i(x, y)
			if _draw_legacy_ground:
				_ground_materials[y * WorldCoordinates.CHUNK_TILES + x] = generator.sample_ground_material(tile)
			var detail := generator.sample_detail(tile, state)
			if not detail.is_empty():
				detail.position -= position
				_details.append(detail)
	queue_redraw()


# Decision 16B: keep the texture's brown hue. Legacy masks/edits provide only
# modest shading and warmth; green bias darkens earth instead of tinting it green.
static func _earth_tint(color: Color) -> Color:
	var mean := (color.r + color.g + color.b) / 3.0
	var green_bias := maxf(0.0, color.g - (color.r + color.b) * 0.5)
	var brightness := clampf(0.94 + (mean - 0.30) * 0.4 - green_bias, 0.84, 0.99)
	var warmth := clampf((color.r - color.b) * 0.15, -0.015, 0.015)
	return Color(brightness + warmth, brightness, brightness - warmth, color.a)


func _draw() -> void:
	if _draw_legacy_ground:
		for y in range(WorldCoordinates.CHUNK_TILES):
			for x in range(WorldCoordinates.CHUNK_TILES):
				var point := Vector2(x, y) * WorldCoordinates.TERRAIN_SIZE
				var size := float(WorldCoordinates.TERRAIN_SIZE)
				var vertices := PackedVector2Array([point, point + Vector2(size, 0),
					point + Vector2(size, size), point + Vector2(0, size)])
				var index := y * VERTEX_WIDTH + x
				var colors := PackedColorArray([_colors[index], _colors[index + 1],
					_colors[index + VERTEX_WIDTH + 1], _colors[index + VERTEX_WIDTH]])
				var ground_material := int(_ground_materials[y * WorldCoordinates.CHUNK_TILES + x])
				draw_polygon(vertices, colors, _texture_uvs, GROUND_TEXTURES[ground_material])
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


# Copy the already calculated halo-averaged vertices, without resampling.
func write_tint(image: Image, origin: Vector2i) -> void:
	for y in range(VERTEX_WIDTH):
		for x in range(VERTEX_WIDTH):
			image.set_pixelv(origin + Vector2i(x, y), _colors[y * VERTEX_WIDTH + x])
