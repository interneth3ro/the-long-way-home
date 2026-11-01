extends SceneTree

# Proposed Gate 2 only. Never run under the standing Native exception.
var failures: int = 0


class MalformedPresenter extends IllustratedTerrainPresenter:
	var malformed: bool = false

	func _prepare(coordinate: Vector2i, token: int, sampler: Callable,
			seed_value: int, rule_version: int) -> Dictionary:
		var result := super._prepare(coordinate, token, sampler, seed_value, rule_version)
		if malformed and result.ok:
			result.assignments[coordinate * WIDTH]["alternative_id"] = 999
		return result


func _initialize() -> void:
	call_deferred("_validate")


func _check(condition: bool, message: String) -> void:
	if not condition:
		failures += 1
		push_error(message)


func _validate() -> void:
	var packed: PackedScene = load("res://scenes/experiments/production_terrain/fixture.tscn")
	var fixture := packed.instantiate()
	root.add_child(fixture)
	await process_frame
	var layer: TileMapLayer = fixture.get_node("Terrain")
	_check(fixture._lookup.error.is_empty(), "Native lookup initialization failed")
	if not fixture._lookup.error.is_empty():
		print("Production terrain fixture failures: %d" % failures)
		quit(1)
		return
	_check(layer.get_used_cells().size() == 4096, "Initial cell count")
	var snapshot: Dictionary = fixture._loaded.duplicate(true)
	fixture._reload(true)
	_check(snapshot == fixture._loaded, "Order-independent assignments")
	fixture._load_chunk(Vector2i(-1, -1))
	_check(snapshot == fixture._loaded, "Replacement assignments")
	fixture._unload_chunk(Vector2i(-1, -1))
	_check(layer.get_used_cells().size() == 3072, "Retirement count")
	for cell in snapshot[Vector2i(-1, -1)]:
		_check(layer.get_cell_source_id(cell) == -1, "Stale retired cell")
	fixture._load_chunk(Vector2i(-1, -1))
	_check(snapshot == fixture._loaded, "Reload assignments")
	for chunk in snapshot.values():
		for cell in chunk:
			var assignment: Dictionary = chunk[cell]
			_check(layer.get_cell_source_id(cell) == assignment.source_id, "Source ID")
			_check(layer.get_cell_atlas_coords(cell) == assignment.atlas_coords, "Atlas coordinates")
			_check(layer.get_cell_alternative_tile(cell) == assignment.alternative_id, "Alternative ID")
	for cell in [Vector2i(-33, -1), Vector2i(-1, 0), Vector2i.ZERO, Vector2i(31, 31)]:
		var center := layer.to_global(layer.map_to_local(cell))
		var expected := (Vector2(cell) + Vector2.ONE * 0.5) * 64.0
		_check(center.is_equal_approx(expected), "Scaled cell center / half-cell offset")
		_check(WorldCoordinates.world_to_terrain(center) == cell, "Floor coordinate roundtrip")
	fixture._set_shading(1)
	fixture._set_shading(2)
	await process_frame
	_check(fixture._tint_texture.get_size() == Vector2(65, 65), "Tint field size")
	_validate_presenter(fixture)
	fixture.queue_free()
	await process_frame
	print("Production terrain fixture failures: %d" % failures)
	quit(0 if failures == 0 else 1)


func _snapshot(layer: TileMapLayer) -> Dictionary:
	var result: Dictionary = {}
	for cell in layer.get_used_cells():
		result[cell] = [layer.get_cell_source_id(cell), layer.get_cell_atlas_coords(cell),
			layer.get_cell_alternative_tile(cell)]
	return result


