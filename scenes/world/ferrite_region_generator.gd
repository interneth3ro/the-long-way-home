class_name FerriteRegionGenerator
extends RefCounted

# Fixed reconstruction policy; changes require a new generation version.
const GENERATION_VERSION := "v1"
const CATALOG_VERSION := "faceted_ferrite_catalog_v1"
const SIZE_POLICY_VERSION := "size_v1"
const REGION_CELLS: int = 48
const CANDIDATE_SLOTS: int = 6
const ORDINARY_SLOTS: int = 3
const RICH_PERCENT: int = 20
const NEIGHBOR_HALO: int = 1
const MAX_REACH_CELLS: int = 12
const VISIBLE_GAP: float = 128.0
const CACHE_LIMIT: int = 32
const MAX_QUERY_REGIONS: int = 64
# Leave room for halo/origin arithmetic inside signed Vector2i terrain cells.
const MAX_REGION_COORDINATE: int = 44739240
const CELL: int = WorldCoordinates.TERRAIN_SIZE
const REGION_SIZE: int = REGION_CELLS * CELL
const CATALOG_PATH := "res://assets/environment/exterior/ferrite/catalog_v1/catalog.json"
const SHAPE_WEIGHTS := {"rectangle": 20, "l_shape": 20, "stepped": 25, "organic": 35}
const SHAPE_ORDER := ["rectangle", "l_shape", "stepped", "organic"]

var _seed: int
var _variants: Array = []
var _by_id: Dictionary = {}
var _cache: Dictionary[Vector2i, Array] = {}
var _protected_bounds: Array[Rect2] = []


func _init(world_seed: int) -> void:
	_seed = world_seed
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(CATALOG_PATH))
	assert(catalog.catalog_version == CATALOG_VERSION)
	_variants = catalog.variants
	_variants.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a.id < b.id)
	for variant: Dictionary in _variants:
		assert(variant.width_cells <= MAX_REACH_CELLS and variant.height_cells <= MAX_REACH_CELLS)
		assert(variant.display_scale == 0.5 and variant.logical_origin_source_pixels == [64, 64])
		assert(variant.image_size_pixels[0] <= (MAX_REACH_CELLS * CELL + CELL) * 2)
		assert(variant.image_size_pixels[1] <= (MAX_REACH_CELLS * CELL + CELL) * 2)
		_by_id[variant.id] = variant
	# Conservative whole-envelope rejection, including containment and edge contact.
	_protected_bounds.append(_bounds(PackedVector2Array(CrashSiteProtection.GAMEPLAY)).grow(VISIBLE_GAP))
	var intro: ResourceDeposit = preload("res://scenes/world/introductory_ferrite.tres")
	# Intro artwork has the same 32-world-unit padded registration as the catalog.
	_protected_bounds.append(_bounds(intro.footprint).grow(32.0 + VISIBLE_GAP))


static func _bounds(polygon: PackedVector2Array) -> Rect2:
	var result := Rect2(polygon[0], Vector2.ZERO)
	for vertex in polygon:
		result = result.expand(vertex)
	return result


static func owner_at(point: Vector2) -> Vector2i:
	return Vector2i(floori(point.x / REGION_SIZE), floori(point.y / REGION_SIZE))


# A SHA-256 channel has no mutable RNG state or platform-dependent String.hash().
# Seven hex digits keep conversion and subsequent arithmetic safely in int64.
func _sample(owner: Vector2i, slot: int, channel: String) -> int:
	var key := "%s:%d:%d:%d:%d:%s" % [GENERATION_VERSION, _seed, owner.x, owner.y, slot, channel]
	return key.sha256_text().left(7).hex_to_int()


# Intentionally isolated: no distance-from-spawn input in size_v1.
func _size_class(owner: Vector2i, slot: int) -> String:
	var roll := _sample(owner, slot, "size_v1") % 100
	return "small" if roll < 10 else ("medium" if roll < 60 else "large")


func _variant(owner: Vector2i, slot: int) -> Dictionary:
	var size := _size_class(owner, slot)
	var available: Dictionary = {}
	for variant: Dictionary in _variants:
		if variant.size_class == size:
			available[variant.shape_family] = true
	var total: int = 0
	for family: String in SHAPE_ORDER:
		if available.has(family):
			total += int(SHAPE_WEIGHTS[family])
	var roll := _sample(owner, slot, "shape") % total
	var selected := ""
	for family: String in SHAPE_ORDER:
		if not available.has(family):
			continue
		roll -= int(SHAPE_WEIGHTS[family])
		if roll < 0:
			selected = family
			break
	var choices: Array[Dictionary] = []
	for variant: Dictionary in _variants:
		if variant.size_class == size and variant.shape_family == selected:
			choices.append(variant)
	return choices[_sample(owner, slot, "variant") % choices.size()]


