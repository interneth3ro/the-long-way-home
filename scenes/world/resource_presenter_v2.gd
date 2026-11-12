class_name ResourcePresenterV2
extends Node2D
## Disposable descriptor view. No ResourceDeposit, placement, save or mining API.

const Catalog = preload("res://scenes/world/resource_presentation_catalog.gd")
const Descriptors = preload("res://scenes/world/resource_generation_descriptors.gd")
const MAX_CATALOGS: int = 8
const MAX_OWNERS: int = 64
const MAX_DESCRIPTORS: int = 775 # 64 * 4 * 3 ordinary members + seven reservations.
const MAX_LOCATIONS_PER_OWNER: int = 11
const TEXTURE_LIMIT: int = 8
const MAX_AREA_AXIS: float = 6144.0

var _source: OrdinaryResourceGenerator
var _seed: int
var _policy: String
var _catalogs: Dictionary = {}
var _references: Dictionary = {}
var _reach: float = 0.0
var _token: int = 0
var _active: bool = false
var _area: Rect2
var _owners: Array = []
var _locations: Array = []
var _registrations: Dictionary = {}
var _ids: Array = []
var _ordered: bool = false
var _index: int = 0
var _sprites: Dictionary = {}
var _textures: Dictionary = {}
var _exiting: bool = false


# Source is an immutable generator instance; replace it via configure for ANY
# seed, policy, definitions or protection change. Configuration owns catalog copies.
func configure(source: OrdinaryResourceGenerator, world_seed: int,
		definitions: Array[WorldResourceDefinition]) -> Dictionary:
	dispose()
	if source == null or not source.is_ready() or definitions.is_empty() \
			or definitions.size() > MAX_CATALOGS:
		return Catalog.failure("Invalid presentation context")
	for definition in definitions:
		if definition == null or _catalogs.has(String(definition.resource_id)):
			return _failure("Null or duplicate presentation definition")
		var resource_id := String(definition.resource_id)
		var catalog := Catalog.read_catalog(definition.presentation_catalog, resource_id)
		if not catalog.ok:
			return _failure(catalog.error)
		_catalogs[resource_id] = catalog
		_references[resource_id] = definition.presentation_catalog
		_reach = maxf(_reach, catalog.reach)
	_source = source
	_seed = world_seed
	_policy = source.identity_policy()
	return {"ok": true}


func request(area: Rect2) -> Dictionary:
	cancel()
	if _source == null or not area.is_finite() or not area.end.is_finite() \
			or area.size.x <= 0.0 or area.size.y <= 0.0 \
			or area.size.x > MAX_AREA_AXIS or area.size.y > MAX_AREA_AXIS:
		return Catalog.failure("Invalid context or presentation area")
	# Plan with actual artwork reach, not the generator's smaller clearance envelope.
	# query_owners adds its own conservative group-offset halo; false positives safe.
	var plan := _source.query_owners(area.grow(_reach))
	if not plan.ok:
		return plan
	if plan.owners.size() > MAX_OWNERS:
		return Catalog.failure("Presentation owner budget exceeded")
	_area = area
	_owners = plan.owners.duplicate()
	_active = true
	return {"ok": true, "token": _token}


