class_name OrdinaryResourceGenerator
extends RefCounted
## Isolated ordinary-world policy; no gameplay registration or presentation.
## Numerical tuning is provisional: docs/RESOURCE_GENERATION_V2_GENERATOR.md.

const Definition = preload("res://scenes/world/world_resource_definition.gd")
const Descriptors = preload("res://scenes/world/resource_generation_descriptors.gd")
const Terrain = preload("res://scenes/world/planet_generator.gd")
const POLICY: String = "ordinary-v2-1"
const REGION_SIZE: int = 1536
const REGION_CONSTRUCTION_CELLS: int = 48
const CELL: int = 32
const ANCHOR_SIZE: int = 128
const CANDIDATE_SLOTS: int = 4
const BASE_PERCENT: int = 18
const CONCENTRATION_PERCENT: int = 8
const CONCENTRATION_MULTIPLIER: int = 3
const CONCENTRATION_REGIONS: int = 4
const VISUAL_MARGIN: int = 64
const WITHIN_GAP: int = 32
const WITHIN_MIN: int = 320
const WITHIN_MAX: int = 704
const BETWEEN_GAP: int = 448
const MAX_OFFSET: int = 448
const QUERY_REACH: int = MAX_OFFSET + ANCHOR_SIZE + VISUAL_MARGIN
const CONFLICT_REACH: int = 2 * MAX_OFFSET + ANCHOR_SIZE + 2 * VISUAL_MARGIN + BETWEEN_GAP
const NEIGHBOR_HALO: int = 2
const MAX_REGION_COORDINATE: int = 8192
const MAX_QUERY_REGIONS: int = 64
const CACHE_LIMIT: int = 32

var _seed: int
var _error: String = ""
var _definitions: Array[WorldResourceDefinition] = []
var _protected: Array[Rect2] = []
var _terrain: PlanetGenerator
var _cache: Dictionary = {}


# Explicit protection inputs are immutable authored bounds, never live machines.
# Empty bounds are useful for synthetic worlds, not crash-site integration.
func _init(world_seed: int, definitions: Array[WorldResourceDefinition],
		protected_bounds: Array[Rect2], policy: String = POLICY) -> void:
	_seed = world_seed
	if policy != POLICY:
		_error = "unsupported generation policy: " + policy
		return
	_error = Definition.definitions_error(definitions, [&"terrain_geology"])
	if not _error.is_empty():
		return
	var total := 0.0
	for definition in definitions:
		var snapshot: WorldResourceDefinition = definition.duplicate(true)
		_definitions.append(snapshot)
		var preference := float(snapshot.geological_preferences.get("terrain_geology", 1.0))
		total += snapshot.abundance_weight * maxf(1.0, preference)
	if not is_finite(total):
		_error = "combined geological abundance weights must remain finite"
		return
	_definitions.sort_custom(func(a: WorldResourceDefinition, b: WorldResourceDefinition) -> bool:
		return String(a.resource_id) < String(b.resource_id))
	for bounds in protected_bounds:
		if not bounds.is_finite() or not bounds.end.is_finite() \
				or bounds.size.x < 0.0 or bounds.size.y < 0.0:
			_error = "authored protection requires finite nonnegative rectangles"
			return
		_protected.append(bounds)
	# Existing seed-only terrain geology, with no state/color/material sampling.
	_terrain = Terrain.new(_seed, [], PackedVector2Array(), PackedVector2Array())


func initialization_error() -> String:
	return _error


func is_ready() -> bool:
	return _error.is_empty()


static func owner_at(point: Vector2) -> Vector2i:
	return Vector2i(floori(point.x / REGION_SIZE), floori(point.y / REGION_SIZE))


static func owner_is_supported(owner: Vector2i) -> bool:
	return absi(owner.x) <= MAX_REGION_COORDINATE and absi(owner.y) <= MAX_REGION_COORDINATE


func _sample(owner: Vector2i, slot: int, channel: String) -> int:
	var key := "%s:%d:%d:%d:%d:%s" % [POLICY, _seed, owner.x, owner.y, slot, channel]
	return key.sha256_text().left(7).hex_to_int()


func _group_size(owner: Vector2i, slot: int) -> int:
	var roll := _sample(owner, slot, "group") % 100
	return 1 if roll < 60 else (2 if roll < 90 else 3)


# Continuous numeric input already used for rock/soil blending in PlanetGenerator.
# This is not a biome/category contract; environment restrictions fail admission.
func _geology(point: Vector2) -> float:
	return _terrain._noise(point / 768.0, 1)


