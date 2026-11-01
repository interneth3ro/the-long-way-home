extends SceneTree

# Proposed Gate 2 only. Never run under the standing Native exception.
var failures: int = 0


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
	fixture.queue_free()
	await process_frame
	print("Production terrain fixture failures: %d" % failures)
	quit(0 if failures == 0 else 1)
