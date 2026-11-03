class_name FerriteDepositPresenter
extends Node2D

# Disposable bounded working set; mining never reads this presenter.
const QUERY_PAGE_SIZE: int = 4 * WorldCoordinates.CHUNK_SIZE
# 13x13 presentation + one chunk on every side: at most 12 owners per axis,
# including the unchanged asymmetric query reach. Not a generation-cache change.
const MAX_SNAPSHOT_REGIONS: int = 144
var _sprites: Dictionary[String, Sprite2D] = {}
var _envelopes: Dictionary[String, Rect2] = {}
var _textures: Dictionary[String, Texture2D] = {}
var _variants: Dictionary[String, Dictionary] = {}
var _regions: Dictionary[Vector2i, Array] = {}
var _footprints: Dictionary[String, ResourceDeposit] = {}
var _state: PlanetWorldState
var _seed: int
var _revision: int
var _token: int = 0
var _active: bool = false
var _area: Rect2
var _lookahead: Rect2
var _required_owners: Array[Vector2i] = []
var _future_owners: Array[Vector2i] = []
var _required_pending: Array[Vector2i] = []
var _future_pending: Array[Vector2i] = []
var _nearby: Dictionary = {}
var _registrations: Dictionary = {}
var _required_ids: Array = []
var _pending_ids: Array = []
var _future_ids: Array = []
var _future: Dictionary = {}
var _validate_index: int = 0
var _commit_index: int = 0
var _future_index: int = 0
var _collected: bool = false
var _future_collected: bool = false
var _required_complete: bool = false


static func query_areas(area: Rect2) -> Array[Rect2]:
	var result: Array[Rect2] = []
	for y in range(ceili(area.size.y / QUERY_PAGE_SIZE)):
		for x in range(ceili(area.size.x / QUERY_PAGE_SIZE)):
			var start := area.position + Vector2(x, y) * QUERY_PAGE_SIZE
			result.append(Rect2(start, Vector2(
				minf(QUERY_PAGE_SIZE, area.end.x - start.x),
				minf(QUERY_PAGE_SIZE, area.end.y - start.y))))
	return result


func matches_context(state: PlanetWorldState) -> bool:
	return _active and _state == state and _seed == state.seed_value and _revision == state.revision


# Cheap owner planning deduplicates page halos BEFORE any region generation.
func _owners(state: PlanetWorldState, area: Rect2) -> Array[Vector2i]:
	var unique: Dictionary[Vector2i, bool] = {}
	for page in query_areas(area):
		var owners := state.deposit_query_owners(page)
		if owners.is_empty():
			return []
		for owner in owners:
			unique[owner] = true
	var result: Array[Vector2i] = []
	result.assign(unique.keys())
	var center := FerriteRegionGenerator.owner_at(_area.get_center())
	result.sort_custom(func(a: Vector2i, b: Vector2i) -> bool:
		var da := maxi(absi(a.x - center.x), absi(a.y - center.y))
		var db := maxi(absi(b.x - center.x), absi(b.y - center.y))
		return da < db if da != db else (a.y < b.y if a.y != b.y else a.x < b.x))
	return result


func request(state: PlanetWorldState, area: Rect2) -> Dictionary:
	cancel()
	if not state.is_resource_generation_ready():
		return _failure(state.resource_generation_error())
	# Query pages and retained memory are bounded even for invalid callers.
	if not area.is_finite() or area.size.x <= 0 or area.size.y <= 0 \
			or area.size.x > 13 * WorldCoordinates.CHUNK_SIZE \
			or area.size.y > 13 * WorldCoordinates.CHUNK_SIZE:
		return _failure("Invalid Ferrite presentation area")
	if _state != state or _seed != state.seed_value or _revision != state.revision:
		_regions.clear()
		_footprints.clear()
	if _state != state or _seed != state.seed_value:
		_variants.clear()
		_textures.clear()
		_clear_sprites()
	_state = state
	_seed = state.seed_value
	_revision = state.revision
	_area = area
	_lookahead = area.grow(WorldCoordinates.CHUNK_SIZE)
	_required_owners = _owners(state, area)
	_future_owners = _owners(state, _lookahead)
	if _required_owners.is_empty() or _future_owners.is_empty() \
			or _future_owners.size() > MAX_SNAPSHOT_REGIONS:
		return _failure("Ferrite owner plan exceeds bounds")
	for owner in _regions.keys():
		if not _future_owners.has(owner):
			_regions.erase(owner)
	for owner in _required_owners:
		if not _regions.has(owner):
			_required_pending.append(owner)
	for owner in _future_owners:
		if not _regions.has(owner) and not _required_owners.has(owner):
			_future_pending.append(owner)
	# Retire only by complete illustrated envelope, without waiting for new work.
	for identity: String in _sprites.keys():
		if not area.intersects(_envelopes[identity], true):
			_remove_sprite(identity)
	_active = true
	return {"ok": true, "token": _token}


func required_ready(token: int) -> bool:
	return _active and token == _token and _required_complete


