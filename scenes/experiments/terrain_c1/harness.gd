extends Node2D
## Fixed C1 comparison harness; never registered as a construction/gameplay world.
const ASSETS := "res://assets/experiments/terrain_c1/"
const COORDS := [Vector2i(-1, -1), Vector2i(0, -1), Vector2i(-1, 0), Vector2i(0, 0)]
const CAMERAS := [Vector2(-1100, 750), Vector2(0, -1700), Vector2.ZERO, Vector2(-384, -192)]
const CANDIDATE_SHADER = preload("res://scenes/experiments/terrain_c1/continuous.gdshader")
var _fixture: Dictionary
var _fields: Dictionary[Vector2i, Image] = {}
var _field_textures: Dictionary[Vector2i, Texture2D] = {}
var _phase_textures: Dictionary[Vector2i, Texture2D] = {}
var _surfaces: Dictionary[Vector2i, Polygon2D] = {}
var _active: Dictionary[Vector2i, int] = {}
var _pending: Array[Vector2i] = []
var _token: int = 0
var _epoch: int = 0
var _receipt_epoch: int = -1
var _request_seed: int = -1
var _request_revision: int = -1
var _ready_for_view: bool = false
var _candidate_visible: bool = true
var _normal_tint: bool = false
var _diagnostic: int = 0
var _failure: String = ""
var _baseline: IllustratedTerrainPresenter
var _baseline_layer: TileMapLayer
var _baseline_tint: Image
var _baseline_texture: ImageTexture
var _baseline_material: ShaderMaterial
var _white_texture: ImageTexture
var _earth: ImageTexture
var _green: ImageTexture
var _generator: PlanetGenerator
var _state: PlanetWorldState
var _foreground: Node2D
var _grid: Node2D


func _ready() -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(ASSETS + "fixture.json"))
	if not parsed is Dictionary:
		_fail("Missing C1 fixture")
		return
	_fixture = parsed
	if _fixture.get("seed") != 26026 or _fixture.get("rule") != "c1_fields_v1" \
			or _fixture.get("art") != "c1_materials_v1" or _fixture.get("regions", []).size() != 4:
		_fail("Unexpected C1 fixture identity")
		return
	for record: Dictionary in _fixture.regions:
		var coordinate := Vector2i(int(record.coord[0]), int(record.coord[1]))
		if coordinate not in COORDS or _fields.has(coordinate):
			_fail("Invalid/duplicate C1 region")
			return
		var field := load(ASSETS + str(record.field)) as Texture2D
		var phase := load(ASSETS + str(record.phase)) as Texture2D
		if field == null or phase == null or field.get_size() != Vector2(137, 137) or phase.get_size() != Vector2(7, 7):
			_fail("Missing/malformed field assets")
			return
		var image := field.get_image()
		if image == null or image.is_empty():
			_fail("Unreadable numerical field")
			return
		if image.is_compressed() and image.decompress() != OK:
			_fail("Cannot decompress numerical field")
			return
		_fields[coordinate] = image
		_field_textures[coordinate] = field
		_phase_textures[coordinate] = phase
	_earth = _material_texture("earth")
	_green = _material_texture("green")
	if _earth == null or _green == null:
		return
	var overlays: Array[Dictionary] = []
	for entry: Dictionary in _fixture.overlays:
		overlays.append({"polygon": _polygon(entry.polygon), "color": Color(float(entry.color[0]),
			float(entry.color[1]), float(entry.color[2]), float(entry.color[3])), "feather": float(entry.feather)})
	_generator = PlanetGenerator.new(int(_fixture.seed), overlays, _polygon(_fixture.gameplay), _polygon(_fixture.anchors))
	_state = PlanetWorldState.new(int(_fixture.seed))
	_baseline = IllustratedTerrainPresenter.new()
	_baseline.z_index = -11
	_baseline_layer = TileMapLayer.new()
	_baseline_layer.name = "Terrain"
	_baseline_layer.scale = Vector2.ONE * 0.5
	# Both comparison materials use linear base filtering. Candidate generates mips.
	_baseline_layer.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	_baseline_layer.collision_enabled = false
	_baseline_layer.navigation_enabled = false
	_baseline_layer.occlusion_enabled = false
	_baseline.add_child(_baseline_layer)
	add_child(_baseline)
	var initialized := _baseline.initialize()
	if not initialized.ok:
		_fail(str(initialized))
		return
	_baseline_tint = Image.create(231, 231, false, Image.FORMAT_RGBAF)
	_baseline_tint.fill(Color.WHITE)
	_baseline_texture = ImageTexture.create_from_image(_baseline_tint)
	var white := Image.create(1, 1, false, Image.FORMAT_RGBAF)
	white.fill(Color.WHITE)
	_white_texture = ImageTexture.create_from_image(white)
	_baseline_material = ShaderMaterial.new()
	_baseline_material.shader = load("res://scenes/world/illustrated_terrain_tint.gdshader") as Shader
	_baseline_material.set_shader_parameter("tint_field", _white_texture)
	_baseline_material.set_shader_parameter("slot_count", 7.0)
	_baseline_layer.material = _baseline_material
	_make_references()
	_rebuild(false)
	_apply_view()


