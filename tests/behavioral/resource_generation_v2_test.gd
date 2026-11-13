extends RefCounted
## Authored only: this expanded manifest requires separate execution approval.
const Ordinary = preload("res://scenes/world/ordinary_resource_generator.gd")
const Starting = preload("res://scenes/world/starting_resource_generator.gd")
const Descriptors = preload("res://scenes/world/resource_generation_descriptors.gd")
const CrashSite = preload("res://scenes/world/resource_generation_crash_site.gd")
const FERRITE = preload("res://scenes/world/resource_definitions/v2/ferrite.tres")
const CARBITE = preload("res://scenes/world/resource_definitions/v2/carbite.tres")
const CUPRITE = preload("res://scenes/world/resource_definitions/v2/cuprite.tres")
const OWNERS := [Vector2i(-1, -1), Vector2i(0, -1), Vector2i(-1, 0), Vector2i.ZERO]

var _checks: int = 0
var _failures: Array[String] = []


# Supplies only raw candidates. Production region/query/ID resolution stay intact.
# Reuses the raw-chain geometry from ordinary_resource_generator_test.gd.
class CandidateFixture:
	extends "res://scenes/world/ordinary_resource_generator.gd"
	var raw: Dictionary = {}

	func _candidate(owner: Vector2i, slot: int) -> Dictionary:
		return raw.get(owner, {}) if slot == 0 else {}


func run() -> Dictionary:
	_checks = 0
	_failures.clear()
	_starting_guarantees()
	_deterministic_reconstruction()
	_stable_identities()
	_boundary_queries()
	_atomic_conflicts()
	_definition_and_copy_isolation()
	return {"checks": _checks, "failures": _failures.duplicate()}


func _expect(actual: Variant, expected: Variant, context: String) -> bool:
	_checks += 1
	if actual == expected:
		return true
	_failures.append("%s: expected %s; got %s" % [context, str(expected), str(actual)])
	return false


func _ready(source: OrdinaryResourceGenerator, context: String) -> bool:
	return _expect(source.is_ready(), true, context + " initialization: " + source.initialization_error())


func _ok(result: Dictionary, context: String) -> bool:
	return _expect(result.get("ok", false), true, context + " result: " + str(result.get("error", "")))


func _definitions() -> Array[WorldResourceDefinition]:
	return [FERRITE.duplicate(true), CARBITE.duplicate(true), CUPRITE.duplicate(true)]


func _starting(seed_value: int) -> StartingResourceGenerator:
	return Starting.new(seed_value, _definitions(), CrashSite.protected_bounds(), CrashSite.SHIP_REFERENCE)


# Independent world-space geometry: do not ask the generator to validate itself.
func _bounds(member: Dictionary) -> Rect2:
	return Rect2(Vector2(member.anchor_cells.position) * 32.0, Vector2(member.anchor_cells.size) * 32.0)


func _axis_distance(a: Rect2, b: Rect2) -> float:
	var delta := (a.get_center() - b.get_center()).abs()
	return maxf(delta.x, delta.y)


func _valid_locations(locations: Array, context: String) -> bool:
	var errors: Array[String] = []
	for location: Variant in locations:
		var error: String = Descriptors.location_error(location)
		if not error.is_empty():
			errors.append(error)
	return _expect(errors, [], context + " descriptor validity")