# One region, registration (possibly one load), or sprite per call. This is a
# work cap, NOT a millisecond guarantee. No coroutine can outlive its token.
func step(state: PlanetWorldState, token: int, required_only: bool = false) -> Dictionary:
	if token != _token or not matches_context(state) or not is_inside_tree():
		return {"ok": true, "changed": false, "stale": true}
	if not _required_pending.is_empty():
		var owner: Vector2i = _required_pending.pop_front()
		_regions[owner] = state.get_deposit_region(owner)
		return {"ok": true, "changed": false}
	if not _collected:
		_nearby = _collect(_required_owners, _area)
		_required_ids = _nearby.keys()
		_required_ids.sort()
		# Surviving sprites already have validated immutable registrations. Cached
		# return visits must not spend two more frames per existing deposit.
		_pending_ids = _required_ids.filter(func(identity: String) -> bool:
			return not _sprites.has(identity))
		for identity: String in _footprints.keys():
			if not _nearby.has(identity):
				_footprints.erase(identity)
		_collected = true
		return {"ok": true, "changed": false}
	if _validate_index < _pending_ids.size():
		var identity: String = _pending_ids[_validate_index]
		var registration := _registration(state, _nearby[identity])
		if not registration.ok:
			return registration
		_registrations[identity] = registration
		_validate_index += 1
		return {"ok": true, "changed": false}
	if _commit_index < _pending_ids.size():
		var identity: String = _pending_ids[_commit_index]
		_commit_index += 1
		if not _sprites.has(identity):
			var registration: Dictionary = _registrations[identity]
			var sprite := Sprite2D.new()
			sprite.centered = false
			sprite.position = registration.origin
			sprite.scale = Vector2.ONE * registration.scale
			sprite.texture = registration.texture
			add_child(sprite)
			_sprites[identity] = sprite
			_envelopes[identity] = _nearby[identity].illustrated_envelope
		return {"ok": true, "changed": false}
	if not _required_complete:
		_required_complete = true
		_registrations.clear()
		return {"ok": true, "changed": true}
	# Required data, textures and sprites ALWAYS precede speculative work.
	if required_only:
		return {"ok": true, "changed": false}
	if not _future_pending.is_empty():
		var owner: Vector2i = _future_pending.pop_front()
		_regions[owner] = state.get_deposit_region(owner)
		return {"ok": true, "changed": false}
	if not _future_collected:
		_future = _collect(_future_owners, _lookahead)
		_future_ids = _future.keys()
		_future_ids.sort()
		_future_collected = true
		return {"ok": true, "changed": false}
	if _future_index < _future_ids.size():
		var identity: String = _future_ids[_future_index]
		var registration := _registration(state, _future[identity])
		if not registration.ok:
			return registration
		_future_index += 1
	return {"ok": true, "changed": false}


func _collect(owners: Array[Vector2i], area: Rect2) -> Dictionary:
	var nearby: Dictionary = {}
	for owner in owners:
		for descriptor in _regions[owner]:
			if area.intersects(descriptor.illustrated_envelope, true):
				nearby[descriptor.deposit_id] = descriptor
	return nearby


func _registration(state: PlanetWorldState, descriptor: Dictionary) -> Dictionary:
	var variant_id: String = descriptor.variant_id
	if not _variants.has(variant_id):
		# This private copy never escapes; the simulation's catalog stays isolated.
		_variants[variant_id] = state.get_deposit_variant(variant_id)
	var variant: Dictionary = _variants[variant_id]
	if variant.is_empty() or descriptor.world_seed != _seed \
			or descriptor.catalog_version != FerriteRegionGenerator.CATALOG_VERSION:
		return _failure("Unknown or incompatible variant for " + String(descriptor.deposit_id))
	var texture: Texture2D = _textures.get(variant.id)
	if texture == null:
		var path := "res://" + String(variant.png_path)
		if not ResourceLoader.exists(path, "Texture2D"):
			return _failure("Missing catalog texture: " + path)
		texture = load(path) as Texture2D
		if texture == null:
			return _failure("Cannot load catalog texture: " + path)
		var expected := Vector2(variant.image_size_pixels[0], variant.image_size_pixels[1])
		if texture.get_size() != expected:
			return _failure("Catalog texture dimensions mismatch: " + path)
		_textures[variant.id] = texture
	var scale_value := float(variant.display_scale)
	var origin := Vector2(descriptor.origin_cell) * WorldCoordinates.TERRAIN_SIZE \
		- Vector2(variant.logical_origin_source_pixels[0], variant.logical_origin_source_pixels[1]) * scale_value
	if Rect2(origin, texture.get_size() * scale_value) != descriptor.illustrated_envelope:
		return _failure("Catalog envelope mismatch for " + String(descriptor.deposit_id))
	return {"ok": true, "origin": origin, "scale": scale_value, "texture": texture}


# Exterior-only geometry view: one reconstruction per unique nearby stable ID.
# It is never handed to mining or used as authoritative simulation state.
func highlight_deposits(state: PlanetWorldState, token: int) -> Array[ResourceDeposit]:
	var result: Array[ResourceDeposit] = []
	if not matches_context(state) or not required_ready(token):
		return result
	for deposit in state.get_deposits():
		if _area.intersects(FerriteRegionGenerator._bounds(deposit.footprint), true):
			result.append(deposit)
	for identity: String in _required_ids:
		if not _footprints.has(identity):
			_footprints[identity] = state.deposit_resource(_nearby[identity])
		result.append(_footprints[identity])
	return result


func cancel() -> void:
	_token += 1
	_active = false
	_required_pending.clear()
	_future_pending.clear()
	_required_owners.clear()
	_future_owners.clear()
	_nearby.clear()
	_future.clear()
	_registrations.clear()
	_required_ids.clear()
	_pending_ids.clear()
	_future_ids.clear()
	_validate_index = 0
	_commit_index = 0
	_future_index = 0
	_collected = false
	_future_collected = false
	_required_complete = false


func _remove_sprite(identity: String) -> void:
	var sprite: Sprite2D = _sprites[identity]
	remove_child(sprite)
	sprite.queue_free()
	_sprites.erase(identity)
	_envelopes.erase(identity)


func _clear_sprites() -> void:
	for identity: String in _sprites.keys():
		_remove_sprite(identity)


func _exit_tree() -> void:
	cancel()


func _failure(message: String) -> Dictionary:
	return {"ok": false, "code": &"ferrite_presentation",
		"message": message + ". Correct the input/package and restart the session."}
