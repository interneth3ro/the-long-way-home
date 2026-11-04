class_name ContinuousTerrainPresenter
extends Node2D
## One caller-driven job. PlanetExterior owns scheduling, revision and readiness.
const SHADER = preload("res://scenes/world/continuous_terrain.gdshader")
const MAX_UNITS := 32768
const SLICE_USEC := 2000
var _earth: Texture2D
var _green: Texture2D
var _tint: ImageTexture
var _slots: int
var _active: Dictionary[Vector2i, Dictionary] = {}
var _job: Dictionary = {}
var _high_water := 0


func initialize(tint: ImageTexture, slots: int) -> Dictionary:
	_earth = load("res://assets/experiments/terrain_c1/sources/earth.png") as Texture2D
	_green = load("res://assets/experiments/terrain_c1/sources/green.png") as Texture2D
	if _earth == null or _green == null or _earth.get_size() != Vector2(1254, 1254) \
			or _green.get_size() != Vector2(1254, 1254) or tint == null or slots <= 0:
		return {"ok": false, "code": &"continuous_resources"}
	_tint = tint
	_slots = slots
	return {"ok": true}


func begin_generation(coordinate: Vector2i, token: int, seed_value: int) -> Dictionary:
	if _earth == null or token <= _high_water or not _job.is_empty() \
			or coordinate.x < -16 or coordinate.x > 15 or coordinate.y < -16 or coordinate.y > 15:
		return {"ok": false, "code": &"continuous_registration"}
	_high_water = token
	# Retain the previous visible surface until replacement publication.
	var previous: Variant = _active.get(coordinate, {}).get("surface")
	_active[coordinate] = {"token": token, "presented": false, "surface": previous}
	_job = {"coordinate": coordinate, "token": token, "seed": seed_value, "cursor": 0,
		"ids": PackedByteArray(), "field": PackedByteArray(), "phase": PackedByteArray()}
	_job.ids.resize(34 * 34)
	_job.field.resize(137 * 137 * 3)
	_job.phase.resize(7 * 7 * 3)
	return {"ok": true}


# No awaits/callback scheduling here: every slice requires exterior authority.
func step(coordinate: Vector2i, token: int, sampler: Callable) -> Dictionary:
	if _job.is_empty() or _job.coordinate != coordinate or _job.token != token \
			or not _active.has(coordinate) or _active[coordinate].token != token or not sampler.is_valid():
		return {"ok": false, "code": &"continuous_stale"}
	var deadline := Time.get_ticks_usec() + SLICE_USEC
	for unit in range(MAX_UNITS):
		var cursor: int = _job.cursor
		if cursor < 1156:
			# Integer quotient selects the row of this flattened grid.
			@warning_ignore("integer_division")
			var cell := coordinate * 32 + Vector2i(cursor % 34 - 1, cursor / 34 - 1)
			var id: Variant = sampler.call(cell)
			if not id is int or id < 0 or id > 4:
				return {"ok": false, "code": &"continuous_material"}
			_job.ids[cursor] = id
		elif cursor < 1156 + 18769:
			var index := cursor - 1156
			# Integer quotient selects the row of this flattened grid.
			@warning_ignore("integer_division")
			var point := Vector2(coordinate * 2048 + Vector2i(index % 137 - 4, index / 137 - 4) * 16)
			# C1 red protection/coverage is absent. Preserve only macro/detail G/B.
			_job.field[index * 3] = 0
			_job.field[index * 3 + 1] = roundi(255.0 * _noise(point / 1270.0, 102, _job.seed))
			_job.field[index * 3 + 2] = roundi(255.0 * _noise(point / 370.0, 103, _job.seed))
		elif cursor < 1156 + 18769 + 49:
			var index := cursor - 1156 - 18769
			# Integer quotient selects the row of this flattened grid.
			@warning_ignore("integer_division")
			var lattice := coordinate * 4 + Vector2i(index % 7 - 1, index / 7 - 1)
			var key := "c1_fields_v1:c1_materials_v1:%d:%d:%d:material" % [_job.seed, lattice.x, lattice.y]
			var digest := key.sha256_buffer()
			for channel in range(3):
				_job.phase[index * 3 + channel] = digest[channel]
		else:
			return _publish(coordinate, token)
		_job.cursor += 1
		if Time.get_ticks_usec() >= deadline:
			break
	return {"ok": true, "pending": true}


