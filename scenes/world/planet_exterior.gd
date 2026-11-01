class_name PlanetExterior
extends Node2D

enum TerrainRenderer { LEGACY, ILLUSTRATED }
@export var terrain_renderer: TerrainRenderer = TerrainRenderer.ILLUSTRATED

@export_range(1, 4, 1) var loading_radius: int = 2
@export_range(1, 2, 1) var retention_margin: int = 1
@export_range(1, 8, 1) var chunks_per_frame: int = 2
# Independent of visual scar polygons: ship, approach and initial factory/Ferrite clearing.
@export var protected_gameplay := PackedVector2Array([
	Vector2(-720, -544), Vector2(192, -544), Vector2(832, -128),
	Vector2(832, 736), Vector2(-640, 736), Vector2(-896, 256)])

var _player: CharacterBody2D
var _state: PlanetWorldState
var _generator: PlanetGenerator
var _chunks: Dictionary[Vector2i, TerrainChunk] = {}
var _pending: Array[Vector2i] = []
var _center := Vector2i(2147483647, 2147483647)
var _revision: int = -1
var _preparing: bool = false
var _machine_presenters: Dictionary[int, DeployedMachine] = {}
var _highlights: Node2D
var _construction_definition: MachineDefinition
var _effective_renderer: TerrainRenderer = TerrainRenderer.LEGACY
var _renderer_configured: bool = false
var _terrain_failure: Dictionary = {}
var _tint_image: Image
var _tint_texture: ImageTexture
var _tint_material: ShaderMaterial
var _tint_slots: int = 0
var _tint_dirty: bool = false
var _terrain_generation: int = 0
var _terrain_tokens: Dictionary[Vector2i, int] = {}
@onready var _terrain_presenter: IllustratedTerrainPresenter = $IllustratedTerrainPresenter


# Transition hook: input stays locked and first arrival stays behind the fade.
# Subsequent hatch visits already have the spawn neighborhood retained.
func prepare_for_arrival(player: CharacterBody2D, state: PlanetWorldState) -> void:
	_preparing = true
	_configure_terrain_renderer()
	_player = player
	_state = state
	if not _state.machines_changed.is_connected(_queue_machine_sync):
		_state.machines_changed.connect(_queue_machine_sync)
	_sync_machines()
	if _highlights == null:
		_highlights = Node2D.new()
		_highlights.z_index = -4
		add_child(_highlights)
	if _generator == null:
		var overlays: Array[Dictionary] = []
		for child in $AuthoredCrashSite.get_children():
			var polygon := child as Polygon2D
			if polygon != null:
				overlays.append({"polygon": polygon.polygon, "color": polygon.color, "feather": 256.0})
		var object_anchors := PackedVector2Array()
		for child in $GroundObjects.get_children():
			if child is StaticBody2D:
				object_anchors.append(child.position)
		_generator = PlanetGenerator.new(state.seed_value, overlays, protected_gameplay, object_anchors)
	_update_neighborhood()
	while not _pending.is_empty() and _terrain_failure.is_empty():
		_generate_budget()
		await get_tree().process_frame
	_preparing = false


func _process(_delta: float) -> void:
	if _preparing or not _terrain_failure.is_empty() or _state == null \
			or not is_instance_valid(_player) or not is_ancestor_of(_player):
		return
	_update_neighborhood()
	_generate_budget()


func _update_neighborhood() -> void:
	if not _terrain_failure.is_empty():
		return
	var center := WorldCoordinates.world_to_chunk(to_local(_player.global_position))
	if center == _center and _state.revision == _revision:
		return
	_center = center
	_revision = _state.revision
	var retained_radius := loading_radius + retention_margin
	for coordinate in _chunks.keys():
		if _distance(coordinate, center) > retained_radius:
			var chunk: TerrainChunk = _chunks[coordinate]
			if not _retire_illustrated_chunk(coordinate):
				return
			remove_child(chunk)
			chunk.queue_free()
			_chunks.erase(coordinate)
	# Replacing the queue discards stale requests after movement, bounding work.
	_pending.clear()
	# Keep old visuals until their replacement is ready, including retained chunks.
	for coordinate in _chunks:
		if _chunks[coordinate].state_revision != _revision:
			_pending.append(coordinate)
	for y in range(-loading_radius, loading_radius + 1):
		for x in range(-loading_radius, loading_radius + 1):
			var coordinate := center + Vector2i(x, y)
			if not _chunks.has(coordinate):
				_pending.append(coordinate)
	_pending.sort_custom(func(a: Vector2i, b: Vector2i) -> bool:
		return _distance(a, center) < _distance(b, center))
	_refresh_highlights()


