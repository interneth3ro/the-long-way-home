class_name StartingResourceGenerator
extends "res://scenes/world/ordinary_resource_generator.gd"
## Versioned shared v2 policy. No gameplay caller, activation input or legacy input.

const STARTING_POLICY: String = "starting-v2-1"
const ARRANGEMENT_BUDGET: int = 512
const START_SLOT: int = 4
const MIN_DISTANCE: int = 384
const MAX_DISTANCE: int = 2304
const INNER_RADIUS: int = 1536
const TRANSITION_WIDTH: int = 1536
const REQUIRED := {"ferrite": 3, "carbite": 2, "cuprite": 2}
const TYPES := ["ferrite", "carbite", "cuprite"]
# Every resource can select every band; these are preferences, never exclusions.
const BAND_THRESHOLDS := [[25, 90], [10, 65], [5, 30]]
const BAND_CELLS := [[14, 22], [26, 46], [50, 68]]
const DIRECTIONS := [Vector2i(1000, 0), Vector2i(924, 383), Vector2i(707, 707),
	Vector2i(383, 924), Vector2i(0, 1000), Vector2i(-383, 924),
	Vector2i(-707, 707), Vector2i(-924, 383), Vector2i(-1000, 0),
	Vector2i(-924, -383), Vector2i(-707, -707), Vector2i(-383, -924),
	Vector2i(0, -1000), Vector2i(383, -924), Vector2i(707, -707), Vector2i(924, -383)]

var _ship: Vector2
var _reservations: Array[Dictionary] = []
var _attempts: int = 0


func _init(world_seed: int, definitions: Array[WorldResourceDefinition],
		protected_bounds: Array[Rect2], ship_reference: Vector2,
		policy: String = STARTING_POLICY) -> void:
	super(world_seed, definitions, protected_bounds)
	if not is_ready():
		return
	if policy != STARTING_POLICY:
		_error = "unsupported starting policy: " + policy
		return
	var limit := float(MAX_REGION_COORDINATE - 4) * REGION_SIZE
	if not ship_reference.is_finite() or absf(ship_reference.x) > limit or absf(ship_reference.y) > limit:
		_error = "ship reference exceeds finite supported domain"
		return
	_ship = ship_reference
	var configured: Dictionary = {}
	for definition in _definitions:
		configured[String(definition.resource_id)] = true
	for resource_type: String in TYPES:
		if not configured.has(resource_type):
			_error = "starting guarantee requires definition: " + resource_type
			return
	# Construct every member before validating any arrangement. Never publish a prefix.
	for attempt in range(ARRANGEMENT_BUDGET):
		_attempts += 1
		var arrangement := _arrangement(attempt)
		if _arrangement_valid(arrangement):
			_reservations = arrangement
			return
	_error = "complete seven-deposit starting arrangement exhausted %d candidates" % ARRANGEMENT_BUDGET


func identity_policy() -> String:
	return STARTING_POLICY


func reservations() -> Dictionary:
	if not is_ready():
		return {"ok": false, "error": _error, "attempts": _attempts}
	return {"ok": true, "locations": _reservations.duplicate(true), "attempts": _attempts}


func _starting_sample(attempt: int, slot: int, channel: String) -> int:
	var key := "%s:%d:%d:%d:%s" % [STARTING_POLICY, _seed, attempt, slot, channel]
	return key.sha256_text().left(7).hex_to_int()