# One bounded region reconstruction, complete location admission (<=3 members),
# ordering pass (<=775), or texture/sprite per call. No async work outlives token.
func step(token: int) -> Dictionary:
	if token != _token or not _active:
		return {"ok": true, "stale": true}
	if _source == null or not _source.is_ready() or _source.identity_policy() != _policy:
		return _failure("Presentation generation context changed")
	if not _locations.is_empty():
		var location: Dictionary = _locations.pop_front()
		var error := Descriptors.location_error(location)
		if not error.is_empty():
			return _failure(error)
		if location.world_seed != _seed or location.generation_policy != _policy:
			return _failure("Descriptor seed/policy mismatch")
		# Inactive types are deliberately not presentation candidates; all remain in source.
		if not _catalogs.has(location.resource_type):
			return {"ok": true, "done": false}
		for member: Dictionary in location.deposits:
			var registration := Catalog.registration(member, _references[member.resource_type],
				_catalogs[member.resource_type])
			if not registration.ok:
				return _failure(registration.error)
			if not _area.intersects(registration.illustrated_envelope, true):
				continue
			var identity: String = member.deposit_id
			if _registrations.has(identity) and _registrations[identity] != registration:
				return _failure("Conflicting duplicate descriptor: " + identity)
			_registrations[identity] = registration
			if _registrations.size() > MAX_DESCRIPTORS:
				return _failure("Presentation descriptor budget exceeded")
		return {"ok": true, "done": false}
	if not _owners.is_empty():
		var owner: Vector2i = _owners.pop_front()
		var result := _source.region(owner)
		if not result.ok:
			return _failure(result.error)
		if result.locations.size() > MAX_LOCATIONS_PER_OWNER:
			return _failure("Presentation region budget exceeded")
		_locations = result.locations
		return {"ok": true, "done": false}
	if not _ordered:
		_ids = _registrations.keys()
		_ids.sort()
		_ordered = true
		return {"ok": true, "done": false}
	if _index < _ids.size():
		var identity: String = _ids[_index]
		var registration: Dictionary = _registrations[identity]
		var texture_result := _texture(registration)
		if not texture_result.ok:
			return _failure(texture_result.error)
		if not _sprites.has(identity):
			var sprite := Sprite2D.new()
			sprite.position = registration.position
			sprite.scale = Vector2.ONE * registration.scale
			sprite.texture = texture_result.texture
			sprite.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
			sprite.z_index = -5
			add_child(sprite)
			_sprites[identity] = sprite
		_index += 1
		return {"ok": true, "done": false}
	return {"ok": true, "done": true}


func _texture(registration: Dictionary) -> Dictionary:
	var key: String = registration.artwork + ":" + registration.sha256
	if _textures.has(key):
		return {"ok": true, "texture": _textures[key]}
	var file := FileAccess.open(registration.artwork, FileAccess.READ)
	if file == null or file.get_length() > Catalog.MAX_IMAGE_BYTES:
		return Catalog.failure("Missing or oversized artwork: " + registration.artwork)
	file.close()
	if FileAccess.get_sha256(registration.artwork) != registration.sha256 \
			or not ResourceLoader.exists(registration.artwork, "Texture2D"):
		return Catalog.failure("Artwork hash/import mismatch: " + registration.artwork)
	var texture := load(registration.artwork) as Texture2D
	if texture == null or texture.get_size() != registration.size:
		return Catalog.failure("Artwork texture/dimension mismatch: " + registration.artwork)
	if _textures.size() >= TEXTURE_LIMIT:
		_textures.erase(_textures.keys()[0])
	_textures[key] = texture
	return {"ok": true, "texture": texture}


func snapshot() -> Dictionary:
	return {"token": _token, "active": _active, "descriptors": _registrations.size(),
		"sprites": _sprites.size(), "textures": _textures.size()}


func cancel() -> void:
	_token += 1
	_active = false
	_owners.clear()
	_locations.clear()
	_registrations.clear()
	_ids.clear()
	_ordered = false
	_index = 0
	# Detach and free now: repeated same-frame requests cannot accumulate queued nodes.
	for sprite: Sprite2D in _sprites.values():
		if _exiting:
			# Tree exit must not mutate the exiting hierarchy. Hidden immediately;
			# deferred deletion is safe even if the detached root is retained.
			sprite.hide()
			sprite.queue_free()
		else:
			remove_child(sprite)
			sprite.free()
	_sprites.clear()


func dispose() -> void:
	cancel()
	_source = null
	_catalogs.clear()
	_references.clear()
	_textures.clear()
	_reach = 0.0


func _failure(message: String) -> Dictionary:
	dispose()
	return Catalog.failure(message)


func _exit_tree() -> void:
	_exiting = true
	dispose()
	_exiting = false
