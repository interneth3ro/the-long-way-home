class_name PlanetExterior
extends Node2D

enum TerrainRenderer { LEGACY, ILLUSTRATED, CONTINUOUS }
@export var terrain_renderer: TerrainRenderer = TerrainRenderer.CONTINUOUS

@export_range(1, 4, 1) var loading_radius: int = 2
@export_range(1, 2, 1) var retention_margin: int = 1
@export_range(1, 8, 1) var chunks_per_frame: int = 2
# Independent of visual scar polygons: ship, approach and initial factory/Ferrite clearing.
@export var protected_gameplay := PackedVector2Array(CrashSiteProtection.GAMEPLAY)

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
var _ferrite_presenter: FerriteDepositPresenter
var _ferrite_token: int = 0
var _arrival_generation: int = 0
var _arrival_cancelled: bool = false
var _highlights_dirty: bool = false
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
var _ground_receipts: Dictionary[Vector2i, Dictionary] = {}
var _ground_state: PlanetWorldState
var _ground_seed: int
var _continuous_presenter: ContinuousTerrainPresenter
var _continuous_job: Dictionary = {}
@onready var _terrain_presenter: IllustratedTerrainPresenter = $IllustratedTerrainPresenter


# Transition hook: input stays locked and first arrival stays behind the fade.
# Subsequent hatch visits already have the spawn neighborhood retained.
func prepare_for_arrival(player: CharacterBody2D, state: PlanetWorldState) -> Dictionary:
	$GroundObjects/Hatch.prepare_for_arrival()
	_cancel_continuous()
	_arrival_generation += 1
	var arrival := _arrival_generation
	_arrival_cancelled = false
	_preparing = true
	_configure_terrain_renderer()
	_player = player
	_state = state
	var arrival_seed := state.seed_value
	var arrival_revision := state.revision
	if _ferrite_presenter == null:
		_ferrite_presenter = FerriteDepositPresenter.new()
		_ferrite_presenter.z_index = -5
		add_child(_ferrite_presenter)
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
		_ground_state = state
		_ground_seed = state.seed_value
	_update_neighborhood()
	while (not _pending.is_empty() or not _ferrite_presenter.required_ready(_ferrite_token)) \
			and _terrain_failure.is_empty() and arrival == _arrival_generation:
		if not is_inside_tree() or not is_instance_valid(player) or not is_ancestor_of(player) \
				or _state != state or state.seed_value != arrival_seed or state.revision != arrival_revision:
			break
		if not _service_ferrite(true):
			break
		_generate_budget()
		_flush_highlights()
		await get_tree().process_frame
	# An old await must not change flags belonging to a newer preparation.
	if arrival != _arrival_generation:
		return {"ok": false, "cancelled": true}
	_preparing = false
	if not _terrain_failure.is_empty():
		return {"ok": false, "cancelled": false}
	if _state != state or state.seed_value != arrival_seed or state.revision != arrival_revision:
		return {"ok": false, "cancelled": true}
	var result := {"ok": true, "generation": arrival, "ferrite_token": _ferrite_token,
		"state": state, "player": player, "seed": arrival_seed, "revision": arrival_revision,
		"ground_center": _center, "ground_radius": loading_radius}
	if not _required_ground_is_current():
		_stop_terrain({"ok": false, "code": &"ground_publication",
			"message": "Required arrival ground lacks current attached publication",
			"center": _center, "radius": loading_radius})
		return {"ok": false, "cancelled": false}
	if not arrival_is_ready(result):
		return {"ok": false, "cancelled": true}
	return result


# Rechecked by the controller after its own physics/fade awaits, not just when
# preparation returns. A detached/replaced/cancelled receipt can never authorize input.
func arrival_is_ready(result: Variant) -> bool:
	return result is Dictionary and result.get("ok", false) \
		and result.get("generation", -1) == _arrival_generation \
		and result.get("state") == _state and result.get("player") == _player \
		and _state != null and result.get("seed") == _state.seed_value \
		and result.get("revision") == _state.revision \
		and result.get("ground_center") == _center and result.get("ground_radius") == loading_radius \
		and _required_ground_is_current() \
		and result.get("ferrite_token", -1) == _ferrite_token \
		and is_inside_tree() and is_instance_valid(_player) and is_ancestor_of(_player) \
		and not _preparing and not _arrival_cancelled and _terrain_failure.is_empty() \
		and _pending.is_empty() and _ferrite_presenter != null \
		and _ferrite_presenter.matches_context(_state) \
		and _ferrite_presenter.required_ready(_ferrite_token) \
		and _center == WorldCoordinates.world_to_chunk(to_local(_player.global_position))


