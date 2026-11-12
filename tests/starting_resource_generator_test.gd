extends SceneTree
## Authored only. Not dispatched by any approved runner; no runtime PASS claimed.

const Generator = preload("res://scenes/world/starting_resource_generator.gd")
const Ordinary = preload("res://scenes/world/ordinary_resource_generator.gd")
const Descriptors = preload("res://scenes/world/resource_generation_descriptors.gd")
const Context = preload("res://scenes/world/resource_generation_crash_site.gd")
const Diagnostics = preload("res://scenes/world/resource_migration_diagnostics.gd")
const FERRITE = preload("res://scenes/world/resource_definitions/v2/ferrite.tres")
const CARBITE = preload("res://scenes/world/resource_definitions/v2/carbite.tres")
const CUPRITE = preload("res://scenes/world/resource_definitions/v2/cuprite.tres")
var _failures: int = 0
var _checks: int = 0


class RawFixture:
	extends "res://scenes/world/starting_resource_generator.gd"
	var raw: Dictionary = {}

	func _candidate(owner: Vector2i, slot: int) -> Dictionary:
		var candidate: Dictionary = raw.get(owner, {}) if slot == 0 else {}
		if candidate.is_empty() or not _ordinary_allowed(candidate.location, owner, slot):
			return {}
		return candidate