func _starting_guarantees() -> void:
	for seed_value: int in [26026, -79]:
		var context := "starting seed=%d" % seed_value
		var source := _starting(seed_value)
		if not _ready(source, context):
			continue
		var result: Dictionary = source.reservations()
		if not _ok(result, context) or not _valid_locations(result.locations, context):
			continue
		var counts := {"ferrite": 0, "carbite": 0, "cuprite": 0}
		var anchors: Array[String] = []
		var distances: Array[String] = []
		var protection: Array[String] = []
		var within_distance: Array[String] = []
		var within_clearance: Array[String] = []
		var between_clearance: Array[String] = []
		var previous: Array[Dictionary] = []
		for location: Dictionary in result.locations:
			var siblings: Array[Dictionary] = []
			for member: Dictionary in location.deposits:
				counts[member.resource_type] = counts.get(member.resource_type, 0) + 1
				var label: String = member.deposit_id
				var bounds := _bounds(member)
				if member.anchor_cells.size != Vector2i(4, 4):
					anchors.append("%s size=%s" % [label, member.anchor_cells.size])
				var distance := bounds.get_center().distance_to(CrashSite.SHIP_REFERENCE)
				if distance < 384.0 or distance > 2304.0:
					distances.append("%s distance=%s" % [label, distance])
				for blocked: Rect2 in CrashSite.protected_bounds():
					if bounds.grow(64.0).intersects(blocked, true):
						protection.append("%s intersects=%s" % [label, blocked])
				for other: Dictionary in siblings:
					var other_bounds := _bounds(other)
					var separation := bounds.get_center().distance_to(other_bounds.get_center())
					if separation < 320.0 or separation > 704.0:
						within_distance.append("%s / %s distance=%s" % [label, other.deposit_id, separation])
					# 128 anchor + two 64 margins + 32 gap; contact fails.
					if _axis_distance(bounds, other_bounds) <= 288.0:
						within_clearance.append("%s / %s axis=%s" % [label, other.deposit_id, _axis_distance(bounds, other_bounds)])
				for other: Dictionary in previous:
					# Different locations: 128 + two 64 margins + 448 gap.
					if _axis_distance(bounds, _bounds(other)) <= 704.0:
						between_clearance.append("%s / %s axis=%s" % [label, other.deposit_id, _axis_distance(bounds, _bounds(other))])
				siblings.append(member)
			previous.append_array(location.deposits)
		_expect(counts, {"ferrite": 3, "carbite": 2, "cuprite": 2}, context + " complete member counts")
		_expect(anchors, [], context + " 4x4 anchors")
		_expect(distances, [], context + " center distance in [384,2304]")
		_expect(protection, [], context + " authored visual clearance")
		_expect(within_distance, [], context + " within-group distance in [320,704]")
		_expect(within_clearance, [], context + " within-group axis clearance >288")
		_expect(between_clearance, [], context + " between-location axis clearance >704")


func _deterministic_reconstruction() -> void:
	for seed_value: int in [42, -79]:
		var context := "reconstruction seed=%d" % seed_value
		var definitions := _definitions()
		definitions.reverse()
		var forward := Ordinary.new(seed_value, _definitions(), [])
		var reverse := Ordinary.new(seed_value, definitions, [])
		var forward_ready := _ready(forward, context + " forward")
		var reverse_ready := _ready(reverse, context + " reverse")
		if not forward_ready or not reverse_ready:
			continue
		var expected: Dictionary = {}
		var total: int = 0
		for owner: Vector2i in OWNERS:
			var result: Dictionary = forward.region(owner)
			if _ok(result, context + " owner=%s forward" % owner):
				expected[owner] = result
				total += result.locations.size()
		_expect(total > 0, true, context + " nonempty ordinary corpus; locations=%d" % total)
		var owners: Array = OWNERS.duplicate()
		owners.reverse()
		for owner: Vector2i in owners:
			var result: Dictionary = reverse.region(owner)
			if _ok(result, context + " owner=%s reverse" % owner) and expected.has(owner):
				_expect(result, expected[owner], context + " owner=%s full descriptors" % owner)
		var first := _starting(seed_value)
		var second := Starting.new(seed_value, definitions, CrashSite.protected_bounds(), CrashSite.SHIP_REFERENCE)
		var first_ready := _ready(first, context + " starting first")
		var second_ready := _ready(second, context + " starting second")
		if not first_ready or not second_ready:
			continue
		var first_layout: Dictionary = first.reservations()
		var second_layout: Dictionary = second.reservations()
		var first_ok := _ok(first_layout, context + " starting first")
		var second_ok := _ok(second_layout, context + " starting second")
		if first_ok and second_ok:
			_expect(second_layout, first_layout, context + " complete starting reconstruction")


