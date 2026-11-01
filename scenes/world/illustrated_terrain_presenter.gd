class_name IllustratedTerrainPresenter
extends Node2D

# Explicit opt-in only: constructing/attaching this node performs no terrain work.
const OFFSETS := [Vector2i.ZERO, Vector2i(-1, -1), Vector2i(0, -1), Vector2i(1, -1),
	Vector2i(-1, 0), Vector2i(1, 0), Vector2i(-1, 1), Vector2i(0, 1), Vector2i(1, 1)]
const WIDTH: int = WorldCoordinates.CHUNK_TILES
const MAX_CHUNK: int = 67108862 # Leave room for the halo in Vector2i coordinates.

var _terrain: TileMapLayer
var _lookup: TerrainAssignmentLookup
var _active: Dictionary[Vector2i, Dictionary] = {}
var _high_water: int = 0
var _busy: bool = false


func initialize() -> Dictionary:
	if _busy:
		return _result(false, &"busy", Vector2i.ZERO, 0, "Operation in progress")
	if _lookup != null:
		return _result(true, &"ready", Vector2i.ZERO, 0, "Already initialized")
	var layer := get_node_or_null("Terrain") as TileMapLayer
	if layer == null or layer.position != Vector2.ZERO or layer.scale != Vector2.ONE * 0.5:
		return _result(false, &"layer", Vector2i.ZERO, 0, "Expected origin-aligned half-scale Terrain child")
	var lookup := TerrainAssignmentLookup.new()
	if not lookup.initialize():
		return _result(false, &"lookup", Vector2i.ZERO, 0, lookup.error)
	var tiles := load(TerrainAssignmentLookup.TILESET_PATH) as TileSet
	if tiles == null or tiles.tile_size != Vector2i(128, 128):
		return _result(false, &"tileset", Vector2i.ZERO, 0, "Expected approved 128-unit TileSet")
	layer.tile_set = tiles
	_terrain = layer
	_lookup = lookup
	return _result(true, &"ready", Vector2i.ZERO, 0, "Initialized")


func begin_generation(coordinate: Vector2i, generation_token: int) -> Dictionary:
	var guard := _guard(coordinate, generation_token)
	if not guard.ok:
		return guard
	if generation_token <= _high_water:
		return _result(false, &"stale", coordinate, generation_token, "Registration must exceed high-water mark")
	_high_water = generation_token
	# Never erase displayed terrain here, even when replacing a failed generation.
	_active[coordinate] = {"token": generation_token, "presented": false}
	return _result(true, &"registered", coordinate, generation_token, "Generation registered")


func present_chunk(coordinate: Vector2i, generation_token: int,
		material_sampler: Callable, presentation_seed: int, rule_version: int) -> Dictionary:
	var guard := _current(coordinate, generation_token, true)
	if not guard.ok:
		return guard
	if not material_sampler.is_valid() or rule_version != TerrainResolver.RULE_VERSION:
		return _result(false, &"input", coordinate, generation_token, "Invalid sampler or unsupported rule version")
	_busy = true
	var prepared := _prepare(coordinate, generation_token, material_sampler, presentation_seed, rule_version)
	if not prepared.ok:
		_busy = false
		return prepared
	var validated := _validate_assignments(coordinate, generation_token, prepared.assignments)
	if not validated.ok:
		_busy = false
		return validated
	# Samplers are external code. Recheck authority after preparation, before writes.
	if not _matches(coordinate, generation_token) or _active[coordinate].presented:
		_busy = false
		return _result(false, &"stale", coordinate, generation_token, "Generation changed during preparation")
	var origin := coordinate * WIDTH
	for y in range(WIDTH):
		for x in range(WIDTH):
			var cell := origin + Vector2i(x, y)
			var assignment: Dictionary = prepared.assignments[cell]
			_terrain.set_cell(cell, assignment.source_id, assignment.atlas_coords, assignment.alternative_id)
	_active[coordinate].presented = true
	_busy = false
	return _result(true, &"presented", coordinate, generation_token, "Complete region presented")


func retire_chunk(coordinate: Vector2i, generation_token: int) -> Dictionary:
	var guard := _current(coordinate, generation_token, false)
	if not guard.ok:
		return guard
	_busy = true
	var origin := coordinate * WIDTH
	for y in range(WIDTH):
		for x in range(WIDTH):
			_terrain.erase_cell(origin + Vector2i(x, y))
	_active.erase(coordinate)
	_busy = false
	return _result(true, &"retired", coordinate, generation_token, "Owned region retired")