func _publish(coordinate: Vector2i, token: int) -> Dictionary:
	if not is_inside_tree() or not _active.has(coordinate) or _active[coordinate].token != token:
		return {"ok": false, "code": &"continuous_publication"}
	var shader_material := ShaderMaterial.new()
	shader_material.shader = SHADER
	for entry in [["material_ids", 34, Image.FORMAT_R8, _job.ids],
			["c1_field", 137, Image.FORMAT_RGB8, _job.field],
			["phase_field", 7, Image.FORMAT_RGB8, _job.phase]]:
		var image := Image.create_from_data(entry[1], entry[1], false, entry[2], entry[3])
		if image == null or image.is_empty():
			return {"ok": false, "code": &"continuous_image"}
		var texture := ImageTexture.create_from_image(image)
		if texture == null:
			return {"ok": false, "code": &"continuous_texture"}
		shader_material.set_shader_parameter(entry[0], texture)
	shader_material.set_shader_parameter("earth_art", _earth)
	shader_material.set_shader_parameter("green_art", _green)
	shader_material.set_shader_parameter("tint_field", _tint)
	shader_material.set_shader_parameter("slot_count", float(_slots))
	shader_material.set_shader_parameter("chunk_coordinate", Vector2(coordinate))
	var surface := Polygon2D.new()
	surface.position = Vector2(coordinate) * 2048.0
	surface.polygon = PackedVector2Array([Vector2.ZERO, Vector2(2048, 0), Vector2(2048, 2048), Vector2(0, 2048)])
	surface.material = shader_material
	add_child(surface)
	if not surface.is_visible_in_tree():
		remove_child(surface)
		surface.free()
		return {"ok": false, "code": &"continuous_attachment"}
	var previous: Variant = _active[coordinate].surface
	if is_instance_valid(previous):
		remove_child(previous)
		previous.queue_free()
	_active[coordinate] = {"token": token, "presented": true, "surface": surface,
		"materials": _job.ids, "seed": _job.seed}
	_job = {}
	return {"ok": true, "pending": false}


func cancel() -> void:
	if not _job.is_empty():
		# Retained pixels never count as publication for this generation.
		var coordinate: Vector2i = _job.coordinate
		_active[coordinate].presented = false
		if not is_instance_valid(_active[coordinate].surface):
			_active.erase(coordinate)
	_job = {}


func retire_chunk(coordinate: Vector2i, token: int) -> Dictionary:
	if not _active.has(coordinate) or _active[coordinate].token != token:
		return {"ok": false, "code": &"continuous_stale"}
	if not _job.is_empty() and _job.coordinate == coordinate:
		cancel()
	var surface: Variant = _active[coordinate].surface
	if is_instance_valid(surface):
		remove_child(surface)
		surface.queue_free()
	_active.erase(coordinate)
	return {"ok": true}


func publication(coordinate: Vector2i, token: int) -> Dictionary:
	if not is_inside_tree() or not _active.has(coordinate) or _active[coordinate].token != token \
			or not _active[coordinate].presented:
		return {}
	var surface: Polygon2D = _active[coordinate].surface
	if not is_instance_valid(surface) or surface.get_parent() != self or not surface.is_visible_in_tree():
		return {}
	return {"chunk": coordinate, "token": token, "presenter": get_instance_id(),
		"layer": surface.get_instance_id(), "seed": _active[coordinate].seed}


func _exit_tree() -> void:
	cancel()


static func _random(cell: Vector2i, channel: int, seed_value: int) -> float:
	var value := posmod(seed_value, 2147483647)
	value = posmod(value * 48271 + posmod(cell.x, 2147483647) * 69621, 2147483647)
	value = posmod(value * 48271 + posmod(cell.y, 2147483647) * 907, 2147483647)
	value = posmod(value * 48271 + channel * 104729, 2147483647)
	return float(posmod((value ^ (value >> 13)) * 48271, 2147483647)) / 2147483647.0


static func _noise(point: Vector2, channel: int, seed_value: int) -> float:
	var cell := Vector2i(floori(point.x), floori(point.y))
	var f := point - Vector2(cell)
	var w := f * f * (Vector2(3, 3) - 2.0 * f)
	return lerpf(lerpf(_random(cell, channel, seed_value), _random(cell + Vector2i.RIGHT, channel, seed_value), w.x),
		lerpf(_random(cell + Vector2i.DOWN, channel, seed_value), _random(cell + Vector2i.ONE, channel, seed_value), w.x), w.y)