func _stable_identities() -> void:
	var seed_value: int = 26026
	var context := "identity seed=%d" % seed_value
	var source := _starting(seed_value)
	if not _ready(source, context):
		return
	var result: Dictionary = source.reservations()
	if not _ok(result, context) or not _valid_locations(result.locations, context):
		return
	_identity_round_trips(source, result.locations, seed_value, "starting-v2-2", 4, 11)
	if not result.locations.is_empty():
		var identity: String = result.locations[0].deposits[0].deposit_id
		for rejected_id: String in [identity.replace(":26026:", ":026026:"),
				identity.replace(":26026:", ":26027:"), identity.replace("starting-v2-2", "starting-v2-1")]:
			var rejected: Dictionary = source.descriptor_by_id(rejected_id)
			_expect(rejected.get("ok"), false, context + " reject " + rejected_id)
			_expect(rejected.has("descriptor"), false, context + " no rejected descriptor " + rejected_id)
	var ordinary := Ordinary.new(42, _definitions(), [])
	if not _ready(ordinary, "identity seed=42 ordinary"):
		return
	var locations: Array = []
	for owner: Vector2i in OWNERS:
		var owned: Dictionary = ordinary.region(owner)
		if _ok(owned, "identity seed=42 owner=%s" % owner):
			locations.append_array(owned.locations)
	if _valid_locations(locations, "identity seed=42 ordinary"):
		_identity_round_trips(ordinary, locations, 42, "ordinary-v2-1", 0, 4)


func _identity_round_trips(source: OrdinaryResourceGenerator, locations: Array,
		seed_value: int, policy: String, first_slot: int, end_slot: int) -> void:
	var context := "identity seed=%d policy=%s" % [seed_value, policy]
	var actual_locations: Array = []
	var expected_locations: Array = []
	var actual_members: Array = []
	var expected_members: Array = []
	var resolved_locations: Array = []
	var resolved_members: Array = []
	var expected_resolved_locations: Array = []
	var expected_resolved_members: Array = []
	for location: Dictionary in locations:
		var point: Vector2 = Vector2(location.deposits[0].anchor_cells.position) * 32.0
		var owner := Vector2i(floori(point.x / 1536.0), floori(point.y / 1536.0))
		var identity := "resource-location:%s:%d:%d:%d:%d" % [policy, seed_value, owner.x, owner.y, location.location_slot]
		actual_locations.append([location.schema_version, location.generation_policy, location.world_seed,
			location.owner_region, location.location_slot >= first_slot and location.location_slot < end_slot, location.location_id])
		expected_locations.append([1, policy, seed_value, owner, true, identity])
		resolved_locations.append(source.descriptor_by_id(location.location_id))
		expected_resolved_locations.append({"ok": true, "descriptor": location})
		for index in range(location.deposits.size()):
			var member: Dictionary = location.deposits[index]
			var deposit_id := "resource:%s:%d:%d:%d:%d:%d" % [policy, seed_value, owner.x, owner.y, location.location_slot, index]
			actual_members.append([member.member_index, member.location_id, member.resource_type, member.deposit_id])
			expected_members.append([index, identity, location.resource_type, deposit_id])
			resolved_members.append(source.descriptor_by_id(member.deposit_id))
			expected_resolved_members.append({"ok": true, "descriptor": member})
	_expect(actual_locations.is_empty(), false, context + " nonempty identity corpus")
	_expect(actual_locations, expected_locations, context + " canonical location fields")
	_expect(actual_members, expected_members, context + " canonical member fields")
	_expect(resolved_locations, expected_resolved_locations, context + " location round trips")
	_expect(resolved_members, expected_resolved_members, context + " member round trips")


func _boundary_queries() -> void:
	var context := "boundary seed=42"
	for vector in [[Vector2(-1, -1536), Vector2i(-1, -1)],
			[Vector2(-1537, 1535), Vector2i(-2, 0)],
			[Vector2(1536, 3072), Vector2i(1, 2)], [Vector2.ZERO, Vector2i.ZERO]]:
		_expect(Ordinary.owner_at(vector[0]), vector[1], context + " point=%s" % vector[0])
	# First anchor belongs to owner zero; the second lies entirely in owner (1,0).
	var made: Dictionary = Descriptors.create_location("ordinary-v2-1", 42, Vector2i.ZERO, 0,
		&"cuprite", [Rect2i(47, 0, 4, 4), Rect2i(59, 0, 4, 4)])
	if not _ok(made, context + " fixture"):
		return
	var source := CandidateFixture.new(42, _definitions(), [])
	if not _ready(source, context):
		return
	source.raw = {Vector2i.ZERO: {"location": made.location, "priority": 0}}
	for owner: Vector2i in [Vector2i.ZERO, Vector2i(1, 0)]:
		var owned: Dictionary = source.region(owner)
		if _ok(owned, context + " owner=%s" % owner):
			_expect(owned.locations, [made.location] if owner == Vector2i.ZERO else [], context + " unique owner=%s" % owner)
	var crossing: Dictionary = made.location.deposits[1]
	var point: Vector2 = _bounds(crossing).get_center()
	var found: Dictionary = source.query(Rect2(point, Vector2.ZERO))
	if _ok(found, context + " crossing point=%s" % point):
		_expect(found.deposits, [crossing], context + " crossing member once with original ID")
	var whole: Dictionary = source.query(Rect2(1440, -64, 640, 256))
	if _ok(whole, context + " whole location"):
		_expect(whole.deposits, made.location.deposits, context + " complete query without duplicates")
	_expect(source.descriptor_by_id(crossing.deposit_id), {"ok": true, "descriptor": crossing}, context + " crossing ID round trip")


