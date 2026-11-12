extends SceneTree
## Behavioral assertions AUTHORED ONLY. No runner authorizes this script.
const Generator = preload("res://scenes/world/ordinary_resource_generator.gd")
const Descriptors = preload("res://scenes/world/resource_generation_descriptors.gd")
const Definition = preload("res://scenes/world/world_resource_definition.gd")
const FERRITE = preload("res://scenes/world/resource_definitions/v2/ferrite.tres")
const CARBITE = preload("res://scenes/world/resource_definitions/v2/carbite.tres")
const CUPRITE = preload("res://scenes/world/resource_definitions/v2/cuprite.tres")
var _failures: int = 0
var _checks: int = 0


class ConflictFixture:
	extends "res://scenes/world/ordinary_resource_generator.gd"
	var raw: Dictionary = {}

	func _candidate(owner: Vector2i, slot: int) -> Dictionary:
		return raw.get(owner, {}) if slot == 0 else {}


func _check(condition: bool, label: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		printerr("FAIL: " + label)


func _definitions() -> Array[WorldResourceDefinition]:
	return [FERRITE.duplicate(true), CARBITE.duplicate(true), CUPRITE.duplicate(true)]


func _generator(seed_value: int = 42) -> OrdinaryResourceGenerator:
	return Generator.new(seed_value, _definitions(), [])


func _boundaries_and_admission() -> void:
	for vector in [[Vector2.ZERO, Vector2i.ZERO],
			[Vector2(-1, -1536), Vector2i(-1, -1)],
			[Vector2(1536, 3072), Vector2i(1, 2)],
			[Vector2(-1537, 1535), Vector2i(-2, 0)]]:
		_check(Generator.owner_at(vector[0]) == vector[1], "negative and exact region boundaries")
	_check(Generator.REGION_SIZE == 24 * WorldCoordinates.TERRAIN_SIZE, "locked terrain region correction")
	_check(Generator.REGION_SIZE == 48 * WorldCoordinates.CONSTRUCTION_SIZE, "construction region dimensions")
	_check(not Generator.new(1, [], []).is_ready(), "empty definitions rejected")
	_check(not Generator.new(1, [FERRITE, FERRITE], []).is_ready(), "duplicate definitions rejected")
	_check(not Generator.new(1, _definitions(), [], "v2").is_ready(), "unsupported policy rejected")
	var definitions := _definitions()
	definitions[0].allowed_environments = [&"invented_biome"]
	_check(not Generator.new(1, definitions, []).is_ready(), "unavailable environment fails closed")
	definitions = _definitions()
	definitions[0].geological_preferences = {"invented_geology": 2.0}
	_check(not Generator.new(1, definitions, []).is_ready(), "unsupported geology rejected")
	for weight in [0.0, -1.0, INF, NAN]:
		definitions = _definitions()
		definitions[0].abundance_weight = weight
		_check(not Generator.new(1, definitions, []).is_ready(), "invalid abundance rejected")
	definitions = _definitions()
	definitions[0].abundance_weight = 1.7e308
	definitions[0].geological_preferences = {"terrain_geology": 2.0}
	_check(not Generator.new(1, definitions, []).is_ready(), "combined weight overflow rejected")
	_check(not Generator.new(1, _definitions(), [Rect2(0, 0, -1, 1)]).is_ready(), "invalid protection rejected")


func _reconstruction() -> void:
	var groups: Dictionary = {}
	var types: Dictionary = {}
	var cross_region := false
	for seed_value in [0, 42, -79, -9223372036854775807]:
		var first := _generator(seed_value)
		var second := _generator(seed_value)
		var owners: Array[Vector2i] = []
		for y in range(-4, 5):
			for x in range(-4, 5):
				owners.append(Vector2i(x, y))
		var expected: Dictionary = {}
		for owner in owners:
			expected[owner] = first.region(owner)
		owners.reverse()
		for owner in owners:
			var actual := second.region(owner)
			_check(actual == expected[owner], "same seed reverse query order and cache eviction")
			for location: Dictionary in actual.locations:
				groups[location.deposits.size()] = true
				types[location.resource_type] = true
				_check(Descriptors.location_error(location).is_empty(), "foundation schema compatible complete membership")
				_check(first.descriptor_by_id(location.location_id).descriptor == location, "stable location identity reconstruction")
				for member: Dictionary in location.deposits:
					_check(first.descriptor_by_id(member.deposit_id).descriptor == member, "stable deposit identity reconstruction")
					var area := Generator.visual_bounds(member)
					if Generator.owner_at(Generator.anchor_bounds(member).position) != owner:
						cross_region = true
						var queried := first.query(area)
						var seen: Dictionary = {}
						for found: Dictionary in queried.deposits:
							_check(not seen.has(found.deposit_id), "cross-region query deduplication")
							seen[found.deposit_id] = true
						_check(seen.has(member.deposit_id), "cross-region ownership retained")
				for other_owner in [owner, owner + Vector2i.RIGHT, owner + Vector2i.DOWN]:
					for other: Dictionary in first.region(other_owner).locations:
						if location.location_id != other.location_id:
							_check(not Generator._conflicts(location, other), "accepted logical and visual separation")
		_check(first._cache.size() <= Generator.CACHE_LIMIT, "bounded FIFO cache")
	_check(groups.size() == 3, "accepted single pair triple coverage")
	_check(types.size() == 3, "deterministic multi-resource selection coverage")
	_check(cross_region, "cross-region fixture coverage")


func _synthetic_conflicts() -> void:
	var generator := _generator()
	var a := Descriptors.create_location(Generator.POLICY, 42, Vector2i.ZERO, 0,
		&"cuprite", [Rect2i(0, 0, 4, 4), Rect2i(12, 0, 4, 4), Rect2i(4, 12, 4, 4)]).location
	var b := Descriptors.create_location(Generator.POLICY, 42, Vector2i.ONE, 0,
		&"ferrite", [Rect2i(12, 0, 4, 4)]).location
	_check(generator._eligible(a), "valid organic triple spacing")
	_check(Generator._conflicts(a, b), "one member conflict rejects complete triple")
	var triple := {"location": a, "priority": 100}
	var winner := {"location": b, "priority": 0}
	_check(Generator._precedes(winner, triple), "deterministic priority")
	winner.priority = 100
	_check(Generator._precedes(triple, winner) != Generator._precedes(winner, triple), "stable tie breaking")
	var protected_generator := Generator.new(42, _definitions(), [Generator.visual_bounds(a.deposits[2])])
	_check(not protected_generator._eligible(a), "authored protection rejects complete group")
	var anchors: Array[Rect2i] = [Rect2i(0, 0, 4, 4), Rect2i(5, 0, 4, 4)]
	var tight := Descriptors.create_location(Generator.POLICY, 42, Vector2i.ZERO, 0, &"cuprite", anchors).location
	_check(not generator._eligible(tight), "conservative visual clearance independent of logical overlap")
	# A conflicts with B; B conflicts with C; A does not conflict with C.
	# B loses to C but must still reject A. A's full triple is never trimmed.
	var middle := Descriptors.create_location(Generator.POLICY, 42, Vector2i(1, 0), 0,
		&"ferrite", [Rect2i(18, 0, 4, 4)]).location
	var last := Descriptors.create_location(Generator.POLICY, 42, Vector2i(2, 0), 0,
		&"ferrite", [Rect2i(36, 0, 4, 4)]).location
	var fixture := ConflictFixture.new(42, _definitions(), [])
	fixture.raw = {Vector2i.ZERO: {"location": a, "priority": 2},
		Vector2i(1, 0): {"location": middle, "priority": 1},
		Vector2i(2, 0): {"location": last, "priority": 0}}
	_check(not Generator._conflicts(a, last), "raw chain has nonadjacent endpoints")
	_check(fixture.region(Vector2i.ZERO).locations.is_empty(), "atomic rejection by losing raw competitor")
	_check(fixture.region(Vector2i(1, 0)).locations.is_empty(), "raw middle loses")
	_check(fixture.region(Vector2i(2, 0)).locations == [last], "two-region halo winner survives")
	var reverse := ConflictFixture.new(42, _definitions(), [])
	reverse.raw = fixture.raw.duplicate(true)
	for owner in [Vector2i(2, 0), Vector2i(1, 0), Vector2i.ZERO]:
		_check(reverse.region(owner) == fixture.region(owner), "synthetic raw chain reverse order")
	for slot in range(Generator.CANDIDATE_SLOTS):
		var candidate := generator._candidate(Vector2i.ZERO, slot)
		if not candidate.is_empty():
			var blocker := Generator.new(42, _definitions(), [Generator.visual_bounds(candidate.location.deposits.back())])
			_check(blocker._candidate(Vector2i.ZERO, slot).is_empty(), "raw group never silently trimmed")


func _bounds_and_isolation() -> void:
	var generator := _generator()
	for area in [Rect2(0, 0, -1, 1), Rect2(0, 0, INF, 1), Rect2(NAN, 0, 1, 1),
			Rect2(0, 0, 1e30, 1), Rect2(0, 0, 1536 * 9, 1536 * 9)]:
		_check(not generator.query(area).ok, "invalid or oversized queries reject atomically")
	_check(generator._cache.is_empty(), "rejected queries do no generation")
	_check(generator.query(Rect2(Vector2.ZERO, Vector2.ZERO)).ok, "bounded point query")
	_check(not generator.region(Vector2i(8193, 0)).ok, "unsupported owner rejected")
	for identity in ["resource:ordinary-v2-1:42:-9223372036854775808:0:0:0",
			"resource:ordinary-v2-1:042:0:0:0:0", "resource:v2:42:0:0:0:0",
			"resource:ordinary-v2-1:42:0:0:4:0", "resource:ordinary-v2-1:42:0:0:0:3"]:
		_check(not generator.descriptor_by_id(identity).ok, "invalid identity rejected")
	var definitions := _definitions()
	var copied := Generator.new(42, definitions, [])
	definitions[0].abundance_weight = 900.0
	definitions[0].presentation_catalog = "res://synthetic/different.json"
	for y in range(-2, 3):
		for x in range(-2, 3):
			var owner := Vector2i(x, y)
			var original := copied.region(owner)
			_check(original == generator.region(owner), "definition snapshot and artwork independence")
			original.locations.clear()
			_check(copied.region(owner) == generator.region(owner), "returned descriptors cannot mutate cache")
	# No machine, player, visual, chunk or authoritative simulation inputs exist.


func _initialize() -> void:
	_boundaries_and_admission()
	_reconstruction()
	_synthetic_conflicts()
	_bounds_and_isolation()
	print("Ordinary generator assertions: %d checks, %d failures" % [_checks, _failures])
	quit(1 if _failures else 0)