func _polygon(values: Array) -> PackedVector2Array:
	var result := PackedVector2Array()
	for pair: Array in values:
		result.append(Vector2(float(pair[0]), float(pair[1])))
	return result


func _material_texture(family: String) -> ImageTexture:
	var source := load(ASSETS + "sources/" + family + ".png") as Texture2D
	if source == null:
		_fail("Missing C1 material " + family)
		return null
	var image := source.get_image()
	if image == null or image.is_empty():
		_fail("Unreadable C1 material")
		return null
	if image.is_compressed() and image.decompress() != OK:
		_fail("Cannot decompress C1 material")
		return null
	# Once per fixed source; no per-frame generation, no disk writes.
	if image.generate_mipmaps() != OK:
		_fail("Cannot generate material mipmaps")
		return null
	return ImageTexture.create_from_image(image)


func _field_at(point: Vector2) -> Color:
	var coordinate := Vector2i(clampi(floori(point.x / 2048.0), -1, 0), clampi(floori(point.y / 2048.0), -1, 0))
	var local := (point - Vector2(coordinate) * 2048.0) / 16.0 + Vector2.ONE * 4.0
	if local.x < 0 or local.y < 0 or local.x > 136 or local.y > 136:
		_fail("Fixture sample outside supported bounds/gutter")
		return Color.BLACK
	var first := Vector2i(floori(local.x), floori(local.y))
	var last := Vector2i(mini(first.x + 1, 136), mini(first.y + 1, 136))
	var image: Image = _fields[coordinate]
	var north := image.get_pixel(first.x, first.y).lerp(image.get_pixel(last.x, first.y), local.x - first.x)
	var south := image.get_pixel(first.x, last.y).lerp(image.get_pixel(last.x, last.y), local.x - first.x)
	return north.lerp(south, local.y - first.y)


func _sample_material(cell: Vector2i) -> int:
	return int(_field_at((Vector2(cell) + Vector2.ONE * 0.5) * 64.0).r >= 0.5)


func _rebuild(reverse_order: bool) -> void:
	if _state.seed_value != int(_fixture.seed):
		_fail("C1 supports only its fixed authored seed")
		return
	_epoch += 1
	_request_seed = _state.seed_value
	_request_revision = _state.revision
	_receipt_epoch = -1
	_ready_for_view = false
	$CanvasLayer/Curtain.show()
	_pending.assign(COORDS)
	if reverse_order:
		_pending.reverse()
	_update_status()


