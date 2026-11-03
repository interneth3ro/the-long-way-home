class_name ContinuousTerrainMetadata
extends RefCounted
## Isolated Stage 3A-1 preparation; no renderer or protection certification.

const Generator = preload("res://scenes/world/planet_generator.gd")
const MIN_CHUNK := -16
const MAX_CHUNK := 15
const HALO_WIDTH := 34


# Variant inputs deliberately reject coercion (including float seeds/chunks).
# Geometry must come from the same authored context as the production generator.
static func prepare(seed: Variant, chunk: Variant, overlays: Variant,
		protected: Variant, anchors: Variant) -> Dictionary:
	if typeof(seed) != TYPE_INT:
		return {"ok": false, "error": "seed_type"}
	if typeof(chunk) != TYPE_VECTOR2I:
		return {"ok": false, "error": "chunk_type"}
	if chunk.x < MIN_CHUNK or chunk.x > MAX_CHUNK \
			or chunk.y < MIN_CHUNK or chunk.y > MAX_CHUNK:
		return {"ok": false, "error": "unsupported_chunk"}
	if WorldCoordinates.TERRAIN_SIZE != 64 or WorldCoordinates.CHUNK_TILES != 32:
		return {"ok": false, "error": "unsupported_grid"}
	if not _valid_points(protected, 3) or not _valid_points(anchors, 0):
		return {"ok": false, "error": "geometry_points"}
	if typeof(overlays) != TYPE_ARRAY:
		return {"ok": false, "error": "overlays_type"}
	var copied_overlays: Array[Dictionary] = []
	for overlay in overlays:
		if typeof(overlay) != TYPE_DICTIONARY:
			return {"ok": false, "error": "overlay_type"}
		if not _valid_points(overlay.get("polygon"), 3):
			return {"ok": false, "error": "overlay_polygon"}
		var feather: Variant = overlay.get("feather")
		if typeof(feather) != TYPE_FLOAT and typeof(feather) != TYPE_INT:
			return {"ok": false, "error": "overlay_feather"}
		if not is_finite(float(feather)) or float(feather) <= 0.0:
			return {"ok": false, "error": "overlay_feather"}
		copied_overlays.append(overlay.duplicate(true))
	var generator := Generator.new(seed, copied_overlays, protected.duplicate(), anchors.duplicate())
	var materials := PackedByteArray()
	materials.resize(HALO_WIDTH * HALO_WIDTH)
	var origin: Vector2i = chunk * WorldCoordinates.CHUNK_TILES
	for y in range(-1, 33):
		for x in range(-1, 33):
			var cell := origin + Vector2i(x, y)
			var material: int = generator.sample_ground_material(cell)
			if material < 0 or material > 4:
				return {"ok": false, "error": "material_range"}
			materials[(y + 1) * HALO_WIDTH + x + 1] = material
	return {"ok": true, "schema": 1, "seed": seed, "chunk": chunk,
		"materials": materials, "runtime_certified": false,
		"geometry": {"overlays": copied_overlays, "protected": protected.duplicate(),
			"anchors": anchors.duplicate()}}


static func _valid_points(points: Variant, minimum: int) -> bool:
	if typeof(points) != TYPE_PACKED_VECTOR2_ARRAY:
		return false
	if points.size() < minimum:
		return false
	for point in points:
		if not point.is_finite():
			return false
	return true