func cancel_arrival_preparation() -> void:
	_arrival_generation += 1
	_arrival_cancelled = true
	_preparing = false
	if _ferrite_presenter != null:
		_ferrite_presenter.cancel()
	_cancel_continuous()
	_clear_highlights()


func _exit_tree() -> void:
	# Children cancel their own work on exit. Do not mutate the exiting tree.
	if not _continuous_job.is_empty() and not _chunks.has(_continuous_job.coordinate):
		_terrain_tokens.erase(_continuous_job.coordinate)
	_continuous_job = {}
	_arrival_generation += 1
	_arrival_cancelled = true
	_preparing = false


func _process(_delta: float) -> void:
	if _preparing or _arrival_cancelled or not _terrain_failure.is_empty() or _state == null \
			or not is_instance_valid(_player) or not is_ancestor_of(_player):
		return
	_update_neighborhood()
	_service_ferrite()
	_generate_budget()
	_flush_highlights()


func _update_neighborhood() -> void:
	if not _terrain_failure.is_empty():
		return
	if _ground_state != _state or _ground_seed != _state.seed_value:
		# A cached exterior belongs to one playthrough/world. Never relabel its
		# generator, details or retained surfaces as a different world's output.
		_stop_terrain({"ok": false, "code": &"ground_context",
			"message": "Cached exterior world/seed changed; create a fresh exterior"})
		return
	var center := WorldCoordinates.world_to_chunk(to_local(_player.global_position))
	if center == _center and _state.revision == _revision \
			and _ferrite_presenter.matches_context(_state):
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
	_cancel_continuous()
	# Replacing the queue discards stale requests after movement, bounding work.
	_pending.clear()
	# Keep old visuals until their replacement is ready, including retained chunks.
	for coordinate in _chunks:
		if _chunks[coordinate].state_revision != _revision or not _ground_is_current(coordinate):
			_pending.append(coordinate)
	for y in range(-loading_radius, loading_radius + 1):
		for x in range(-loading_radius, loading_radius + 1):
			var coordinate := center + Vector2i(x, y)
			if not _chunks.has(coordinate):
				_pending.append(coordinate)
	_pending.sort_custom(func(a: Vector2i, b: Vector2i) -> bool:
		return _distance(a, center) < _distance(b, center))
	var presented := _ferrite_presenter.request(_state, _retained_presentation_area())
	if not presented.ok:
		_stop_terrain(presented)
		push_error("Exterior Ferrite presentation blocked: " + str(presented))
		get_tree().paused = true
		return
	_ferrite_token = presented.token
	_highlights_dirty = true


func _service_ferrite(required_only: bool = false) -> bool:
	if not _terrain_failure.is_empty():
		return false
	var presented := _ferrite_presenter.step(_state, _ferrite_token, required_only)
	if not presented.ok:
		_stop_terrain(presented)
		push_error("Exterior Ferrite preparation blocked: " + str(presented))
		get_tree().paused = true
		return false
	elif presented.changed:
		_highlights_dirty = true
	return not presented.get("stale", false)


