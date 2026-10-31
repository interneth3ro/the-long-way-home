class_name TerrainResolver
extends RefCounted

# Presentation rule version, independent of the sampler's world-generation version.
const RULE_VERSION: int = 1
const HASH_MODULUS: int = 2147483647
const PRESENTATION_CHANNEL: int = 193


static func classify(material: int) -> int:
	if material < 0 or material > 4:
		return -1
	return int(material > 0)


# Samples: center, NW, N, NE, W, E, SW, S, SE, from an absolute-cell
# sampler or one-cell halo. No loaded-chunk or rendered-cell dependency.
static func signature(materials: PackedInt32Array, rule_version: int = RULE_VERSION) -> PackedInt32Array:
	if rule_version != RULE_VERSION or materials.size() != 9:
		push_error("TerrainResolver: unknown rule version or incomplete neighborhood")
		return PackedInt32Array()
	var g := PackedInt32Array()
	for material in materials:
		var terrain := classify(material)
		if terrain < 0:
			push_error("TerrainResolver: unsupported material")
			return PackedInt32Array()
		g.append(terrain)
	# Products implement AND on binary terrain IDs. Earth center is solid Earth.
	return PackedInt32Array([g[0],
		g[0] * g[1] * g[2] * g[4], g[0] * g[2],
		g[0] * g[2] * g[3] * g[5], g[0] * g[4], g[0] * g[5],
		g[0] * g[4] * g[6] * g[7], g[0] * g[7], g[0] * g[5] * g[7] * g[8]])


# Reduce before multiplication: all intermediates fit signed int64, even for
# negative coordinates/seeds. This channel never touches PlanetGenerator's RNG.
static func variation_bucket(cell: Vector2i, presentation_seed: int = 0) -> int:
	var value := posmod(presentation_seed, HASH_MODULUS)
	value = posmod(value * 48271 + posmod(cell.x, HASH_MODULUS) * 69621, HASH_MODULUS)
	value = posmod(value * 48271 + posmod(cell.y, HASH_MODULUS) * 907, HASH_MODULUS)
	value = posmod(value * 48271 + PRESENTATION_CHANNEL * 104729, HASH_MODULUS)
	value = posmod((value ^ (value >> 13)) * 48271, HASH_MODULUS)
	return value % 100


static func variant_for_bucket(bucket: int) -> String:
	if bucket < 0 or bucket >= 100:
		return ""
	if bucket < 60:
		return "A"
	if bucket < 85:
		return "B"
	return "C"


# Successful output contains source_id, atlas_coords, alternative_id, signature,
# and variant. Failure returns {} and reports a diagnostic; no approximate tile.
static func resolve(cell: Vector2i, materials: PackedInt32Array, lookup: TerrainAssignmentLookup,
		presentation_seed: int = 0, rule_version: int = RULE_VERSION) -> Dictionary:
	var resolved := signature(materials, rule_version)
	if resolved.is_empty() or lookup == null:
		return {}
	var variant := "A"
	var solid := true
	for terrain in resolved:
		if terrain != resolved[0]:
			solid = false
	if solid:
		variant = variant_for_bucket(variation_bucket(cell, presentation_seed))
	return lookup.assignment(resolved, variant)
