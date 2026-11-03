extends SceneTree
## Fixed smoke assertions only; never instantiate gameplay state or load artwork.
const Metadata = preload("res://scenes/world/continuous_terrain_metadata.gd")
const Generator = preload("res://scenes/world/planet_generator.gd")
var failures: int = 0


func check(value: bool, label: String) -> void:
	if not value:
		failures += 1
		printerr("SMOKE_FAIL: " + label)


func points(values: Array) -> PackedVector2Array:
	var result := PackedVector2Array()
	for pair in values:
		result.append(Vector2(pair[0], pair[1]))
	return result


func build(seed: Variant, chunk: Variant, geometry: Dictionary) -> Dictionary:
	return Metadata.prepare(seed, chunk, geometry.overlays, geometry.protected, geometry.anchors)


func reject(seed: Variant, chunk: Variant, geometry: Dictionary, error: String) -> void:
	var result := build(seed, chunk, geometry)
	check(result == {"ok": false, "error": error}, "reject without partial payload: " + error)


func _initialize() -> void:
	var raw: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(
		"res://tests/fixtures/metadata_smoke/geometry.json"))
	var overlays: Array[Dictionary] = []
	for overlay in raw.overlays:
		overlays.append({"polygon": points(overlay.polygon), "feather": overlay.feather,
			"color": Color(overlay.color[0], overlay.color[1], overlay.color[2], overlay.color[3])})
	var anchors := PackedVector2Array()
	for anchor in raw.anchors:
		anchors.append(Vector2(anchor[1][0], anchor[1][1]))
	var geometry := {"overlays": overlays, "protected": points(raw.protected), "anchors": anchors}
	# Decimal strings avoid JSON float truncation of signed int64 endpoints.
	for text in ["-9223372036854775808", "-42", "-1", "0", "26026", "9223372036854775807"]:
		var seed := text.to_int()
		var generator := Generator.new(seed, overlays, geometry.protected, anchors)
		var shared := {}
		for chunk in [Vector2i(-1, -1), Vector2i(0, -1), Vector2i(-1, 0), Vector2i.ZERO,
				Vector2i(-16, -16), Vector2i(-16, 15), Vector2i(15, -16), Vector2i(15, 15)]:
			var result := build(seed, chunk, geometry)
			check(result.get("ok", false), "prepare")
			if not result.get("ok", false):
				continue
			check(result.seed == seed and result.chunk == chunk and result.schema == 1, "signed identity")
			check(result.runtime_certified == false, "uncertified")
			check(typeof(result.materials) == TYPE_PACKED_BYTE_ARRAY and result.materials.size() == 1156, "34x34 bytes")
			if result.materials.size() != 1156:
				continue
			check(result == build(seed, chunk, geometry), "repeatability")
			for y in range(-1, 33):
				for x in range(-1, 33):
					var cell: Vector2i = chunk * 32 + Vector2i(x, y)
					var material: int = result.materials[(y + 1) * 34 + x + 1]
					check(material >= 0 and material <= 4, "IDs 0..4")
					# All fixture cells, including outer halos, use the actual classifier.
					check(material == generator.sample_ground_material(cell), "row-major classifier parity")
					if shared.has(cell):
						check(shared[cell] == material, "overlapping halo identity")
					shared[cell] = material
			check(result.geometry == geometry, "copied geometry value")
	# Existing independent OFFLINE goldens are regression expectations, not a proof.
	var vectors: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(
		"res://tests/fixtures/terrain_stage2_classification_vectors.json"))
	for record in vectors.records:
		var cell := Vector2i(record.cell[0], record.cell[1])
		var owner := WorldCoordinates.terrain_to_chunk(cell)
		var local := cell - owner * 32
		var result := build(int(record.seed), owner, geometry)
		check(result.get("ok", false), "golden prepare")
		if result.get("ok", false):
			check(result.materials[(local.y + 1) * 34 + local.x + 1] == int(record.material), "offline golden")
	check(WorldCoordinates.world_to_terrain(Vector2(-0.25, -0.25)) == Vector2i(-1, -1), "negative world")
	check(WorldCoordinates.terrain_to_chunk(Vector2i(-1, -1)) == Vector2i(-1, -1), "negative owner")
	check(WorldCoordinates.terrain_to_local(Vector2i(-1, -1)) == Vector2i(31, 31), "negative local")
	reject(1.0, Vector2i.ZERO, geometry, "seed_type")
	reject(1, Vector2.ZERO, geometry, "chunk_type")
	for chunk in [Vector2i(-17, 0), Vector2i(16, 0), Vector2i(0, -17), Vector2i(0, 16)]:
		reject(1, chunk, geometry, "unsupported_chunk")
	var bad := geometry.duplicate(true)
	bad.protected = PackedVector2Array([Vector2.ZERO])
	reject(1, Vector2i.ZERO, bad, "geometry_points")
	bad = geometry.duplicate(true)
	bad.anchors = PackedVector2Array([Vector2(INF, 0)])
	reject(1, Vector2i.ZERO, bad, "geometry_points")
	bad = geometry.duplicate(true)
	bad.overlays = null
	reject(1, Vector2i.ZERO, bad, "overlays_type")
	bad.overlays = [null]
	reject(1, Vector2i.ZERO, bad, "overlay_type")
	bad.overlays = [{"polygon": PackedVector2Array(), "feather": 1.0}]
	reject(1, Vector2i.ZERO, bad, "overlay_polygon")
	for feather in [0.0, -1.0, INF, NAN, "256"]:
		bad = geometry.duplicate(true)
		bad.overlays[0].feather = feather
		reject(1, Vector2i.ZERO, bad, "overlay_feather")
	var copied := build(-42, Vector2i.ZERO, geometry)
	var before := copied.duplicate(true)
	geometry.overlays[0].polygon[0] = Vector2(9999, 9999)
	geometry.overlays[0].feather = 9999.0
	geometry.protected[0] = Vector2(9999, 9999)
	geometry.anchors[0] = Vector2(9999, 9999)
	check(copied == before, "input mutation leaves copied geometry/payload unchanged")
	print("TLWH_METADATA_SMOKE_V1 failures: %d" % failures)
	quit(0 if failures == 0 else 1)