func _generate_budget() -> void:
	if not _terrain_failure.is_empty():
		return
	if _pending.is_empty():
		_flush_terrain_tint()
		return
	if _effective_renderer == TerrainRenderer.CONTINUOUS:
		if not _step_continuous():
			return
	var committed: Array[Vector2i] = []
	var budget := 1 if _effective_renderer == TerrainRenderer.CONTINUOUS else chunks_per_frame
	for index in range(mini(budget, _pending.size())):
		var coordinate: Vector2i = _pending.pop_front()
		var chunk := TerrainChunk.new()
		chunk.configure(coordinate, _generator, _state, _effective_renderer == TerrainRenderer.LEGACY)
		chunk.z_index = -10
		if not _present_illustrated_chunk(coordinate):
			chunk.free()
			# Preserve the request and stop; never spin or silently discard failure.
			_pending.push_front(coordinate)
			break
		if _effective_renderer != TerrainRenderer.LEGACY:
			chunk.write_tint(_tint_image, _tint_slot(coordinate))
			_sync_tint_borders(coordinate)
			_tint_dirty = true
		if _chunks.has(coordinate):
			var previous: TerrainChunk = _chunks[coordinate]
			remove_child(previous)
			previous.queue_free()
		add_child(chunk)
		_chunks[coordinate] = chunk
		committed.append(coordinate)
	_flush_terrain_tint()
	# Publication authority includes attached details and the flushed tint, not
	# just successful TileMap writes. This commit boundary is synchronous.
	if _effective_renderer != TerrainRenderer.LEGACY:
		for coordinate in committed:
			_ground_receipts[coordinate] = {"publication": _ground_publication(
				coordinate, _terrain_tokens[coordinate]), "state": _state,
				"seed": _state.seed_value, "revision": _state.revision,
				"generator": _generator.get_instance_id(), "chunk": _chunks[coordinate].get_instance_id()}
	_highlights_dirty = true


func _ground_is_current(coordinate: Vector2i) -> bool:
	if _effective_renderer == TerrainRenderer.LEGACY:
		return true # Preserve the explicit legacy fallback's existing contract.
	if _state == null or _ground_state != _state or _ground_seed != _state.seed_value \
			or not is_instance_valid(_generator) or not is_instance_valid(_terrain_presenter) \
			or not is_ancestor_of(_terrain_presenter) or not _ground_receipts.has(coordinate) \
			or not _terrain_tokens.has(coordinate) or not _chunks.has(coordinate):
		return false
	var chunk: TerrainChunk = _chunks[coordinate]
	var receipt: Dictionary = _ground_receipts[coordinate]
	return is_instance_valid(chunk) and chunk.is_inside_tree() and chunk.get_parent() == self \
		and chunk.state_revision == _state.revision and receipt.get("state") == _state \
		and receipt.get("seed") == _state.seed_value and receipt.get("revision") == _state.revision \
		and receipt.get("generator") == _generator.get_instance_id() \
		and receipt.get("chunk") == chunk.get_instance_id() \
		and not receipt.get("publication", {}).is_empty() \
		and receipt.publication == _ground_publication(coordinate, _terrain_tokens[coordinate])


func _required_ground_is_current() -> bool:
	if not is_inside_tree() or _tint_dirty:
		return false
	# Match the existing loading square, excluding the optional retention margin.
	for y in range(-loading_radius, loading_radius + 1):
		for x in range(-loading_radius, loading_radius + 1):
			if not _ground_is_current(_center + Vector2i(x, y)):
				return false
	return true


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
		if _effective_renderer != TerrainRenderer.LEGACY:
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
			if _effective_renderer == TerrainRenderer.ILLUSTRATED:
				layer.material = _tint_material
			else:
				_continuous_presenter = ContinuousTerrainPresenter.new()
				_continuous_presenter.z_index = -11
				add_child(_continuous_presenter)
				var initialized := _continuous_presenter.initialize(_tint_texture, _tint_slots)
				if not initialized.ok:
					_stop_terrain(initialized)
					return
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
		_cancel_continuous()
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
	_ground_receipts.erase(coordinate)
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
	if _effective_renderer == TerrainRenderer.LEGACY:
		return true
	if not _terrain_tokens.has(coordinate):
		return true
	var result := _continuous_presenter.retire_chunk(coordinate, _terrain_tokens[coordinate]) \
		if _effective_renderer == TerrainRenderer.CONTINUOUS else \
		_terrain_presenter.retire_chunk(coordinate, _terrain_tokens[coordinate])
	if result.ok:
		_terrain_tokens.erase(coordinate)
		_ground_receipts.erase(coordinate)
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
	_clear_highlights()
	_highlights_dirty = definition != null