func _resource_type(owner: Vector2i, slot: int, geology: float) -> StringName:
	var weights: Array[float] = []
	var total := 0.0
	for definition in _definitions:
		var preference := float(definition.geological_preferences.get("terrain_geology", 1.0))
		var weight := definition.abundance_weight * lerpf(1.0, preference, geology)
		weights.append(weight)
		total += weight
	var roll := float(_sample(owner, slot, "resource")) / 268435456.0 * total
	for index in range(_definitions.size()):
		roll -= weights[index]
		if roll < 0.0:
			return _definitions[index].resource_id
	return _definitions.back().resource_id


func _anchors(owner: Vector2i, slot: int) -> Array[Rect2i]:
	var origin := owner * REGION_CONSTRUCTION_CELLS + Vector2i(
		_sample(owner, slot, "x") % REGION_CONSTRUCTION_CELLS,
		_sample(owner, slot, "y") % REGION_CONSTRUCTION_CELLS)
	var offsets: Array[Vector2i] = [Vector2i.ZERO,
		Vector2i(10 + _sample(owner, slot, "pair_x") % 5, _sample(owner, slot, "pair_y") % 5 - 2),
		Vector2i(2 + _sample(owner, slot, "triple_x") % 5, 12 + _sample(owner, slot, "triple_y") % 3)]
	var result: Array[Rect2i] = []
	var turns := _sample(owner, slot, "rotation") % 4
	var mirror := 1 if _sample(owner, slot, "mirror") % 2 == 0 else -1
	for index in range(_group_size(owner, slot)):
		var offset := offsets[index]
		offset.x *= mirror
		for turn in range(turns):
			offset = Vector2i(-offset.y, offset.x)
		result.append(Rect2i(origin + offset, Vector2i(4, 4)))
	return result


static func anchor_bounds(member: Dictionary) -> Rect2:
	return Rect2(Vector2(member.anchor_cells.position) * CELL, Vector2.ONE * ANCHOR_SIZE)


static func visual_bounds(member: Dictionary) -> Rect2:
	return anchor_bounds(member).grow(VISUAL_MARGIN)


func _eligible(location: Dictionary) -> bool:
	for index in range(location.deposits.size()):
		var member: Dictionary = location.deposits[index]
		var envelope := visual_bounds(member)
		for bounds in _protected:
			if envelope.intersects(bounds, true):
				return false
		for previous in range(index):
			var other: Dictionary = location.deposits[previous]
			var distance := anchor_bounds(member).get_center().distance_to(anchor_bounds(other).get_center())
			if distance < WITHIN_MIN or distance > WITHIN_MAX \
					or member.anchor_cells.intersects(other.anchor_cells) \
					or envelope.grow(WITHIN_GAP).intersects(visual_bounds(other), true):
				return false
	return true


func _candidate(owner: Vector2i, slot: int) -> Dictionary:
	# The halo may inspect supported owners just beyond the public coordinate cap.
	var anchors := _anchors(owner, slot)
	var point := Vector2(anchors[0].position) * CELL + Vector2.ONE * (ANCHOR_SIZE / 2.0)
	var geology := _geology(point)
	var concentration_owner := Vector2i(floori(float(owner.x) / CONCENTRATION_REGIONS),
		floori(float(owner.y) / CONCENTRATION_REGIONS))
	var rich := _sample(concentration_owner, -1, "concentration") % 100 < CONCENTRATION_PERCENT \
		and geology >= 0.55
	var percent := BASE_PERCENT * (CONCENTRATION_MULTIPLIER if rich else 1)
	if _sample(owner, slot, "presence") % 100 >= percent:
		return {}
	var made := Descriptors.create_location(POLICY, _seed, owner, slot,
		_resource_type(owner, slot, geology), anchors)
	if not made.ok or not _eligible(made.location):
		return {}
	return {"location": made.location, "priority": _sample(owner, slot, "priority")}


static func _precedes(a: Dictionary, b: Dictionary) -> bool:
	if a.priority != b.priority:
		return a.priority < b.priority
	return a.location.location_id < b.location.location_id


static func _conflicts(a: Dictionary, b: Dictionary) -> bool:
	for member: Dictionary in a.deposits:
		for other: Dictionary in b.deposits:
			if member.anchor_cells.intersects(other.anchor_cells) \
					or visual_bounds(member).grow(BETWEEN_GAP).intersects(visual_bounds(other), true):
				return true
	return false


