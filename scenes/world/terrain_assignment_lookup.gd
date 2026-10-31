class_name TerrainAssignmentLookup
extends RefCounted

const TILESET_PATH := "res://assets/experiments/native_terrain_47_96/baked_v2/baked_terrain.tres"
const MANIFEST_PATH := "res://assets/experiments/native_terrain_47_96/baked_v2/mapping.json"
const PEERS := [TileSet.CELL_NEIGHBOR_TOP_LEFT_CORNER, TileSet.CELL_NEIGHBOR_TOP_SIDE,
	TileSet.CELL_NEIGHBOR_TOP_RIGHT_CORNER, TileSet.CELL_NEIGHBOR_LEFT_SIDE,
	TileSet.CELL_NEIGHBOR_RIGHT_SIDE, TileSet.CELL_NEIGHBOR_BOTTOM_LEFT_CORNER,
	TileSet.CELL_NEIGHBOR_BOTTOM_SIDE, TileSet.CELL_NEIGHBOR_BOTTOM_RIGHT_CORNER]

var _assignments: Dictionary = {}
var error: String = "Lookup has not been initialized"


# Explicit opt-in initialization; no production preload or renderer integration.
func initialize() -> bool:
	_assignments.clear()
	error = ""
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST_PATH))
	if not parsed is Dictionary:
		return _fail("Missing or malformed baked manifest")
	var manifest: Dictionary = parsed
	if not manifest.get("baseline") is Array or not manifest.get("interiors") is Array:
		return _fail("Missing manifest inventory")
	var tiles: TileSet = load(TILESET_PATH) as TileSet
	if tiles == null or tiles.get_source_count() != 2 or tiles.get_terrain_sets_count() != 1:
		return _fail("Unexpected native TileSet inventory")
	if tiles.get_terrain_set_mode(0) != TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES:
		return _fail("Unexpected native terrain mode")
	var actual: Dictionary = {}
	for index in range(tiles.get_source_count()):
		var source_id := tiles.get_source_id(index)
		var source := tiles.get_source(source_id) as TileSetAtlasSource
		if source == null:
			return _fail("Expected native atlas source")
		for tile_index in range(source.get_tiles_count()):
			var atlas := source.get_tile_id(tile_index)
			if source.get_alternative_tiles_count(atlas) != 1:
				return _fail("Unexpected native alternative inventory")
			var alternative := source.get_alternative_tile_id(atlas, 0)
			var data := source.get_tile_data(atlas, alternative)
			if data == null or data.terrain_set != 0:
				return _fail("Missing native terrain data")
			var sig := PackedInt32Array([data.terrain])
			for peer in PEERS:
				sig.append(data.get_terrain_peering_bit(peer))
			actual[_location(source_id, atlas)] = {"source_id": source_id,
				"atlas_coords": atlas, "alternative_id": alternative, "signature": sig}
	if manifest.baseline.size() != 94 or manifest.interiors.size() != 4 or actual.size() != 98:
		return _fail("Expected 94 baseline and four interior records")
	var seen: Dictionary = {}
	for group in ["baseline", "interiors"]:
		for entry in manifest[group]:
			if not entry is Dictionary:
				return _fail("Malformed manifest record")
			var coords: Variant = entry.get("atlas")
			var raw_sig: Variant = entry.get("signature")
			if not coords is Array or coords.size() != 2 or not raw_sig is Array or raw_sig.size() != 9:
				return _fail("Malformed manifest coordinates/signature")
			for number in coords + raw_sig:
				if not (number is int or number is float) or float(number) != floor(float(number)):
					return _fail("Noninteger manifest value")
			for terrain in raw_sig:
				if terrain != 0 and terrain != 1:
					return _fail("Unknown manifest terrain")
			for coordinate in coords:
				if coordinate < 0 or coordinate > 2147483647:
					return _fail("Invalid atlas coordinate")
			var sig := PackedInt32Array(raw_sig)
			var source_id := 0 if group == "baseline" else 1
			var atlas := Vector2i(int(coords[0]), int(coords[1]))
			var location := _location(source_id, atlas)
			if seen.has(location) or not actual.has(location):
				return _fail("Duplicate or missing native assignment")
			seen[location] = true
			var record: Dictionary = actual[location]
			if record.signature != sig or record.alternative_id != 0:
				return _fail("TileSet and manifest disagree")
			var variant := str(entry.get("variant", "A"))
			if (group == "baseline" and variant != "A") or (group == "interiors" and variant not in ["B", "C"]):
				return _fail("Unexpected interior variant")
			if group == "interiors":
				for terrain in sig:
					if terrain != sig[0]:
						return _fail("Interior variant is not solid")
			var key := _key(sig, variant)
			if _assignments.has(key):
				return _fail("Duplicate signature/variant")
			record["variant"] = variant
			_assignments[key] = record
	return true


func assignment(sig: PackedInt32Array, variant: String = "A") -> Dictionary:
	var key := _key(sig, variant)
	if not error.is_empty() or not _assignments.has(key):
		push_error("TerrainAssignmentLookup: unavailable signature/variant: " + key + " " + error)
		return {}
	return _assignments[key].duplicate(true)


static func _location(source_id: int, atlas: Vector2i) -> String:
	return "%d:%d:%d" % [source_id, atlas.x, atlas.y]


static func _key(sig: PackedInt32Array, variant: String) -> String:
	return str(sig) + ":" + variant


func _fail(message: String) -> bool:
	_assignments.clear()
	error = message
	push_error("TerrainAssignmentLookup: " + message)
	return false