func _generate_budget() -> void:
	if not _terrain_failure.is_empty():
		return
	if _pending.is_empty():
		_flush_terrain_tint()
		return
	for index in range(mini(chunks_per_frame, _pending.size())):
		var coordinate: Vector2i = _pending.pop_front()
		var chunk := TerrainChunk.new()
		chunk.configure(coordinate, _generator, _state, _effective_renderer == TerrainRenderer.LEGACY)
		chunk.z_index = -10
		if not _present_illustrated_chunk(coordinate):
			chunk.free()
			# Preserve the request and stop; never spin or silently discard failure.
			_pending.push_front(coordinate)
			break
		if _effective_renderer == TerrainRenderer.ILLUSTRATED:
			chunk.write_tint(_tint_image, _tint_slot(coordinate))
			_sync_tint_borders(coordinate)
			_tint_dirty = true
		if _chunks.has(coordinate):
			var previous: TerrainChunk = _chunks[coordinate]
			remove_child(previous)
			previous.queue_free()
		add_child(chunk)
		_chunks[coordinate] = chunk
	_flush_terrain_tint()
	_refresh_highlights()


func _configure_terrain_renderer() -> void:
	if not _terrain_failure.is_empty():
		return
	# Lock selection once. Cached exterior reattachment preserves tokens and data.
	if not _renderer_configured:
		_renderer_configured = true
		_effective_renderer = terrain_renderer
		if _effective_renderer == TerrainRenderer.ILLUSTRATED:
			var initialized := _terrain_presenter.initialize()
			if not initialized.ok:
				_stop_terrain(initialized)
				return
			# Modulo slots are unique throughout the square retention window.
			_tint_slots = 2 * (loading_radius + retention_margin) + 1
			var width := _tint_slots * TerrainChunk.VERTEX_WIDTH
			_tint_image = Image.create(width, width, false, Image.FORMAT_RGBAF)
			_tint_image.fill(Color.WHITE)
			_tint_texture = ImageTexture.create_from_image(_tint_image)
			_tint_material = ShaderMaterial.new()
			_tint_material.shader = load("res://scenes/world/illustrated_terrain_tint.gdshader") as Shader
			if _tint_material.shader == null:
				_stop_terrain({"ok": false, "code": &"shader", "message": "Missing production tint shader"})
				return
			_tint_material.set_shader_parameter("tint_field", _tint_texture)
			_tint_material.set_shader_parameter("slot_count", float(_tint_slots))
			var layer := _terrain_presenter.get_node("Terrain") as TileMapLayer
			layer.material = _tint_material
	if _tint_material != null:
		# Inverse columns keep sampling in exterior space after reattachment.
		var inverse := global_transform.affine_inverse()
		_tint_material.set_shader_parameter("exterior_x", inverse.x)
		_tint_material.set_shader_parameter("exterior_y", inverse.y)
		_tint_material.set_shader_parameter("exterior_origin", inverse.origin)


func terrain_failure() -> Dictionary:
	return _terrain_failure.duplicate(true)


func _stop_terrain(result: Dictionary) -> void:
	if _terrain_failure.is_empty():
		_terrain_failure = result.duplicate(true)
		push_warning("Exterior terrain stopped; restart after correcting input: " + str(result))


func _tint_slot(coordinate: Vector2i) -> Vector2i:
	return Vector2i(posmod(coordinate.x, _tint_slots), posmod(coordinate.y, _tint_slots)) \
		* TerrainChunk.VERTEX_WIDTH


func _flush_terrain_tint() -> void:
	if _tint_dirty:
		_tint_texture.update(_tint_image)
		_tint_dirty = false


