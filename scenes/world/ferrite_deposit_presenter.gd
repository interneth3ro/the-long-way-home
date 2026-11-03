class_name FerriteDepositPresenter
extends Node2D

# Disposable exterior-local artwork only. Simulation and ID lookup live in state.
const QUERY_PAGE_SIZE: int = 4 * WorldCoordinates.CHUNK_SIZE
var _sprites: Dictionary[String, Sprite2D] = {}
var _textures: Dictionary[String, Texture2D] = {}


# At most 16 pages for the exterior's maximum 13x13-chunk retention square.
# Each page plus the generator's owner lookup halo is below its 64-owner cap.
static func query_areas(area: Rect2) -> Array[Rect2]:
	var result: Array[Rect2] = []
	for y in range(ceili(area.size.y / QUERY_PAGE_SIZE)):
		for x in range(ceili(area.size.x / QUERY_PAGE_SIZE)):
			var start := area.position + Vector2(x, y) * QUERY_PAGE_SIZE
			result.append(Rect2(start, Vector2(
				minf(QUERY_PAGE_SIZE, area.end.x - start.x),
				minf(QUERY_PAGE_SIZE, area.end.y - start.y))))
	return result


func refresh(state: PlanetWorldState, area: Rect2) -> Dictionary:
	if not state.is_resource_generation_ready():
		return _failure(state.resource_generation_error())
	var nearby: Dictionary = {}
	for page in query_areas(area):
		for descriptor in state.query_deposit_descriptors(page):
			nearby[descriptor.deposit_id] = descriptor
	# Resolve/validate before changing nodes. Failed inputs never create substitutes.
	var registrations: Dictionary = {}
	for identity: String in nearby:
		var descriptor: Dictionary = nearby[identity]
		var variant := state.get_deposit_variant(descriptor.variant_id)
		if variant.is_empty() or descriptor.catalog_version != FerriteRegionGenerator.CATALOG_VERSION:
			return _failure("Unknown or incompatible variant for " + identity)
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
			return _failure("Catalog envelope mismatch for " + identity)
		registrations[identity] = {"origin": origin, "scale": scale_value, "texture": texture}
	for identity: String in nearby:
		if _sprites.has(identity):
			continue
		var registration: Dictionary = registrations[identity]
		var sprite := Sprite2D.new()
		sprite.centered = false
		sprite.position = registration.origin
		sprite.scale = Vector2.ONE * registration.scale
		sprite.texture = registration.texture
		add_child(sprite)
		_sprites[identity] = sprite
	# Queries include complete illustrated envelopes, even outside owner/chunk life.
	for identity: String in _sprites.keys():
		if not nearby.has(identity):
			var sprite: Sprite2D = _sprites[identity]
			remove_child(sprite)
			sprite.queue_free()
			_sprites.erase(identity)
	return {"ok": true}


func _failure(message: String) -> Dictionary:
	return {"ok": false, "code": &"ferrite_presentation",
		"message": message + ". Correct the input/package and restart the session."}