func _candidate(owner: Vector2i, slot: int) -> Dictionary:
	var rich := _sample(owner, -1, "richness") % 100 < RICH_PERCENT
	if slot >= (CANDIDATE_SLOTS if rich else ORDINARY_SLOTS):
		return {}
	var variant := _variant(owner, slot)
	var origin := owner * REGION_CELLS + Vector2i(
		_sample(owner, slot, "position_x") % REGION_CELLS,
		_sample(owner, slot, "position_y") % REGION_CELLS)
	var registration := Vector2(variant.logical_origin_source_pixels[0],
		variant.logical_origin_source_pixels[1]) * float(variant.display_scale)
	var envelope := Rect2(Vector2(origin) * CELL - registration,
		Vector2(variant.image_size_pixels[0], variant.image_size_pixels[1]) * float(variant.display_scale))
	for reserved in _protected_bounds:
		if envelope.intersects(reserved, true):
			return {}
	var result := {"deposit_id": "ferrite:%s:%d:%d:%d:%d" % [
		GENERATION_VERSION, _seed, owner.x, owner.y, slot],
		"world_seed": _seed, "owner_region": owner, "slot": slot,
		"variant_id": String(variant.id), "origin_cell": origin,
		"catalog_version": CATALOG_VERSION, "generation_version": GENERATION_VERSION,
		"size_policy_version": SIZE_POLICY_VERSION, "illustrated_envelope": envelope,
		"priority": _sample(owner, slot, "priority")}
	result.make_read_only()
	return result


static func _precedes(a: Dictionary, b: Dictionary) -> bool:
	if a.priority != b.priority:
		return a.priority < b.priority
	return a.deposit_id < b.deposit_id


# Compare eligible raw candidates, including losers. No recursive acceptance,
# retries or first-query wins; local minima survive even across region borders.
func region(owner: Vector2i) -> Array:
	if absi(owner.x) > MAX_REGION_COORDINATE or absi(owner.y) > MAX_REGION_COORDINATE:
		return []
	if _cache.has(owner):
		return _cache[owner]
	var neighbors: Array[Dictionary] = []
	for y in range(-NEIGHBOR_HALO, NEIGHBOR_HALO + 1):
		for x in range(-NEIGHBOR_HALO, NEIGHBOR_HALO + 1):
			for slot in range(CANDIDATE_SLOTS):
				var candidate := _candidate(owner + Vector2i(x, y), slot)
				if not candidate.is_empty():
					neighbors.append(candidate)
	var accepted: Array = []
	for candidate in neighbors:
		if candidate.owner_region != owner:
			continue
		var blocked := false
		for other in neighbors:
			if _precedes(other, candidate) and candidate.illustrated_envelope.grow(
					VISIBLE_GAP).intersects(other.illustrated_envelope, true):
				blocked = true
				break
		if not blocked:
			accepted.append(candidate)
	accepted.make_read_only()
	if _cache.size() >= CACHE_LIMIT:
		_cache.erase(_cache.keys()[0])
	_cache[owner] = accepted
	return accepted


# Inclusive broad-phase envelope query, deterministic row-major owner/slot order.
# Reject oversize requests in full; callers must page explicitly, never truncate.
func query_is_bounded(area: Rect2) -> bool:
	if not area.is_finite() or not area.end.is_finite() or area.size.x < 0.0 or area.size.y < 0.0:
		return false
	# Reject unrepresentable coordinates before floor/int conversion, and huge
	# extents before multiplying region counts. No overflow can bypass the budget.
	var limit := float(MAX_REGION_COORDINATE - 1) * REGION_SIZE
	if maxf(absf(area.position.x), absf(area.end.x)) > limit \
			or maxf(absf(area.position.y), absf(area.end.y)) > limit:
		return false
	if area.size.x > REGION_SIZE * MAX_QUERY_REGIONS or area.size.y > REGION_SIZE * MAX_QUERY_REGIONS:
		push_error("Ferrite query exceeds bounded owner-region budget; page the request")
		return false
	var reach := float(MAX_REACH_CELLS * CELL + CELL)
	var first := owner_at(area.position - Vector2.ONE * reach)
	var last := owner_at(area.end + Vector2.ONE * CELL)
	var count := (last.x - first.x + 1) * (last.y - first.y + 1)
	if count > MAX_QUERY_REGIONS:
		push_error("Ferrite query exceeds bounded owner-region budget; page the request")
		return false
	return true


func query(area: Rect2) -> Array:
	if not query_is_bounded(area):
		return []
	var reach := float(MAX_REACH_CELLS * CELL + CELL)
	var first := owner_at(area.position - Vector2.ONE * reach)
	var last := owner_at(area.end + Vector2.ONE * CELL)
	var result: Array = []
	for y in range(first.y, last.y + 1):
		for x in range(first.x, last.x + 1):
			for descriptor in region(Vector2i(x, y)):
				if area.intersects(descriptor.illustrated_envelope, true):
					result.append(descriptor)
	return result


func descriptor_by_id(deposit_id: StringName) -> Dictionary:
	var parts := String(deposit_id).split(":")
	if parts.size() != 6 or parts[0] != "ferrite" or parts[1] != GENERATION_VERSION:
		return {}
	for index in range(2, 6):
		if not parts[index].is_valid_int():
			return {}
	if parts[2].to_int() != _seed:
		return {}
	var owner := Vector2i(parts[3].to_int(), parts[4].to_int())
	for descriptor in region(owner):
		if descriptor.deposit_id == String(deposit_id):
			return descriptor
	return {}


# Fresh Resource objects protect cached immutable descriptors from caller edits.
# Rendering metadata stays in descriptors, never on the simulation Resource.
func resource(descriptor: Dictionary) -> ResourceDeposit:
	var variant: Dictionary = _by_id[descriptor.variant_id]
	var deposit := ResourceDeposit.new()
	deposit.deposit_id = StringName(descriptor.deposit_id)
	deposit.resource_type = &"ferrite"
	var polygon := PackedVector2Array()
	for vertex: Array in variant.logical_polygon_world_units:
		polygon.append(Vector2(vertex[0], vertex[1]) + Vector2(descriptor.origin_cell) * CELL)
	deposit.footprint = polygon
	return deposit