func _check(condition: bool, label: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		printerr("FAIL: " + label)


func _definitions() -> Array[WorldResourceDefinition]:
	return [FERRITE.duplicate(true), CARBITE.duplicate(true), CUPRITE.duplicate(true)]


func _generator(seed_value: int) -> StartingResourceGenerator:
	return Generator.new(seed_value, _definitions(), Context.protected_bounds(), Context.SHIP_REFERENCE)


func _layouts() -> void:
	var positions: Dictionary = {}
	var groupings: Dictionary = {}
	var cross_region := false
	for seed_value in [0, 1, 42, -79, 7341, -9223372036854775807, 9223372036854775807]:
		var generator := _generator(seed_value)
		_check(generator.is_ready(), "representative seed has valid complete layout")
		if not generator.is_ready():
			continue
		var layout := generator.reservations()
		_check(layout.attempts >= 1 and layout.attempts <= Generator.ARRANGEMENT_BUDGET, "finite search budget")
		_check(layout == _generator(seed_value).reservations(), "same seed complete reconstruction")
		_check(generator._arrangement_valid(layout.locations), "complete-arrangement validation")
		var counts := {"ferrite": 0, "carbite": 0, "cuprite": 0}
		var anchors: Array[Rect2i] = []
		var sizes: Array[int] = []
		for location: Dictionary in layout.locations:
			counts[location.resource_type] += location.deposits.size()
			sizes.append(location.deposits.size())
			_check(Descriptors.location_error(location).is_empty(), "foundation schema unchanged")
			_check(generator.descriptor_by_id(location.location_id).descriptor == location, "stable reserved location identity")
			_check(location.owner_region == Ordinary.owner_at(Ordinary.anchor_bounds(location.deposits[0]).position), "one floor-derived owner")
			for member: Dictionary in location.deposits:
				anchors.append(member.anchor_cells)
				_check(generator.descriptor_by_id(member.deposit_id).descriptor == member, "stable reserved identity")
				var distance := Ordinary.anchor_bounds(member).get_center().distance_to(Context.SHIP_REFERENCE)
				_check(distance >= 384 and distance <= 2304, "anchor-center starting distance targets")
				for protection in Context.protected_bounds():
					_check(not Ordinary.visual_bounds(member).intersects(protection, true), "ship hatch construction and visual clearance")
				var query := generator.query(Ordinary.visual_bounds(member))
				var ids: Dictionary = {}
				for found: Dictionary in query.deposits:
					_check(not ids.has(found.deposit_id), "cross-region deduplication")
					ids[found.deposit_id] = true
				_check(ids.has(member.deposit_id), "reserved member found across boundaries")
				cross_region = cross_region or Ordinary.owner_at(Ordinary.anchor_bounds(member).position) != location.owner_region
		_check(counts == Generator.REQUIRED, "exact seven counts")
		positions[str(anchors)] = true
		groupings[str(sizes)] = true
		# Mutating returned data cannot relocate or deactivate any reservation.
		layout.locations[0].deposits[0].anchor_cells = Rect2i(0, 0, 4, 4)
		_check(generator.reservations() == _generator(seed_value).reservations(), "snapshot and activation independence")
	_check(positions.size() > 1 and groupings.size() > 1, "seed position and grouping variation")
	_check(cross_region, "cross-region starting group coverage")


func _failures_and_admission() -> void:
	var blocked := Generator.new(42, _definitions(), [Rect2(-10000, -10000, 20000, 20000)], Context.SHIP_REFERENCE)
	var failure := blocked.reservations()
	_check(not failure.ok and failure.attempts == Generator.ARRANGEMENT_BUDGET \
		and blocked._reservations.is_empty() and failure.error.contains("exhausted"), "explicit bounded exhaustion")
	_check(not blocked.region(Vector2i.ZERO).ok and not blocked.query(Rect2()).ok, "failure publishes no partial world")
	_check(not Generator.new(1, [FERRITE, CARBITE], [], Vector2.ZERO).is_ready(), "missing guaranteed definition rejected")
	_check(not Generator.new(1, _definitions(), [], Vector2(NAN, 0)).is_ready(), "invalid ship rejected")
	_check(not Generator.new(1, _definitions(), [], Vector2(1e30, 0)).is_ready(), "out-of-domain ship rejected")
	_check(not Generator.new(1, _definitions(), [], Vector2.ZERO, Ordinary.POLICY).is_ready(), "policy explicit")
	var generator := _generator(42)
	if not generator.is_ready():
		return
	var layout: Array[Dictionary] = generator.reservations().locations
	var incomplete := layout.duplicate(true)
	incomplete.pop_back()
	_check(not generator._arrangement_valid(incomplete), "whole arrangement rejection")
	var overlap := layout.duplicate(true)
	overlap[1].deposits[0].anchor_cells = overlap[0].deposits[0].anchor_cells
	_check(not generator._arrangement_valid(overlap), "all seven validated together")
	var protected_layout := layout.duplicate(true)
	protected_layout[0].deposits[0].anchor_cells = Rect2i(-14, -8, 4, 4)
	_check(not generator._arrangement_valid(protected_layout), "authored ship protection cannot be overridden")
	var boundary := Generator.new(42, _definitions(), [], Vector2(-1536, -1536))
	_check(boundary.is_ready(), "negative exact-boundary ship")
	for identity in ["resource:starting-v2-1:042:0:0:4:0", "resource:ordinary-v2-1:42:0:0:0:0",
			"resource:starting-v2-1:42:0:0:11:0", "resource:starting-v2-1:42:0:0:4:3"]:
		_check(not generator.descriptor_by_id(identity).ok, "canonical identity admission")


func _transition_and_priority() -> void:
	_check(Generator.transition_density(0) == 0 and Generator.transition_density(1536) == 0 \
		and Generator.transition_density(2304) == 0.5 and Generator.transition_density(3072) == 1 \
		and Generator.transition_density(100000) == 1, "transition endpoints and midpoint")
	var generator := _generator(42)
	if not generator.is_ready():
		return
	var expected: Dictionary = {}
	var owners: Array[Vector2i] = []
	for y in range(-3, 4):
		for x in range(-3, 4):
			var owner := Vector2i(x, y)
			owners.append(owner)
			expected[owner] = generator.region(owner)
			for location: Dictionary in expected[owner].locations:
				if location.location_slot >= Generator.START_SLOT:
					continue
				_check(generator.descriptor_by_id(location.location_id).descriptor == location, "versioned ordinary identity reconstruction")
				for reservation: Dictionary in generator.reservations().locations:
					_check(not Ordinary._conflicts(location, reservation), "ordinary cannot displace inactive reservations")
	owners.reverse()
	var reverse := _generator(42)
	for owner in owners:
		_check(reverse.region(owner) == expected[owner], "reverse query order and cache eviction")
	# Fixed raw chain isolates reservation admission from ordinary competition.
	var fixture := RawFixture.new(42, _definitions(), [], Vector2(-10000, -10000))
	var a := Descriptors.create_location(Generator.STARTING_POLICY, 42, Vector2i.ZERO, 0,
		&"cuprite", [Rect2i(0, 0, 4, 4), Rect2i(12, -2, 4, 4), Rect2i(4, 12, 4, 4)]).location
	var b := Descriptors.create_location(Generator.STARTING_POLICY, 42, Vector2i(1, 0), 0,
		&"ferrite", [Rect2i(30, 0, 4, 4)]).location
	var reservation := Descriptors.create_location(Generator.STARTING_POLICY, 42, Vector2i(-1, 0), 4,
		&"carbite", [Rect2i(-18, 0, 4, 4)]).location
	fixture._reservations = [reservation] # Synthetic test only; no production setter.
	fixture.raw = {Vector2i.ZERO: {"location": a, "priority": 0},
		Vector2i(1, 0): {"location": b, "priority": 100}}
	_check(Ordinary._conflicts(a, reservation) and Ordinary._conflicts(a, b) \
		and not Ordinary._conflicts(b, reservation), "raw chain geometry")
	_check(fixture._candidate(Vector2i.ZERO, 0).is_empty(), "inactive reservation blocks ordinary triple")
	_check(fixture.region(Vector2i(1, 0)).locations == [b], "removed raw competitor cannot suppress survivor")
	_check(fixture.region(Vector2i.ZERO).locations.is_empty(), "ordinary triple atomically rejected")
	# Outside transition and reservation reach, retained v2-1 raw geometry is exact.
	var ordinary := Ordinary.new(42, _definitions(), Context.protected_bounds())
	for x in range(8, 12):
		var owner := Vector2i(x, 8)
		var old := ordinary.region(owner)
		var current := generator.region(owner)
		_check(old.locations.size() == current.locations.size(), "distant abundance unchanged")
		for index in range(old.locations.size()):
			_check(old.locations[index].resource_type == current.locations[index].resource_type,
				"distant geological selection unchanged")
			for member_index in range(old.locations[index].deposits.size()):
				_check(old.locations[index].deposits[member_index].anchor_cells == current.locations[index].deposits[member_index].anchor_cells,
					"distant grouping geometry unchanged")


func _diagnostics() -> void:
	var legacy_polygon := PackedVector2Array([Vector2(0, 0), Vector2(128, 0), Vector2(128, 128), Vector2(0, 128)])
	var snapshot := Diagnostics.legacy_snapshot("legacy-fixture", legacy_polygon, Rect2(-32, -32, 192, 192))
	_check(snapshot.ok, "legacy polygon snapshot admission")
	var location := Descriptors.create_location(Generator.STARTING_POLICY, 42, Vector2i.ZERO, 4,
		&"ferrite", [Rect2i(0, 0, 4, 4)]).location
	var legacy: Array[Dictionary] = [snapshot.snapshot]
	var locations: Array[Dictionary] = [location]
	var before := [legacy.duplicate(true), locations.duplicate(true)]
	var report := Diagnostics.inspect(legacy, locations, [])
	_check(report.ok and report.complete and report.owner_review_required \
		and report.reports[0].kind == "potential_gameplay_overlap", "potential blocking overlap requires owner review")
	_check([legacy, locations] == before, "legacy snapshots unchanged")
	_check(Diagnostics.inspect(legacy, locations, []) == report, "repeatable diagnostics without relocation")
	var nearby := Descriptors.create_location(Generator.STARTING_POLICY, 42, Vector2i.ZERO, 5,
		&"cuprite", [Rect2i(10, 0, 4, 4)]).location
	var proximity := Diagnostics.inspect(legacy, [nearby], [])
	_check(proximity.ok and not proximity.owner_review_required \
		and proximity.reports[0].kind == "visual_proximity", "harmless visual proximity distinguished")
	var protection := Diagnostics.inspect(legacy, locations, [Rect2(0, 0, 64, 64)])
	_check(protection.owner_review_required and protection.reports.size() == 3, "authored construction conflicts reported")
	_check(not Diagnostics.inspect([snapshot.snapshot, snapshot.snapshot], [], []).ok, "duplicate diagnostic input rejected")
	var crowded: Array[Dictionary] = []
	for slot in range(128):
		crowded.append(Descriptors.create_location(Generator.STARTING_POLICY, 42, Vector2i.ZERO, slot,
			&"ferrite", [Rect2i(0, 0, 4, 4), Rect2i(4, 0, 4, 4), Rect2i(8, 0, 4, 4)]).location)
	var exhausted := Diagnostics.inspect(legacy, crowded, [Rect2(0, 0, 1000, 1000)])
	_check(not exhausted.ok and not exhausted.complete and exhausted.reports.size() == 256 \
		and exhausted.owner_review_required, "diagnostic overflow fails explicitly")


func _initialize() -> void:
	_layouts()
	_failures_and_admission()
	_transition_and_priority()
	_diagnostics()
	print("Starting reservation assertions: %d checks, %d failures" % [_checks, _failures])
	quit(1 if _failures else 0)
