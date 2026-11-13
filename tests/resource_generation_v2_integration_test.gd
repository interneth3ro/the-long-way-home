extends SceneTree
## Authored but not executed. No approved runner dispatches this test.

const World = preload("res://scenes/world/planet_world_state.gd")
const Integration = preload("res://scenes/world/resource_generation_v2_integration.gd")
const Starting = preload("res://scenes/world/starting_resource_generator.gd")
const Ordinary = preload("res://scenes/world/ordinary_resource_generator.gd")
const CrashSite = preload("res://scenes/world/resource_generation_crash_site.gd")
const Descriptors = preload("res://scenes/world/resource_generation_descriptors.gd")
const FERRITE = preload("res://scenes/world/resource_definitions/v2/ferrite.tres")
const CARBITE = preload("res://scenes/world/resource_definitions/v2/carbite.tres")
const CUPRITE = preload("res://scenes/world/resource_definitions/v2/cuprite.tres")
var _checks: int = 0
var _failures: int = 0


func _check(condition: bool, label: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		printerr("FAIL: " + label)


func _check_failure(result: Dictionary, expected_code: String, label: String) -> void:
	# Exact failure envelope excludes token/descriptor/deposits/locations payloads.
	_check(result.size() == 3 and result.get("ok") == false
		and result.get("code") == expected_code and result.get("error") is String
		and not String(result.get("error", "")).is_empty(), label)


func _world_contract(seed_value: int) -> void:
	var world := World.new(seed_value)
	var context := world.resource_generation_v2_context()
	_check(context.ok and world.is_resource_generation_v2_ready(), "successful initialization")
	if not context.ok:
		return
	var token: RefCounted = context.token
	_check(context.world_seed == seed_value and context.schema_version == 1 \
		and context.starting_policy == "starting-v2-1" and context.ordinary_policy == "ordinary-v2-1",
		"authoritative seed and approved policies")
	var direct := Starting.new(seed_value, [FERRITE, CARBITE, CUPRITE],
		CrashSite.protected_bounds(), CrashSite.SHIP_REFERENCE)
	var layout := world.starting_resource_reservations_v2(token)
	_check(layout == direct.reservations(), "existing generator and exact authored context")
	var counts := {"ferrite": 0, "carbite": 0, "cuprite": 0}
	var first: Dictionary = layout.locations[0].deposits[0].duplicate(true)
	for location: Dictionary in layout.locations:
		_check(Descriptors.location_error(location).is_empty(), "unchanged schema")
		counts[location.resource_type] += location.deposits.size()
		_check(world.resource_descriptor_v2_by_id(location.location_id, token).descriptor == location,
			"stable location resolution")
		for member: Dictionary in location.deposits:
			var area := Ordinary.visual_bounds(member)
			var result := world.query_resource_descriptors_v2(area, token)
			_check(result.ok and result == direct.query(area), "stable descriptor queries")
			var ids: Dictionary = {}
			for found: Dictionary in result.deposits:
				_check(not ids.has(found.deposit_id), "no cross-region duplicates")
				ids[found.deposit_id] = true
			_check(ids.has(member.deposit_id), "cross-region reservation found")
			_check(world.resource_descriptor_v2_by_id(member.deposit_id, token).descriptor == member,
				"stable deposit-ID resolution")
			result.deposits.clear()
			_check(world.query_resource_descriptors_v2(area, token) == direct.query(area),
				"query defensive copy")
	_check(counts == Starting.REQUIRED, "complete seven-deposit starting reservations")
	layout.locations[0].deposits[0].presentation["variant_id"] = "caller_edit"
	_check(world.starting_resource_reservations_v2(token) == direct.reservations(),
		"reservation nested defensive copy")
	var resolved := world.resource_descriptor_v2_by_id(first.deposit_id, token)
	resolved.descriptor.anchor_cells = Rect2i(0, 0, 4, 4)
	_check(world.resource_descriptor_v2_by_id(first.deposit_id, token).descriptor == first,
		"identity defensive copy")
	_check(world.configure_resource_generation_v2().token == token, "same-context idempotency")
	_check(world.query_resource_descriptors_v2(Rect2(0, 0, -1, 1), token).code == "invalid_query",
		"invalid query distinction")
	_check(world.query_resource_descriptors_v2(Rect2(Vector2(NAN, 0), Vector2.ONE), token).code == "invalid_query",
		"nonfinite query rejection")
	_check(world.query_resource_descriptors_v2(Rect2(0, 0, 100000, 100000), token).code == "invalid_query",
		"owner budget preserved")
	# A point in the protected ship area is valid but has no generated v2 deposits.
	var empty := world.query_resource_descriptors_v2(Rect2(CrashSite.SHIP_REFERENCE, Vector2.ZERO), token)
	_check(empty.ok and empty.deposits.is_empty(), "successful empty query distinction")
	_check(world.resource_descriptor_v2_by_id("invalid", token).code == "invalid_identity", "invalid identity")
	var wrong_policy := "resource:ordinary-v2-1:%d:0:0:0:0" % seed_value
	_check_failure(world.resource_descriptor_v2_by_id(wrong_policy, token), "incompatible_context",
		"incompatible identity policy with current seed")
	var wrong_seed := "resource:starting-v2-1:%d:0:0:0:0" % (seed_value + 1)
	_check_failure(world.resource_descriptor_v2_by_id(wrong_seed, token), "invalid_identity",
		"wrong identity seed with current policy")
	_check(world.resource_generation_v2_context().token == token,
		"identity admission failures preserve healthy context")
	# Find a rejected canonical slot through the existing generator, not a
	# hard-coded assumption about a seed's ordinary candidate positions.
	var absent := ""
	for slot in range(Ordinary.CANDIDATE_SLOTS):
		var identity := "resource:starting-v2-1:%d:-1:-1:%d:0" % [seed_value, slot]
		var probe := direct.descriptor_by_id(identity)
		if not probe.ok and probe.error == "identity has no accepted descriptor":
			absent = identity
			break
	_check(not absent.is_empty(), "missing identity fixture exists")
	if not absent.is_empty():
		_check(world.resource_descriptor_v2_by_id(absent, token).code == "not_found", "stable identity not found")
	_check(world.query_resource_descriptors_v2(Rect2(), World.new(seed_value).resource_generation_v2_context().token).code == "stale_context",
		"foreign world token rejected")
	# Model chunk disposal with unrelated nodes, never launch a playable scene.
	var chunk := Node2D.new()
	chunk.free()
	world.set_terrain_color(Vector2i(9, 9), Color.RED)
	world.remove_detail(Vector2i(8, 8))
	var after := world.resource_generation_v2_context()
	_check(after.token == token and world.resource_descriptor_v2_by_id(first.deposit_id, token).descriptor == first,
		"streaming-independent resource identity")
	var legacy_ids := world.query_deposit_descriptors(Rect2(-1000, -1000, 2000, 2000))
	var legacy_intro := world.get_deposits()[0]
	var machines_before := world.get_machines()
	var revision_before := world.revision
	var failed := world.configure_resource_generation_v2("unsupported")
	_check_failure(failed, "incompatible_context", "replacement failure envelope")
	_check(not failed.ok and failed.code == "incompatible_context" and not world.is_resource_generation_v2_ready(),
		"failed replacement behavior")
	_check(world.resource_generation_v2_error() == failed.error,
		"failure diagnostic without partial publication")
	_check_failure(world.resource_generation_v2_context(), "unavailable", "failed context has no token")
	_check_failure(world.query_resource_descriptors_v2(Rect2(), token), "unavailable",
		"unavailable context distinction")
	_check_failure(world.starting_resource_reservations_v2(token), "unavailable",
		"failed replacement exposes no reservations")
	_check_failure(world.resource_descriptor_v2_by_id(first.deposit_id, token), "unavailable",
		"failed replacement exposes no descriptors")
	_check_failure(world.query_resource_descriptors_v2(Rect2(0, 0, -1, 1), null), "unavailable",
		"unavailable precedes invalid query and token")
	_check(world.is_resource_generation_ready() and world.get_deposit(legacy_intro.deposit_id) == legacy_intro \
		and world.query_deposit_descriptors(Rect2(-1000, -1000, 2000, 2000)) == legacy_ids,
		"preservation of legacy Ferrite behavior")
	var replacement := world.configure_resource_generation_v2()
	_check(replacement.ok and replacement.token != token, "changed-context invalidation")
	_check(world.query_resource_descriptors_v2(Rect2(), token).code == "stale_context" \
		and world.resource_descriptor_v2_by_id(first.deposit_id, token).code == "stale_context" \
		and world.starting_resource_reservations_v2(token).code == "stale_context", "rejection of stale references")
	_check(world.get_machines() == machines_before and world.revision == revision_before \
		and world.terrain_color(Vector2i(9, 9), Color.WHITE) == Color.RED \
		and world.is_detail_removed(Vector2i(8, 8)), "unrelated authoritative state preserved")
	_check(world.deposit_at(Ordinary.anchor_bounds(first).get_center(), &"cuprite") == null,
		"v2 gameplay remains inactive")
	world.invalidate_resource_generation_v2()
	_check(not world.is_resource_generation_v2_ready(), "teardown releases context")
	_check_failure(world.resource_generation_v2_context(), "unavailable", "teardown has no token")
	_check_failure(world.query_resource_descriptors_v2(Rect2(), replacement.token), "unavailable",
		"teardown exposes no descriptors")
	var restored := world.configure_resource_generation_v2()
	world.seed_value = seed_value + 1
	world.seed_value = seed_value
	_check(not world.is_resource_generation_v2_ready(), "seed changes cannot resurrect context")
	world.seed_value = seed_value + 1
	_check(world.configure_resource_generation_v2().code == "incompatible_context",
		"in-place reseeding requires fresh world")
	world.seed_value = seed_value
	_check(world.configure_resource_generation_v2().token != restored.token, "explicit recovery has fresh token")


func _component_failures() -> void:
	var integration := Integration.new()
	_check_failure(integration.query(Rect2(), null), "unavailable", "uninitialized unavailable")
	_check_failure(integration.context(), "unavailable", "uninitialized context has no token")
	var first := integration.configure(42)
	_check(first.ok, "component initializes")
	if not first.ok:
		return
	var failed := integration.configure(42, "ordinary-v2-1", "starting-v2-1", 2)
	_check_failure(failed, "incompatible_context",
		"unsupported schema invalidates previous context")
	_check(not integration.is_ready(), "no fallback after invalid schema")
	_check(integration.initialization_error() == failed.error, "replacement diagnostic retained")
	_check_failure(integration.context(), "unavailable", "failed component has no token")
	_check_failure(integration.reservations(first.token), "unavailable", "failed component has no reservations")
	_check_failure(integration.descriptor_by_id("invalid", first.token), "unavailable",
		"unavailable precedes invalid identity")
	var repeated := integration.configure(42, "ordinary-v2-1", "starting-v2-1", 2)
	_check_failure(repeated, "incompatible_context", "repeated invalid configuration stays failed")
	_check(not integration.is_ready() and integration.initialization_error() == failed.error,
		"repeated failure cannot restore retired context")
	var second := integration.configure(43)
	_check(second.ok and second.token != first.token, "component explicit seed replacement")
	_check(integration.descriptor_by_id("invalid", first.token).code == "stale_context", "component seed retires token")
	var definitions: Array[WorldResourceDefinition] = [FERRITE, CARBITE, CUPRITE]
	var direct := Starting.new(42, definitions, CrashSite.protected_bounds(), CrashSite.SHIP_REFERENCE)
	var layout := direct.reservations()
	if not layout.ok:
		_check(false, "validation fixture ready")
		return
	layout.locations.pop_back()
	_check(not Integration._reservation_error(layout, definitions, 42).is_empty(), "partial layout rejected")
	_check(Integration._reservation_error({"ok": false, "error": "exhausted"}, definitions, 42) == "exhausted",
		"generator exhaustion diagnostic retained")
	_check(not Integration._reservation_error({"ok": true, "locations": []}, definitions, 42).is_empty(),
		"empty successful reservation payload rejected")
	layout = direct.reservations()
	_check(not Integration._reservation_error(layout, definitions, 43).is_empty(), "mismatched seed rejected")
	layout.locations.append(layout.locations[0].duplicate(true))
	_check(not Integration._reservation_error(layout, definitions, 42).is_empty(), "duplicate reservations rejected")


func _initialize() -> void:
	for seed_value in [26026, 0, -79]:
		_world_contract(seed_value)
	_component_failures()
	print("V2 world integration assertions: %d checks, %d failures" % [_checks, _failures])
	quit(1 if _failures else 0)