func _arrangement(attempt: int) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var slot := START_SLOT
	for type_index in range(TYPES.size()):
		var resource_type: String = TYPES[type_index]
		var remaining: int = REQUIRED[resource_type]
		while remaining > 0: # At most seven groups; remaining strictly decreases.
			var members := 1 + _starting_sample(attempt, slot, "group") % remaining
			remaining -= members
			var roll := _starting_sample(attempt, slot, "band") % 100
			var band := 0 if roll < BAND_THRESHOLDS[type_index][0] else (
				1 if roll < BAND_THRESHOLDS[type_index][1] else 2)
			var low: int = BAND_CELLS[band][0]
			var radius: int = low + _starting_sample(attempt, slot, "radius") % (BAND_CELLS[band][1] - low + 1)
			var direction: Vector2i = DIRECTIONS[_starting_sample(attempt, slot, "direction") % DIRECTIONS.size()]
			var center := _ship + Vector2(direction) * (float(radius * CELL) / 1000.0)
			var origin := Vector2i(roundi(center.x / CELL) - 2, roundi(center.y / CELL) - 2)
			var offsets: Array[Vector2i] = [Vector2i.ZERO, Vector2i(12, -2), Vector2i(4, 12)]
			var turns := _starting_sample(attempt, slot, "rotation") % 4
			var anchors: Array[Rect2i] = []
			for index in range(members):
				var offset := offsets[index]
				for turn in range(turns):
					offset = Vector2i(-offset.y, offset.x)
				anchors.append(Rect2i(origin + offset, Vector2i(4, 4)))
			var owner := owner_at(Vector2(origin) * CELL)
			var made := Descriptors.create_location(STARTING_POLICY, _seed, owner, slot,
				StringName(resource_type), anchors)
			if not made.ok:
				return []
			result.append(made.location)
			slot += 1
	return result


func _arrangement_valid(locations: Array[Dictionary]) -> bool:
	var counts := {"ferrite": 0, "carbite": 0, "cuprite": 0}
	var identities: Dictionary = {}
	for index in range(locations.size()):
		var location := locations[index]
		if not Descriptors.configured_location_error(location, _definitions, [&"terrain_geology"]).is_empty():
			return false
		if location.generation_policy != STARTING_POLICY or location.world_seed != _seed \
				or location.location_slot < START_SLOT or location.location_slot >= START_SLOT + 7 \
				or identities.has(location.location_id) or not counts.has(location.resource_type) \
				or not owner_is_supported(location.owner_region) \
				or location.owner_region != owner_at(anchor_bounds(location.deposits[0]).position) \
				or not _eligible(location):
			return false
		identities[location.location_id] = true
		counts[location.resource_type] += location.deposits.size()
		for member: Dictionary in location.deposits:
			var distance := anchor_bounds(member).get_center().distance_to(_ship)
			if distance < MIN_DISTANCE or distance > MAX_DISTANCE:
				return false
		for previous in range(index):
			if _conflicts(location, locations[previous]):
				return false
	return counts == REQUIRED


static func transition_density(distance: float) -> float:
	return smoothstep(float(INNER_RADIUS), float(INNER_RADIUS + TRANSITION_WIDTH), distance)


func _ordinary_allowed(location: Dictionary, owner: Vector2i, slot: int) -> bool:
	var center := anchor_bounds(location.deposits[0]).get_center()
	var density := transition_density(center.distance_to(_ship))
	var roll := float(_starting_sample(0, slot, "transition:%d:%d" % [owner.x, owner.y])) / 268435456.0
	if roll >= density:
		return false
	for reservation in _reservations:
		if _conflicts(location, reservation):
			return false
	return true


func _candidate(owner: Vector2i, slot: int) -> Dictionary:
	# This override runs for EVERY raw competitor, before local-priority resolution.
	# Keep v2-1 geological/group/position/priority channels deliberately unchanged.
	var raw := super._candidate(owner, slot)
	if raw.is_empty() or not _ordinary_allowed(raw.location, owner, slot):
		return {}
	var anchors: Array[Rect2i] = []
	for member: Dictionary in raw.location.deposits:
		anchors.append(member.anchor_cells)
	var made := Descriptors.create_location(STARTING_POLICY, _seed, owner, slot,
		StringName(raw.location.resource_type), anchors)
	if not made.ok:
		return {}
	return {"location": made.location, "priority": raw.priority}


func region(owner: Vector2i) -> Dictionary:
	var result := super.region(owner)
	if not result.ok:
		return result
	for location in _reservations:
		if location.owner_region == owner:
			result.locations.append(location.duplicate(true))
	return result


func descriptor_by_id(identity: String) -> Dictionary:
	if not is_ready():
		return {"ok": false, "error": _error}
	# Exact comparison of seven reserved members also rejects malformed aliases.
	for location in _reservations:
		if identity == location.location_id:
			return {"ok": true, "descriptor": location.duplicate(true)}
		for member: Dictionary in location.deposits:
			if identity == member.deposit_id:
				return {"ok": true, "descriptor": member.duplicate(true)}
	return super.descriptor_by_id(identity)