func _prepare_chunk(coordinate: Vector2i, generation: int) -> void:
	_token += 1
	var token := _token
	var chunk := TerrainChunk.new()
	chunk.configure(coordinate, _generator, _state, false)
	var tint := Image.create(33, 33, false, Image.FORMAT_RGBAF)
	chunk.write_tint(tint, Vector2i.ZERO)
	chunk.free() # No primitive decoration in either material comparison view.
	var material := ShaderMaterial.new()
	material.shader = CANDIDATE_SHADER
	material.set_shader_parameter("earth_art", _earth)
	material.set_shader_parameter("green_art", _green)
	material.set_shader_parameter("region_field", _field_textures[coordinate])
	material.set_shader_parameter("phase_field", _phase_textures[coordinate])
	material.set_shader_parameter("tint_field", ImageTexture.create_from_image(tint))
	material.set_shader_parameter("normal_tint", _normal_tint)
	material.set_shader_parameter("diagnostic", _diagnostic)
	var surface := Polygon2D.new()
	surface.texture = _white_texture
	surface.position = Vector2(coordinate) * 2048.0
	surface.polygon = PackedVector2Array([Vector2.ZERO, Vector2(2048, 0), Vector2(2048, 2048), Vector2(0, 2048)])
	surface.uv = PackedVector2Array([Vector2.ZERO, Vector2.RIGHT, Vector2.ONE, Vector2.DOWN])
	surface.material = material
	surface.z_index = -11
	surface.visible = _candidate_visible
	if generation != _epoch or _state.seed_value != _request_seed \
			or _state.revision != _request_revision or not _failure.is_empty():
		surface.free()
		_fail("C1 preparation identity changed")
		return
	var registered := _baseline.begin_generation(coordinate, token)
	if not registered.ok:
		surface.free()
		_fail(str(registered))
		return
	var result := _baseline.present_chunk(coordinate, token, Callable(self, "_sample_material"), int(_fixture.seed), TerrainResolver.RULE_VERSION)
	if not result.ok or not _failure.is_empty():
		surface.free()
		_fail(str(result))
		return
	var slot := Vector2i(posmod(coordinate.x, 7), posmod(coordinate.y, 7)) * 33
	_baseline_tint.blit_rect(tint, Rect2i(0, 0, 33, 33), slot)
	_baseline_texture.update(_baseline_tint)
	if _surfaces.has(coordinate):
		var old: Polygon2D = _surfaces[coordinate]
		remove_child(old)
		old.queue_free()
	add_child(surface)
	_surfaces[coordinate] = surface
	_active[coordinate] = token


func _retire(coordinate: Vector2i, token: int) -> bool:
	if _active.get(coordinate, -1) != token:
		return false
	var result := _baseline.retire_chunk(coordinate, token)
	if not result.ok:
		_fail(str(result))
		return false
	var surface: Polygon2D = _surfaces[coordinate]
	remove_child(surface)
	surface.queue_free()
	_surfaces.erase(coordinate)
	_active.erase(coordinate)
	return true


func _process(delta: float) -> void:
	if not _failure.is_empty() or _fixture.is_empty():
		return
	if _state.seed_value != _request_seed or _state.revision != _request_revision:
		_fail("C1 state changed; request a new explicit reconstruction")
		return
	if not _pending.is_empty():
		_prepare_chunk(_pending.pop_front(), _epoch) # Exactly one fixed chunk per frame.
		if _pending.is_empty() and _active.size() == 4 and _failure.is_empty():
			_receipt_epoch = _epoch
			_ready_for_view = true
			$CanvasLayer/Curtain.hide()
		_update_status()
	if _ready_for_view and _receipt_epoch == _epoch:
		var direction := Vector2(float(Input.is_physical_key_pressed(KEY_D)) - float(Input.is_physical_key_pressed(KEY_A)),
			float(Input.is_physical_key_pressed(KEY_S)) - float(Input.is_physical_key_pressed(KEY_W)))
		$Camera2D.position += direction * delta * 350.0 / $Camera2D.zoom.x
		_clamp_camera()


