extends Node2D

# Bounded experiment only. No production startup, simulation or seed selection.
const CHUNKS := [Vector2i(-1, -1), Vector2i(0, -1), Vector2i(-1, 0), Vector2i(0, 0)]
const OFFSETS := [Vector2i(0, 0), Vector2i(-1, -1), Vector2i(0, -1), Vector2i(1, -1),
	Vector2i(-1, 0), Vector2i(1, 0), Vector2i(-1, 1), Vector2i(0, 1), Vector2i(1, 1)]
const FIELD_MIN := Vector2i(-32, -32)
const FIELD_WIDTH: int = 65
const PRESENTATION_SEED: int = 19
const COLOR_SAMPLE_SEED: int = 19
const RULE_VERSION: int = TerrainResolver.RULE_VERSION
# Ordered rectangles [x, y, width, height, material]. Later patches win.
# Broad interiors, orthogonal edges, pocket, islands and seam-crossing bridges.
const REGIONS := [
	[-30, -30, 26, 26, 1], [4, -30, 26, 26, 1],
	[-20, -20, 6, 6, 0], [-2, -26, 1, 1, 1], [1, -23, 2, 2, 1],
	[-8, -10, 16, 2, 1], [-1, -8, 2, 18, 1],
	[-24, 9, 5, 12, 0], [-22, 14, 1, 1, 1],
	[14, 12, 1, 1, 1], [18, 18, 2, 2, 1], [22, 22, 4, 4, 1]]

@onready var terrain: TileMapLayer = $Terrain
@onready var fixture_camera: Camera2D = $Camera
var _lookup := TerrainAssignmentLookup.new()
var _loaded: Dictionary = {}
var _tint_texture: ImageTexture
var _shading_mode: int = -1
var _boundaries: bool = true
var _selected: int = 0
var _status: Label
var _mode_picker: OptionButton
var _last_operation: String = ""


func _ready() -> void:
	_build_controls()
	if not _lookup.initialize():
		_status.text = "STOP: " + _lookup.error
		return
	_set_shading(0)
	_reload(false)


static func sample_material(cell: Vector2i) -> int:
	var result: int = 0
	# Stair-step irregular boundary across the x=0 chunk seam.
	if cell.y >= 4 and cell.y < 30 and cell.x < 8 + posmod(cell.y, 7):
		result = 1
	for region in REGIONS:
		if Rect2i(region[0], region[1], region[2], region[3]).has_point(cell):
			result = region[4]
	return result


func _generate(coordinate: Vector2i) -> Dictionary:
	var origin := coordinate * WorldCoordinates.CHUNK_TILES
	var halo: Dictionary = {}
	for y in range(-1, WorldCoordinates.CHUNK_TILES + 1):
		for x in range(-1, WorldCoordinates.CHUNK_TILES + 1):
			var cell := origin + Vector2i(x, y)
			halo[cell] = sample_material(cell)
	var assignments: Dictionary = {}
	for y in range(WorldCoordinates.CHUNK_TILES):
		for x in range(WorldCoordinates.CHUNK_TILES):
			var cell := origin + Vector2i(x, y)
			var samples := PackedInt32Array()
			for offset in OFFSETS:
				samples.append(halo[cell + offset])
			var assignment := TerrainResolver.resolve(cell, samples, _lookup, PRESENTATION_SEED, RULE_VERSION)
			if assignment.is_empty():
				return {}
			assignments[cell] = assignment
	return assignments


func _load_chunk(coordinate: Vector2i) -> bool:
	if coordinate not in CHUNKS or not _lookup.error.is_empty():
		return false
	# Build first: failure leaves the old chunk intact. Retire its exact owned cells.
	var assignments := _generate(coordinate)
	if assignments.is_empty():
		_status.text = "STOP: resolver returned no assignment"
		return false
	if _loaded.has(coordinate):
		if _loaded[coordinate] != assignments:
			_status.text = "STOP: regeneration mismatch"
			return false
	_unload_chunk(coordinate)
	for cell in assignments:
		var assignment: Dictionary = assignments[cell]
		terrain.set_cell(cell, assignment.source_id, assignment.atlas_coords, assignment.alternative_id)
	_loaded[coordinate] = assignments
	_last_operation = "Loaded/replaced %s (1024 assignments)" % coordinate
	_update_status()
	return true


func _unload_chunk(coordinate: Vector2i) -> void:
	if not _loaded.has(coordinate):
		return
	for cell in _loaded[coordinate]:
		terrain.erase_cell(cell)
	_loaded.erase(coordinate)
	_last_operation = "Retired %s (all owned cells erased)" % coordinate
	_update_status()


func _reload(reverse_order: bool) -> void:
	for coordinate in CHUNKS:
		_unload_chunk(coordinate)
	var order := CHUNKS.duplicate()
	if reverse_order:
		order.reverse()
	for coordinate in order:
		if not _load_chunk(coordinate):
			return