func _prepare(coordinate: Vector2i, token: int, sampler: Callable,
		seed_value: int, rule_version: int) -> Dictionary:
	var origin := coordinate * WIDTH
	var halo: Dictionary = {}
	for y in range(-1, WIDTH + 1):
		for x in range(-1, WIDTH + 1):
			var cell := origin + Vector2i(x, y)
			var sample: Variant = sampler.call(cell)
			if not sample is int or sample < 0 or sample > 4:
				return _cell_failure(&"material", coordinate, token, cell, "Expected integer material 0..4")
			halo[cell] = sample
	var assignments: Dictionary = {}
	for y in range(WIDTH):
		for x in range(WIDTH):
			var cell := origin + Vector2i(x, y)
			var samples := PackedInt32Array()
			for offset in OFFSETS:
				samples.append(halo[cell + offset])
			var assignment := TerrainResolver.resolve(cell, samples, _lookup, seed_value, rule_version)
			if assignment.is_empty():
				return _cell_failure(&"resolve", coordinate, token, cell, "Resolver returned no assignment")
			assignments[cell] = assignment
	return {"ok": true, "assignments": assignments}


# Private validation seam: no public assignment-injection API.
func _validate_assignments(coordinate: Vector2i, token: int, assignments: Dictionary) -> Dictionary:
	if assignments.size() != WIDTH * WIDTH:
		return _result(false, &"coverage", coordinate, token, "Expected 1024 assignments")
	var origin := coordinate * WIDTH
	for y in range(WIDTH):
		for x in range(WIDTH):
			var cell := origin + Vector2i(x, y)
			var value: Variant = assignments.get(cell)
			if not value is Dictionary:
				return _cell_failure(&"assignment", coordinate, token, cell, "Missing owned assignment")
			var record: Dictionary = value
			if not record.get("source_id") is int or not record.get("atlas_coords") is Vector2i \
					or not record.get("alternative_id") is int or not record.get("signature") is PackedInt32Array \
					or not record.get("variant") is String:
				return _cell_failure(&"assignment", coordinate, token, cell, "Malformed assignment fields")
			if record.signature.size() != 9 or record.variant not in ["A", "B", "C"]:
				return _cell_failure(&"assignment", coordinate, token, cell, "Invalid signature or variant")
			if record.variant != "A":
				for terrain_id in record.signature:
					if terrain_id != record.signature[0]:
						return _cell_failure(&"assignment", coordinate, token, cell, "Variant requires solid interior")
			for terrain_id in record.signature:
				if terrain_id != 0 and terrain_id != 1:
					return _cell_failure(&"assignment", coordinate, token, cell, "Invalid terrain ID")
			var tiles := _terrain.tile_set
			if not tiles.has_source(record.source_id):
				return _cell_failure(&"assignment", coordinate, token, cell, "Unknown source")
			var source := tiles.get_source(record.source_id) as TileSetAtlasSource
			if source == null or not source.has_tile(record.atlas_coords) \
					or not source.has_alternative_tile(record.atlas_coords, record.alternative_id):
				return _cell_failure(&"assignment", coordinate, token, cell, "Unknown atlas or alternative")
			var data := source.get_tile_data(record.atlas_coords, record.alternative_id)
			if data == null or data.terrain_set != 0:
				return _cell_failure(&"assignment", coordinate, token, cell, "Missing native terrain data")
			var signature := PackedInt32Array([data.terrain])
			for peer in TerrainAssignmentLookup.PEERS:
				signature.append(data.get_terrain_peering_bit(peer))
			if signature != record.signature:
				return _cell_failure(&"assignment", coordinate, token, cell, "Native signature mismatch")
			var expected := _lookup.assignment(signature, record.variant)
			if expected.is_empty() or expected != record:
				return _cell_failure(&"assignment", coordinate, token, cell, "Lookup assignment mismatch")
	return _result(true, &"validated", coordinate, token, "Complete assignments validated")


func _guard(coordinate: Vector2i, token: int) -> Dictionary:
	if _busy:
		return _result(false, &"busy", coordinate, token, "Operation in progress")
	if _lookup == null or not is_instance_valid(_terrain):
		return _result(false, &"uninitialized", coordinate, token, "Initialize presenter first")
	if token <= 0 or absi(coordinate.x) > MAX_CHUNK or absi(coordinate.y) > MAX_CHUNK:
		return _result(false, &"input", coordinate, token, "Invalid token or coordinate range")
	return _result(true, &"valid", coordinate, token, "Valid request")


func _current(coordinate: Vector2i, token: int, presentation: bool) -> Dictionary:
	var guard := _guard(coordinate, token)
	if not guard.ok:
		return guard
	if not _matches(coordinate, token):
		return _result(false, &"stale", coordinate, token, "No matching active generation")
	if presentation and _active[coordinate].presented:
		return _result(false, &"duplicate", coordinate, token, "Generation already presented")
	return guard


func _matches(coordinate: Vector2i, token: int) -> bool:
	return _active.has(coordinate) and _active[coordinate].token == token


func _result(ok: bool, code: StringName, coordinate: Vector2i, token: int, message: String) -> Dictionary:
	return {"ok": ok, "code": code, "chunk": coordinate, "token": token, "message": message}


func _cell_failure(code: StringName, coordinate: Vector2i, token: int,
		cell: Vector2i, message: String) -> Dictionary:
	var result := _result(false, code, coordinate, token, message)
	result["cell"] = cell
	return result