func _atomic_conflicts() -> void:
	var context := "conflict seed=42"
	# Intentionally synthetic resolver fixture, not generated spatial ownership:
	# all first anchors naturally lie in owner (0,0), but B/C declare (1,0)/(2,0)
	# to exercise the raw-competitor halo. Only candidate supply is overridden.
	var made: Array[Dictionary] = [
		Descriptors.create_location("ordinary-v2-1", 42, Vector2i.ZERO, 0, &"cuprite",
			[Rect2i(0, 0, 4, 4), Rect2i(12, 0, 4, 4), Rect2i(4, 12, 4, 4)]),
		Descriptors.create_location("ordinary-v2-1", 42, Vector2i(1, 0), 0, &"ferrite", [Rect2i(18, 0, 4, 4)]),
		Descriptors.create_location("ordinary-v2-1", 42, Vector2i(2, 0), 0, &"ferrite", [Rect2i(36, 0, 4, 4)]),
	]
	var valid: bool = true
	for index in range(made.size()):
		var admitted := _ok(made[index], context + " fixture=%d" % index)
		valid = valid and admitted
	if not valid:
		return
	var a: Dictionary = made[0].location
	var b: Dictionary = made[1].location
	var c: Dictionary = made[2].location
	# Validate the fixture's distinguishing geometry independently of _conflicts.
	_expect(_axis_distance(_bounds(a.deposits[1]), _bounds(b.deposits[0])) <= 704.0, true, context + " A/B conflict")
	_expect(_axis_distance(_bounds(b.deposits[0]), _bounds(c.deposits[0])) <= 704.0, true, context + " B/C conflict")
	var endpoint_clear: bool = true
	for member: Dictionary in a.deposits:
		endpoint_clear = endpoint_clear and _axis_distance(_bounds(member), _bounds(c.deposits[0])) > 704.0
	_expect(endpoint_clear, true, context + " A/C independent endpoints")
	# Cover C's visual bounds AND reach its synthetic declared owner in the plan.
	var query_area := Rect2(-64, -64, 2496, 640)
	_expect(query_area.encloses(Ordinary.visual_bounds(c.deposits[0])), true,
		context + " query covers C visual bounds")
	for reverse_order: bool in [false, true]:
		var source := CandidateFixture.new(42, _definitions(), [])
		if not _ready(source, context + " reverse=%s" % reverse_order):
			continue
		source.raw = {Vector2i.ZERO: {"location": a, "priority": 2},
			Vector2i(1, 0): {"location": b, "priority": 1}, Vector2i(2, 0): {"location": c, "priority": 0}}
		var owners: Array[Vector2i] = [Vector2i.ZERO, Vector2i(1, 0), Vector2i(2, 0)]
		if reverse_order:
			owners.reverse()
		for owner: Vector2i in owners:
			var result: Dictionary = source.region(owner)
			if _ok(result, context + " owner=%s reverse=%s" % [owner, reverse_order]):
				_expect(result.locations, [c] if owner == Vector2i(2, 0) else [], context + " accepted owner=%s reverse=%s" % [owner, reverse_order])
		var plan: Dictionary = source.query_owners(query_area)
		if _ok(plan, context + " query plan reverse=%s" % reverse_order):
			_expect(plan.owners.has(c.owner_region), true,
				context + " declared C owner=%s in plan=%s reverse=%s" % [c.owner_region, plan.owners, reverse_order])
		var queried: Dictionary = source.query(query_area)
		if _ok(queried, context + " query reverse=%s" % reverse_order):
			_expect(queried.deposits, c.deposits, context + " only C query reverse=%s" % reverse_order)
		for member: Dictionary in a.deposits:
			_expect(source.descriptor_by_id(member.deposit_id).get("ok"), false, context + " all A members rejected id=%s reverse=%s" % [member.deposit_id, reverse_order])