# Planet-local square, independent of which terrain requests have completed.
func _retained_presentation_area() -> Rect2:
	var radius := loading_radius + retention_margin
	return Rect2(Vector2(_center - Vector2i.ONE * radius) * WorldCoordinates.CHUNK_SIZE,
		Vector2.ONE * (2 * radius + 1) * WorldCoordinates.CHUNK_SIZE)


func _clear_highlights() -> void:
	if _highlights == null:
		return
	for child in _highlights.get_children():
		_highlights.remove_child(child)
		child.queue_free()


func _flush_highlights() -> void:
	if _highlights_dirty and _ferrite_presenter.required_ready(_ferrite_token):
		_highlights_dirty = false
		_refresh_highlights()


func _refresh_highlights() -> void:
	_clear_highlights()
	if _construction_definition == null or _state == null or _chunks.is_empty():
		return
	for deposit in _ferrite_presenter.highlight_deposits(_state, _ferrite_token):
		if not _construction_definition.compatible_resources.has(deposit.resource_type):
			continue
		var bounds := FerriteRegionGenerator._bounds(deposit.footprint)
		var first := WorldCoordinates.world_to_chunk(bounds.position)
		var last := WorldCoordinates.world_to_chunk(bounds.end)
		# Visit footprint chunk candidates only, never explored deposits x chunks.
		for y in range(first.y, last.y + 1):
			for x in range(first.x, last.x + 1):
				var coordinate := Vector2i(x, y)
				if not _chunks.has(coordinate):
					continue
				var start := Vector2(coordinate) * WorldCoordinates.CHUNK_SIZE
				var end := start + Vector2.ONE * WorldCoordinates.CHUNK_SIZE
				var boundary := PackedVector2Array([start, Vector2(end.x, start.y), end,
					Vector2(start.x, end.y)])
				# All pieces of the actual concave footprint; decorative rims stay empty.
				for polygon in Geometry2D.intersect_polygons(deposit.footprint, boundary):
					var highlight := Polygon2D.new()
					highlight.polygon = polygon
					highlight.color = deposit.construction_highlight
					_highlights.add_child(highlight)


func _distance(a: Vector2i, b: Vector2i) -> int:
	return maxi(absi(a.x - b.x), absi(a.y - b.y))


func _ground_publication(coordinate: Vector2i, token: int) -> Dictionary:
	if _effective_renderer == TerrainRenderer.CONTINUOUS:
		if not is_instance_valid(_continuous_presenter) or not is_ancestor_of(_continuous_presenter):
			return {}
		return _continuous_presenter.publication(coordinate, token)
	return _terrain_presenter.publication(coordinate, token)


func _cancel_continuous() -> void:
	if not _continuous_job.is_empty() and not _chunks.has(_continuous_job.coordinate):
		_terrain_tokens.erase(_continuous_job.coordinate)
	if is_instance_valid(_continuous_presenter):
		_continuous_presenter.cancel()
	_continuous_job = {}


func _step_continuous() -> bool:
	var coordinate: Vector2i = _pending[0]
	if _continuous_job.is_empty():
		_terrain_generation += 1
		var token := _terrain_generation
		_ground_receipts.erase(coordinate)
		var registered := _continuous_presenter.begin_generation(coordinate, token, _state.seed_value)
		if not registered.ok:
			_stop_terrain(registered)
			return false
		_terrain_tokens[coordinate] = token
		_continuous_job = {"coordinate": coordinate, "token": token, "revision": _state.revision,
			"state": _state, "seed": _state.seed_value, "arrival": _arrival_generation}
	if _continuous_job.coordinate != coordinate or _continuous_job.state != _state \
			or _continuous_job.revision != _state.revision or _continuous_job.seed != _state.seed_value \
			or _continuous_job.arrival != _arrival_generation or _arrival_cancelled:
		_cancel_continuous()
		return false
	var result := _continuous_presenter.step(coordinate, _continuous_job.token,
		Callable(_generator, "sample_ground_material"))
	if not result.ok:
		_stop_terrain(result)
		return false
	if result.pending:
		return false
	_continuous_job = {}
	return true