func _sync_tint_borders(coordinate: Vector2i) -> void:
	# Refresh duplicate shared vertices even while adjacent revision replacements
	# are still pending. No neighbor sampling or terrain assignment changes.
	var bounds := Rect2i(coordinate * WorldCoordinates.CHUNK_TILES,
		Vector2i.ONE * TerrainChunk.VERTEX_WIDTH)
	for y in range(-1, 2):
		for x in range(-1, 2):
			var neighbor := coordinate + Vector2i(x, y)
			if neighbor == coordinate or not _chunks.has(neighbor):
				continue
			var neighbor_origin := neighbor * WorldCoordinates.CHUNK_TILES
			var shared := bounds.intersection(Rect2i(neighbor_origin,
				Vector2i.ONE * TerrainChunk.VERTEX_WIDTH))
			var source := Rect2i(_tint_slot(coordinate) + shared.position - bounds.position, shared.size)
			_tint_image.blit_rect(_tint_image, source,
				_tint_slot(neighbor) + shared.position - neighbor_origin)


func _present_illustrated_chunk(coordinate: Vector2i) -> bool:
	if _effective_renderer != TerrainRenderer.ILLUSTRATED:
		return true
	_terrain_generation += 1
	var token := _terrain_generation
	var registered := _terrain_presenter.begin_generation(coordinate, token)
	if not registered.ok:
		_stop_terrain(registered)
		return false
	_terrain_tokens[coordinate] = token
	var result := _terrain_presenter.present_chunk(coordinate, token,
		Callable(_generator, "sample_ground_material"), _state.seed_value, TerrainResolver.RULE_VERSION)
	if not result.ok:
		_stop_terrain(result)
	return result.ok


func _retire_illustrated_chunk(coordinate: Vector2i) -> bool:
	if _effective_renderer != TerrainRenderer.ILLUSTRATED:
		return true
	if not _terrain_tokens.has(coordinate):
		return true
	var result := _terrain_presenter.retire_chunk(coordinate, _terrain_tokens[coordinate])
	if result.ok:
		_terrain_tokens.erase(coordinate)
		_tint_image.fill_rect(Rect2i(_tint_slot(coordinate),
			Vector2i.ONE * TerrainChunk.VERTEX_WIDTH), Color.WHITE)
		_tint_dirty = true
	else:
		_stop_terrain(result)
	return result.ok


func _queue_machine_sync() -> void:
	# Machine transactions can originate during physics; mutate bodies deferred.
	_sync_machines.call_deferred()


func _sync_machines() -> void:
	if not is_inside_tree() or _state == null:
		return
	var retained: Array[int] = []
	for machine in _state.get_machines():
		var machine_id: int = machine.id
		retained.append(machine_id)
		if not _machine_presenters.has(machine_id):
			var presenter := DeployedMachine.new()
			presenter.configure(machine, _state)
			$GroundObjects.add_child(presenter)
			_machine_presenters[machine_id] = presenter
	for machine_id in _machine_presenters.keys():
		if not retained.has(machine_id):
			var presenter: DeployedMachine = _machine_presenters[machine_id]
			presenter.get_parent().remove_child(presenter)
			presenter.queue_free()
			_machine_presenters.erase(machine_id)


func set_construction_definition(definition: MachineDefinition) -> void:
	_construction_definition = definition
	_refresh_highlights()


func _refresh_highlights() -> void:
	if _highlights == null:
		return
	for child in _highlights.get_children():
		_highlights.remove_child(child)
		child.queue_free()
	if _construction_definition == null or _state == null:
		return
	for deposit in _state.get_deposits():
		if not _construction_definition.compatible_resources.has(deposit.resource_type):
			continue
		for coordinate in _chunks:
			var start := Vector2(coordinate) * WorldCoordinates.CHUNK_SIZE
			var end := start + Vector2.ONE * WorldCoordinates.CHUNK_SIZE
			var boundary := PackedVector2Array([start, Vector2(end.x, start.y), end,
				Vector2(start.x, end.y)])
			# Exact mineral geometry clipped to loaded presentation, never its bounds.
			for polygon in Geometry2D.intersect_polygons(deposit.footprint, boundary):
				var highlight := Polygon2D.new()
				highlight.polygon = polygon
				highlight.color = deposit.construction_highlight
				_highlights.add_child(highlight)


func _distance(a: Vector2i, b: Vector2i) -> int:
	return maxi(absi(a.x - b.x), absi(a.y - b.y))