func _definition_and_copy_isolation() -> void:
	var context := "isolation seed=42"
	var empty := Ordinary.new(42, [], [])
	_expect(empty.is_ready(), false, context + " empty definitions")
	var duplicate := Ordinary.new(42, [FERRITE, FERRITE], [])
	_expect(duplicate.is_ready(), false, context + " duplicate definitions")
	var unsupported := _definitions()
	unsupported[0].geological_preferences = {"invented_geology": 2.0}
	var invalid := Ordinary.new(42, unsupported, [])
	_expect(invalid.is_ready(), false, context + " unsupported geology")
	var definitions := _definitions()
	var source := Ordinary.new(42, definitions, [])
	var reference := Ordinary.new(42, _definitions(), [])
	var source_ready := _ready(source, context + " snapshot")
	var reference_ready := _ready(reference, context + " reference")
	if not source_ready or not reference_ready:
		return
	# Mutate before the first region generation: no warm cache can hide aliasing.
	definitions[0].abundance_weight = 900.0
	definitions[0].geological_preferences["terrain_geology"] = 50.0
	for definition: WorldResourceDefinition in definitions:
		definition.resource_id = &"caller_edit"
	definitions.reverse()
	var sample: Dictionary = {}
	for owner: Vector2i in OWNERS:
		var actual: Dictionary = source.region(owner)
		var expected: Dictionary = reference.region(owner)
		var actual_ok := _ok(actual, context + " owner=%s snapshot" % owner)
		var expected_ok := _ok(expected, context + " owner=%s reference" % owner)
		if not actual_ok or not expected_ok:
			continue
		_expect(actual, expected, context + " owner=%s construction snapshot" % owner)
		if sample.is_empty() and not expected.locations.is_empty():
			sample = {"owner": owner, "actual": actual, "expected": expected}
	if not _expect(sample.is_empty(), false, context + " nonempty copy corpus"):
		return
	if not _valid_locations(sample.expected.locations, context + " reference") \
			or not _valid_locations(sample.actual.locations, context + " snapshot"):
		return
	var member: Dictionary = sample.expected.locations[0].deposits[0]
	sample.actual.locations[0].deposits[0].anchor_cells = Rect2i(100, 100, 4, 4)
	sample.actual.locations[0].deposits[0].presentation["variant_id"] = "caller_edit"
	_expect(source.region(sample.owner), sample.expected, context + " owner=%s nested region copy" % sample.owner)
	var area := _bounds(member).grow(64.0)
	var queried: Dictionary = source.query(area)
	var expected_query: Dictionary = reference.query(area)
	var query_ok := _ok(queried, context + " query")
	var expected_query_ok := _ok(expected_query, context + " reference query")
	if query_ok and expected_query_ok:
		_expect(queried, expected_query, context + " original query")
		if not _expect(queried.deposits.is_empty(), false, context + " nonempty query copy corpus"):
			return
		queried.deposits[0].presentation["variant_id"] = "query_edit"
		_expect(source.query(area), expected_query, context + " nested query copy")
	var resolved: Dictionary = source.descriptor_by_id(member.deposit_id)
	if _expect(resolved, {"ok": true, "descriptor": member}, context + " ID before mutation"):
		resolved.descriptor.presentation["variant_id"] = "identity_edit"
		_expect(source.descriptor_by_id(member.deposit_id), {"ok": true, "descriptor": member}, context + " nested ID copy")
	var starting := _starting(26026)
	if not _ready(starting, "isolation seed=26026 reservations"):
		return
	var layout: Dictionary = starting.reservations()
	if not _ok(layout, "isolation seed=26026 reservations") \
			or not _valid_locations(layout.locations, "isolation seed=26026 reservations"):
		return
	if not _expect(layout.locations.is_empty(), false, "isolation seed=26026 nonempty reservations"):
		return
	var baseline := layout.duplicate(true)
	layout.locations[0].deposits[0].presentation["variant_id"] = "reservation_edit"
	_expect(starting.reservations(), baseline, "isolation seed=26026 nested reservation copy")
