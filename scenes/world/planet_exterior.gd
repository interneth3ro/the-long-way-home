extends Node2D

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


# Transition hook: input stays locked and first arrival stays behind the fade.
# Subsequent hatch visits already have the spawn neighborhood retained.
func prepare_for_arrival(player: CharacterBody2D, state: PlanetWorldState) -> void:
	_preparing = true
	_player = player
	_state = state
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
	while not _pending.is_empty():
		_generate_budget()
		await get_tree().process_frame
	_preparing = false


func _process(_delta: float) -> void:
	if _preparing or _state == null or not is_instance_valid(_player) or not is_ancestor_of(_player):
		return
	_update_neighborhood()
	_generate_budget()


func _update_neighborhood() -> void:
	var center := WorldCoordinates.world_to_chunk(to_local(_player.global_position))
	if center == _center and _state.revision == _revision:
		return
	_center = center
	_revision = _state.revision
	var retained_radius := loading_radius + retention_margin
	for coordinate in _chunks.keys():
		if _distance(coordinate, center) > retained_radius:
			var chunk: TerrainChunk = _chunks[coordinate]
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


func _generate_budget() -> void:
	for index in range(mini(chunks_per_frame, _pending.size())):
		var coordinate: Vector2i = _pending.pop_front()
		var chunk := TerrainChunk.new()
		chunk.configure(coordinate, _generator, _state)
		chunk.z_index = -10
		if _chunks.has(coordinate):
			var previous: TerrainChunk = _chunks[coordinate]
			remove_child(previous)
			previous.queue_free()
		add_child(chunk)
		_chunks[coordinate] = chunk


func _distance(a: Vector2i, b: Vector2i) -> int:
	return maxi(absi(a.x - b.x), absi(a.y - b.y))