func _unhandled_key_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key == null or not key.pressed or key.echo or not _failure.is_empty():
		return
	match key.physical_keycode:
		KEY_B:
			_candidate_visible = not _candidate_visible
		KEY_T:
			_normal_tint = not _normal_tint
		KEY_F:
			_diagnostic = (_diagnostic + 1) % 4
			_candidate_visible = true
		KEY_G:
			_grid.visible = not _grid.visible
		KEY_H:
			_foreground.visible = not _foreground.visible
		KEY_R:
			for coordinate: Vector2i in _active.keys():
				if not _retire(coordinate, _active[coordinate]):
					return
			_rebuild(false)
		KEY_V:
			_rebuild(true)
		KEY_1:
			$Camera2D.zoom = Vector2.ONE
		KEY_2:
			$Camera2D.zoom = Vector2.ONE * 0.5
		KEY_3:
			$Camera2D.zoom = Vector2.ONE * 1.5
		KEY_4, KEY_5, KEY_6, KEY_7:
			$Camera2D.position = CAMERAS[key.physical_keycode - KEY_4]
	_apply_view()


func _apply_view() -> void:
	if _baseline == null:
		return
	_baseline.visible = not _candidate_visible
	var inverse := global_transform.affine_inverse()
	_baseline_material.set_shader_parameter("exterior_x", inverse.x)
	_baseline_material.set_shader_parameter("exterior_y", inverse.y)
	_baseline_material.set_shader_parameter("exterior_origin", inverse.origin)
	_baseline_material.set_shader_parameter("tint_field", _baseline_texture if _normal_tint else _white_texture)
	for surface: Polygon2D in _surfaces.values():
		surface.visible = _candidate_visible
		var material := surface.material as ShaderMaterial
		material.set_shader_parameter("normal_tint", _normal_tint)
		material.set_shader_parameter("diagnostic", _diagnostic)
	_clamp_camera()
	_update_status()


func _clamp_camera() -> void:
	var half_view: Vector2 = get_viewport_rect().size / ($Camera2D.zoom * 2.0)
	half_view = Vector2(minf(2048.0, half_view.x), minf(2048.0, half_view.y))
	$Camera2D.position = $Camera2D.position.clamp(Vector2.ONE * -2048.0 + half_view,
		Vector2.ONE * 2048.0 - half_view)


func _update_status() -> void:
	$CanvasLayer/Status.text = "C1 ISOLATED / %s / tint %s / diagnostic %d / ready %s / epoch %d\nB baseline/candidate | T tint | F field | G junction | H references | R retire/reload | V reverse rebuild\n1/2/3 zoom 1.0/0.5/1.5 | 4 recovery / 5 grass / 6 origin / 7 ship | WASD pan\nHarness only; owner runtime acceptance pending. No production arrival proof. %s" % [
		"CANDIDATE" if _candidate_visible else "BASELINE", "NORMAL" if _normal_tint else "NEUTRAL",
		_diagnostic, str(_ready_for_view), _epoch, _failure]


func _fail(message: String) -> void:
	_failure = message
	_ready_for_view = false
	$CanvasLayer/Curtain.show()
	_update_status()
	push_error("C1 stopped: " + message)


func _make_references() -> void:
	_foreground = Node2D.new()
	add_child(_foreground)
	for entry: Array in [
		["crashed_ship_contact_shadow_prototype.png", Vector2(-1063, -785), 0.7, false, -1],
		["crashed_exploration_ship_approved.png", Vector2(-979, -701), 0.7, false, 0],
		["ferrite/faceted_ferrite_10x6.png", Vector2(96, 96), 0.5, false, -5]]:
		var sprite := Sprite2D.new()
		sprite.texture = load("res://assets/environment/exterior/" + str(entry[0])) as Texture2D
		sprite.position = entry[1]
		sprite.scale = Vector2.ONE * float(entry[2])
		sprite.centered = entry[3]
		sprite.z_index = entry[4]
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
		_foreground.add_child(sprite)
	_grid = Node2D.new()
	_grid.z_index = 10
	_grid.visible = false
	add_child(_grid)
	for points: PackedVector2Array in [PackedVector2Array([Vector2(-2048, 0), Vector2(2048, 0)]),
		PackedVector2Array([Vector2(0, -2048), Vector2(0, 2048)])]:
		var line := Line2D.new()
		line.points = points
		line.width = 2.0
		line.default_color = Color(0.6, 0.95, 1.0, 0.8)
		_grid.add_child(line)