func _validate_presenter(fixture: Variant) -> void:
	var reference := _snapshot(fixture.terrain)
	var tint: ImageTexture = fixture._tint_texture
	_check(not fixture._presenter_mode, "Reference default")
	_check(fixture.select_presenter_mode(true), "Presenter mode initialization")
	var presenter: IllustratedTerrainPresenter = fixture.presenter
	var layer: TileMapLayer = presenter.get_node("Terrain")
	_check(fixture.terrain.get_used_cells().is_empty(), "No competing reference ground")
	_check(_snapshot(layer) == reference, "Presenter matches accepted reference assignments")
	_check(fixture._reload_active(true), "Reversed presenter order")
	_check(_snapshot(layer) == reference, "Reversed presenter assignments")
	var coordinate := Vector2i(-1, -1)
	var old_token: int = fixture._presenter_tokens[coordinate]
	_check(fixture._load_active(coordinate), "In-place replacement")
	var new_token: int = fixture._presenter_tokens[coordinate]
	var sampler := Callable(fixture, "sample_material")
	_check(not presenter.retire_chunk(coordinate, old_token).ok, "Stale retirement rejected")
	_check(not presenter.present_chunk(coordinate, old_token, sampler, 19, 1).ok, "Stale presentation rejected")
	_check(not presenter.present_chunk(coordinate, new_token, sampler, 19, 1).ok, "Duplicate rejected")
	_check(_snapshot(layer) == reference, "Stale operations preserve all neighbors")
	_check(fixture._unload_active(coordinate), "Exact negative retirement")
	_check(layer.get_used_cells().size() == 3072, "Retirement count")
	for cell in reference:
		if Rect2i(coordinate * 32, Vector2i(32, 32)).has_point(cell):
			_check(layer.get_cell_source_id(cell) == -1, "Negative owned cell erased")
		else:
			_check(_snapshot_cell(layer, cell) == reference[cell], "Neighbor preserved")
	_check(not presenter.begin_generation(coordinate, new_token).ok, "Retired token cannot resurrect")
	_check(not presenter.present_chunk(coordinate, new_token, sampler, 19, 1).ok, "Retired presentation rejected")
	_check(fixture._load_active(coordinate), "Deterministic reload")
	_check(_snapshot(layer) == reference, "Regeneration snapshot")
	var pending_old: int = fixture._presenter_tokens[coordinate]
	fixture._generation += 1
	var failed_token: int = fixture._generation
	_check(presenter.begin_generation(coordinate, failed_token).ok, "Failed replacement registration")
	fixture._presenter_tokens[coordinate] = failed_token
	_check(not presenter.present_chunk(coordinate, pending_old, sampler, 19, 1).ok,
		"Delayed old presentation rejected while newer generation pending")
	var bad_material := presenter.present_chunk(coordinate, failed_token, func(_cell: Vector2i) -> int: return 5, 19, 1)
	_check(not bad_material.ok and bad_material.has("cell") and bad_material.chunk == coordinate,
		"Invalid material diagnostic")
	_check(not presenter.present_chunk(coordinate, failed_token, sampler, 19, 999).ok, "Invalid version")
	_check(not presenter.present_chunk(coordinate, failed_token, Callable(), 19, 1).ok, "Invalid callable")
	_check(not presenter.present_chunk(coordinate, failed_token, func(_cell: Vector2i) -> float: return 1.0,
		19, 1).ok, "Noninteger material rejected")
	_check(_snapshot(layer) == reference, "Failed preparation preserves old pixels")
	var reentrant: Array[Dictionary] = []
	var guarded_sampler := func(cell: Vector2i) -> int:
		if reentrant.is_empty():
			reentrant.append(presenter.retire_chunk(coordinate, failed_token))
		return fixture.sample_material(cell)
	_check(presenter.present_chunk(coordinate, failed_token, guarded_sampler, 19, 1).ok, "Valid retry is explicit")
	_check(not reentrant[0].ok and reentrant[0].code == &"busy", "Reentrant mutation rejected")
	_check(_snapshot(layer) == reference, "Reentrant request cannot alter neighbors")
	for mode in [0, 1, 2]:
		fixture._set_shading(mode)
		_check(layer.material == fixture.terrain.material, "Same comparison material")
		_check(_snapshot(layer) == reference, "Shading never changes assignments")
	_check(fixture._tint_texture == tint, "Tint texture reused")
	for chunk in fixture.CHUNKS:
		_check(fixture._unload_active(chunk), "Presenter cleared before isolated malformed test")
	_check(fixture._load_active(Vector2i(-1, -1)), "Initial single region")
	_check(layer.get_used_cells().size() == 1024, "Initial 1024 cells")
	_check(fixture._load_active(Vector2i(0, -1)), "Adjacent region")
	_check(layer.get_used_cells().size() == 2048, "Adjacent 2048 cells")
	for chunk in fixture.CHUNKS:
		_check(fixture._unload_active(chunk), "Retire bounded regions")
	var malformed := MalformedPresenter.new()
	var malformed_layer := TileMapLayer.new()
	malformed_layer.name = "Terrain"
	malformed_layer.scale = Vector2.ONE * 0.5
	malformed_layer.collision_enabled = false
	malformed_layer.navigation_enabled = false
	malformed_layer.occlusion_enabled = false
	malformed.add_child(malformed_layer)
	fixture.add_child(malformed)
	_check(malformed.initialize().ok, "Malformed-test initialization")
	_check(malformed.begin_generation(coordinate, 1).ok, "Malformed-test registration")
	_check(malformed.present_chunk(coordinate, 1, sampler, 19, 1).ok, "Malformed-test baseline")
	var previous := _snapshot(malformed_layer)
	malformed.malformed = true
	_check(malformed.begin_generation(coordinate, 2).ok, "Malformed replacement registration")
	_check(not malformed.present_chunk(coordinate, 2, sampler, 19, 1).ok, "Invalid assignment rejected")
	_check(_snapshot(malformed_layer) == previous, "Invalid assignment preserves terrain")
	_check(malformed.retire_chunk(coordinate, 2).ok, "Retire after failed replacement")
	_check(malformed.begin_generation(coordinate, 3).ok, "Empty-region failure registration")
	_check(not malformed.present_chunk(coordinate, 3, sampler, 19, 1).ok, "Invalid initial assignment rejected")
	_check(malformed_layer.get_used_cells().is_empty(), "Invalid initial assignment leaves empty region")
	malformed.get_parent().remove_child(malformed)
	malformed.free()
	_check(fixture.select_presenter_mode(false), "Restore reference mode")
	_check(_snapshot(fixture.terrain) == reference, "Reference restored unchanged")
	_check(layer.get_used_cells().is_empty(), "No competing presenter ground")


func _snapshot_cell(layer: TileMapLayer, cell: Vector2i) -> Array:
	return [layer.get_cell_source_id(cell), layer.get_cell_atlas_coords(cell), layer.get_cell_alternative_tile(cell)]