func region(owner: Vector2i) -> Dictionary:
	if not is_ready():
		return {"ok": false, "error": _error}
	if not owner_is_supported(owner):
		return {"ok": false, "error": "owner exceeds supported coordinate domain"}
	if _cache.has(owner):
		return {"ok": true, "locations": _cache[owner].duplicate(true)}
	var neighbors: Array[Dictionary] = []
	for y in range(-NEIGHBOR_HALO, NEIGHBOR_HALO + 1):
		for x in range(-NEIGHBOR_HALO, NEIGHBOR_HALO + 1):
			for slot in range(CANDIDATE_SLOTS):
				var candidate := _candidate(owner + Vector2i(x, y), slot)
				if not candidate.is_empty():
					neighbors.append(candidate)
	var accepted: Array[Dictionary] = []
	for candidate in neighbors:
		if candidate.location.owner_region != owner:
			continue
		var blocked := false
		# Eligible RAW competitors, including losers; no recursive acceptance.
		for other in neighbors:
			if _precedes(other, candidate) and _conflicts(candidate.location, other.location):
				blocked = true
				break
		if not blocked:
			accepted.append(candidate.location)
	if _cache.size() >= CACHE_LIMIT:
		_cache.erase(_cache.keys()[0])
	_cache[owner] = accepted
	return {"ok": true, "locations": accepted.duplicate(true)}


# Planning validates before integer conversion/multiplication or generation.
# Inclusive broad phase supports points and exact right/bottom boundaries.
func query_owners(area: Rect2) -> Dictionary:
	if not is_ready():
		return {"ok": false, "error": _error}
	if not area.is_finite() or not area.end.is_finite() or area.size.x < 0.0 or area.size.y < 0.0:
		return {"ok": false, "error": "query requires a finite nonnegative rectangle"}
	var limit := float(MAX_REGION_COORDINATE - 1) * REGION_SIZE
	if maxf(absf(area.position.x), absf(area.end.x)) > limit \
			or maxf(absf(area.position.y), absf(area.end.y)) > limit \
			or area.size.x > REGION_SIZE * MAX_QUERY_REGIONS \
			or area.size.y > REGION_SIZE * MAX_QUERY_REGIONS:
		return {"ok": false, "error": "query exceeds coordinate or extent limits"}
	var first := owner_at(area.position - Vector2.ONE * QUERY_REACH)
	var last := owner_at(area.end + Vector2.ONE * QUERY_REACH)
	var count := (last.x - first.x + 1) * (last.y - first.y + 1)
	if count > MAX_QUERY_REGIONS:
		return {"ok": false, "error": "query exceeds owner budget; page explicitly"}
	var owners: Array[Vector2i] = []
	for y in range(first.y, last.y + 1):
		for x in range(first.x, last.x + 1):
			owners.append(Vector2i(x, y))
	return {"ok": true, "owners": owners}


func query(area: Rect2) -> Dictionary:
	var plan := query_owners(area)
	if not plan.ok:
		return plan
	var deposits: Array[Dictionary] = []
	var seen: Dictionary = {}
	for owner: Vector2i in plan.owners:
		var owned := region(owner)
		if not owned.ok:
			return owned
		for location: Dictionary in owned.locations:
			for member: Dictionary in location.deposits:
				if area.intersects(visual_bounds(member), true) and not seen.has(member.deposit_id):
					seen[member.deposit_id] = true
					deposits.append(member)
	return {"ok": true, "deposits": deposits}


# Both canonical identity forms resolve only ACCEPTED complete locations.
# No generic decoder; exact round-trip checks reject aliases and int overflow.
func identity_policy() -> String:
	return POLICY


func descriptor_by_id(identity: String) -> Dictionary:
	var parts := identity.split(":")
	var is_deposit := parts.size() == 7 and parts[0] == "resource"
	if not is_deposit and not (parts.size() == 6 and parts[0] == "resource-location"):
		return {"ok": false, "error": "invalid identity shape"}
	if parts[1] != identity_policy():
		return {"ok": false, "error": "unsupported identity policy"}
	for index in range(2, parts.size()):
		if not parts[index].is_valid_int() or str(parts[index].to_int()) != parts[index]:
			return {"ok": false, "error": "identity integer is not canonical int64"}
	if parts[2].to_int() != _seed \
			or parts[3].to_int() < -MAX_REGION_COORDINATE or parts[3].to_int() > MAX_REGION_COORDINATE \
			or parts[4].to_int() < -MAX_REGION_COORDINATE or parts[4].to_int() > MAX_REGION_COORDINATE \
			or parts[5].to_int() < 0 or parts[5].to_int() >= CANDIDATE_SLOTS:
		return {"ok": false, "error": "identity outside this world or owner/slot domain"}
	var owned := region(Vector2i(parts[3].to_int(), parts[4].to_int()))
	if not owned.ok:
		return owned
	for location: Dictionary in owned.locations:
		if not is_deposit and location.location_id == identity:
			return {"ok": true, "descriptor": location}
		for member: Dictionary in location.deposits:
			if is_deposit and member.deposit_id == identity:
				return {"ok": true, "descriptor": member}
	return {"ok": false, "error": "identity has no accepted descriptor"}