func _set_shading(mode: int) -> void:
	var shared_material := terrain.material as ShaderMaterial
	shared_material.set_shader_parameter("shading_enabled", mode != 0)
	# Unshaded switching needs no upload. Mode changes alone rebuild the field.
	if mode != 0 and mode != _shading_mode:
		var overlays: Array[Dictionary] = []
		var state := PlanetWorldState.new()
		if mode == 2:
			# Synthetic masks only, outer recovery first, dark core second.
			overlays = [
				{"polygon": PackedVector2Array([Vector2(-800, -480), Vector2(640, -320),
					Vector2(880, 480), Vector2(-640, 640)]), "feather": 768.0, "color": Color(0.35, 0.32, 0.26)},
				{"polygon": PackedVector2Array([Vector2(-320, -160), Vector2(256, -128),
					Vector2(384, 224), Vector2(-256, 320)]), "feather": 384.0, "color": Color(0.12, 0.14, 0.13)}]
			state.set_terrain_color(Vector2i(-12, 0), Color(0.55, 0.30, 0.18))
		# This reuses procedural color -> stored overrides -> ordered masks.
		var generator := PlanetGenerator.new(COLOR_SAMPLE_SEED, overlays, PackedVector2Array(), PackedVector2Array())
		var image := Image.create(FIELD_WIDTH, FIELD_WIDTH, false, Image.FORMAT_RGBAF)
		# 66x66 center samples cover every 65x65 vertex's four contributors.
		var samples: Dictionary = {}
		for y in range(-1, FIELD_WIDTH):
			for x in range(-1, FIELD_WIDTH):
				var cell := FIELD_MIN + Vector2i(x, y)
				samples[cell] = generator.sample_color(cell, state)
		for y in range(FIELD_WIDTH):
			for x in range(FIELD_WIDTH):
				var vertex := FIELD_MIN + Vector2i(x, y)
				var average: Color = (samples[vertex - Vector2i.ONE] + samples[vertex - Vector2i.DOWN]
					+ samples[vertex - Vector2i.RIGHT] + samples[vertex]) / 4.0
				image.set_pixel(x, y, TerrainChunk._earth_tint(average))
		if _tint_texture == null:
			_tint_texture = ImageTexture.create_from_image(image)
		else:
			_tint_texture.update(image)
		shared_material.set_shader_parameter("tint_field", _tint_texture)
		shared_material.set_shader_parameter("field_origin", Vector2(FIELD_MIN) * WorldCoordinates.TERRAIN_SIZE)
		shared_material.set_shader_parameter("field_size", Vector2(FIELD_WIDTH, FIELD_WIDTH))
		shared_material.set_shader_parameter("terrain_size", float(WorldCoordinates.TERRAIN_SIZE))
	_shading_mode = mode


func _build_controls() -> void:
	var panel := VBoxContainer.new()
	panel.position = Vector2(12, 12)
	$Controls.add_child(panel)
	var title := Label.new()
	title.text = "EXPERIMENT | 4 chunks | 64-unit terrain / 32-unit construction | no gameplay"
	panel.add_child(title)
	var row := HBoxContainer.new()
	panel.add_child(row)
	_mode_picker = OptionButton.new()
	for caption in ["Unshaded", "CPU tint", "Crash-style tint + override"]:
		_mode_picker.add_item(caption)
	_mode_picker.item_selected.connect(_set_shading)
	row.add_child(_mode_picker)
	var picker := OptionButton.new()
	for coordinate in CHUNKS:
		picker.add_item(str(coordinate))
	picker.item_selected.connect(func(index: int) -> void: _selected = index)
	row.add_child(picker)
	_button(row, "Load / replace", func() -> void: _load_chunk(CHUNKS[_selected]))
	_button(row, "Unload", func() -> void: _unload_chunk(CHUNKS[_selected]))
	_button(row, "Load forward", func() -> void: _reload(false))
	_button(row, "Load reverse", func() -> void: _reload(true))
	var views := HBoxContainer.new()
	panel.add_child(views)
	_button(views, "Overview", func() -> void: _view(Vector2(0, -192), 0.14))
	_button(views, "Origin / shading", func() -> void: _view(Vector2(0, -192), 0.7))
	_button(views, "Negative / pocket", func() -> void: _view(Vector2(-1088, -1088), 0.7))
	_button(views, "Narrow / seam", func() -> void: _view(Vector2(0, -576), 1.0))
	_button(views, "Irregular / islands", func() -> void: _view(Vector2(896, 1152), 0.7))
	_button(views, "Chunk lines / grid", func() -> void:
		_boundaries = not _boundaries
		queue_redraw())
	_status = Label.new()
	panel.add_child(_status)


func _button(row: HBoxContainer, caption: String, action: Callable) -> void:
	var button := Button.new()
	button.text = caption
	button.pressed.connect(action)
	row.add_child(button)


func _view(point: Vector2, magnification: float) -> void:
	fixture_camera.position = point
	fixture_camera.zoom = Vector2.ONE * magnification


func _update_status() -> void:
	_status.text = "%s | loaded %d/4; cells %d/4096 | %s" % [
		_last_operation, _loaded.size(), _loaded.size() * 1024, str(_loaded.keys())]
	queue_redraw()


func _draw() -> void:
	if not _boundaries:
		return
	for coordinate in CHUNKS:
		var bounds := Rect2(Vector2(coordinate) * WorldCoordinates.CHUNK_SIZE,
			Vector2.ONE * WorldCoordinates.CHUNK_SIZE)
		draw_rect(bounds, Color(1.0, 0.7, 0.2), false, 4.0)
	# Tiny construction grid around origin: terrain origins orange, centers white.
	for step in range(-4, 5):
		var axis := float(step * WorldCoordinates.CONSTRUCTION_SIZE)
		draw_line(Vector2(axis, -128), Vector2(axis, 128), Color(0.8, 0.8, 0.8, 0.5), 1.0)
		draw_line(Vector2(-128, axis), Vector2(128, axis), Color(0.8, 0.8, 0.8, 0.5), 1.0)
	for y in range(-2, 2):
		for x in range(-2, 2):
			var origin := Vector2(x, y) * WorldCoordinates.TERRAIN_SIZE
			draw_circle(origin, 3.0, Color.ORANGE)
			draw_circle(origin + Vector2.ONE * 32.0, 2.0, Color.WHITE)
