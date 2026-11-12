extends SceneTree
## Synthetic pure-data assertions, authored only. NOT allowlisted for execution.
const Definition = preload("res://scenes/world/world_resource_definition.gd")
const Descriptors = preload("res://scenes/world/resource_generation_descriptors.gd")
const FIXTURE = preload("res://tests/fixtures/resource_generation_v2/cuprite.tres")
var _checks: int = 0
var _failures: int = 0


func _check(condition: bool, label: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		printerr("FAIL: " + label)


func _definition(identity: StringName = &"cuprite") -> WorldResourceDefinition:
	var definition := Definition.new()
	definition.resource_id = identity
	definition.abundance_weight = 1.0
	return definition


func _location(count: int = 1, identity: StringName = &"cuprite") -> Dictionary:
	var anchors: Array[Rect2i] = []
	for index in range(count):
		anchors.append(Rect2i(-9 + index * 8, 3 + index * 5, 4, 4))
	return Descriptors.create_location("v2", -9223372036854775807, Vector2i(-2, -3),
		7, identity, anchors)


func _definitions() -> void:
	_check(FIXTURE.validation_error().is_empty(), "native tres synthetic definition")
	_check(not Definition.new().validation_error().is_empty(), "unconfigured definition rejected")
	for identity in [&"ferrite", &"carbite", &"cuprite"]:
		_check(_definition(identity).validation_error().is_empty(), "existing resource vocabulary " + identity)
	for identity in [&"", &"Cuprite", &"cuprite:alias", &" cuprite"]:
		_check(not _definition(identity).validation_error().is_empty(), "invalid resource ID " + identity)
	for weight in [0.0, -1.0, INF, NAN]:
		var definition := _definition()
		definition.abundance_weight = weight
		_check(not definition.validation_error().is_empty(), "invalid abundance rejected")
	var a := _definition()
	var b := _definition()
	_check(not Definition.definitions_error([a, b]).is_empty(), "duplicate resource ID rejected")
	_check(not Definition.definitions_error([null]).is_empty(), "null definition rejected")
	_check(not Definition.definitions_error([]).is_empty(), "empty definition set rejected")
	a.anchor_cells = Vector2i(2, 4)
	_check(not a.validation_error().is_empty(), "invalid anchor dimensions rejected")
	a.anchor_cells = Vector2i(4, 4)
	a.geological_preferences = {"test_geology": 2.0}
	_check(not a.validation_error().is_empty(), "unknown geology rejected")
	_check(a.validation_error([&"test_geology"]).is_empty(), "explicit geology vocabulary")
	for weight in [false, "2", 0, -1, INF, NAN]:
		a.geological_preferences["test_geology"] = weight
		_check(not a.validation_error([&"test_geology"]).is_empty(), "invalid geology weight rejected")
	a.geological_preferences = {}
	a.allowed_environments = [&"test_environment"]
	_check(not a.validation_error().is_empty(), "unknown environment rejected")
	_check(a.validation_error([], [&"test_environment"]).is_empty(), "future allowed-only configuration")
	a.restricted_environments = [&"test_environment"]
	_check(not a.validation_error([], [&"test_environment"]).is_empty(), "conflicting restrictions rejected")
	a.allowed_environments = []
	_check(a.validation_error([], [&"test_environment"]).is_empty(), "future restricted configuration")
	a.restricted_environments = [&"test_environment", &"test_environment"]
	_check(not a.validation_error([], [&"test_environment"]).is_empty(), "duplicate restriction rejected")
	a.restricted_environments = []
	for reference in ["res://catalogs/test.tres", "res://catalogs/test.json", ""]:
		a.presentation_catalog = reference
		_check(a.validation_error().is_empty(), "catalog reference accepted without IO")
	for reference in ["user://test.tres", "res://../test.tres", "res://test.png", "res://x//test.json"]:
		a.presentation_catalog = reference
		_check(not a.validation_error().is_empty(), "invalid catalog reference rejected")


func _membership_and_identity() -> void:
	for count in [1, 2, 3]:
		var result := _location(count)
		_check(result.ok, "single pair triple construction %d" % count)
		if not result.ok:
			continue
		var location: Dictionary = result.location
		_check(location.deposits.size() == count, "complete membership")
		_check(location.location_id == "resource-location:v2:-9223372036854775807:-2:-3:7", "negative owner and int64 seed golden")
		for index in range(count):
			_check(location.deposits[index].deposit_id == "resource:v2:-9223372036854775807:-2:-3:7:%d" % index,
				"deposit identity golden")
		_check(Descriptors.location_error(location).is_empty(), "constructed location consistency")
		_check(Descriptors.configured_location_error(location, [_definition()]).is_empty(), "configured admission")
		_check(not Descriptors.configured_location_error(location, [_definition(&"ferrite")]).is_empty(), "unconfigured type rejected")
		_check(location == _location(count).location, "repeat construction equality")
	for count in [0, 4]:
		var result := _location(count)
		_check(not result.ok and not result.has("location"), "invalid group publishes no partial location")
	var base: Dictionary = _location().location
	for identity in [&"ferrite", &"carbite"]:
		_check(_location(1, identity).location.location_id == base.location_id, "type independent identity")
	var moved := Descriptors.create_location("v2", -9223372036854775807, Vector2i(-2, -3), 7,
		&"cuprite", [Rect2i(100, 100, 4, 4)], [{"variant_id": "test_variant"}])
	_check(moved.location.deposits[0].deposit_id == base.deposits[0].deposit_id, "anchor and artwork independent identity")
	for changed in [Descriptors.create_location("v3", -9223372036854775807, Vector2i(-2, -3), 7, &"cuprite", [Rect2i(0, 0, 4, 4)]),
			Descriptors.create_location("v2", -9223372036854775807, Vector2i(-2, -3), 8, &"cuprite", [Rect2i(0, 0, 4, 4)]),
			Descriptors.create_location("v2", -9223372036854775807, Vector2i(-1, -3), 7, &"cuprite", [Rect2i(0, 0, 4, 4)]),
			Descriptors.create_location("v2", 1, Vector2i(-2, -3), 7, &"cuprite", [Rect2i(0, 0, 4, 4)])]:
		_check(changed.ok and changed.location.location_id != base.location_id, "identity inputs distinguish locations")


func _invalid_descriptors() -> void:
	var valid: Dictionary = _location(2).location
	var mutations := {"schema_version": 1.0, "world_seed": 1.0, "owner_region": Vector2(-2, -3),
		"location_slot": -1, "generation_policy": "v2:bad", "resource_type": "", "location_id": "wrong"}
	for field in mutations:
		var copy := valid.duplicate(true)
		copy[field] = mutations[field]
		_check(not Descriptors.location_error(copy).is_empty(), "invalid location field " + field)
	var member_mutations := {"member_index": 1, "location_id": "wrong", "resource_type": "ferrite",
		"deposit_id": "wrong", "anchor_cells": Rect2(0, 0, 4, 4), "presentation": {"placement": "invalid"}}
	for field in member_mutations:
		var copy := valid.duplicate(true)
		copy.deposits[0][field] = member_mutations[field]
		_check(not Descriptors.location_error(copy).is_empty(), "invalid member field " + field)
	for anchor in [Rect2i(0, 0, 2, 4), Rect2i(2147483647, 0, 4, 4), valid.deposits[1].anchor_cells]:
		var copy := valid.duplicate(true)
		copy.deposits[0].anchor_cells = anchor
		_check(not Descriptors.location_error(copy).is_empty(), "size overflow overlap rejection")
	var copy := valid.duplicate(true)
	copy["unexpected"] = true
	_check(not Descriptors.location_error(copy).is_empty(), "unknown authoritative fields rejected")
	copy = valid.duplicate(true)
	copy.deposits.reverse()
	_check(not Descriptors.location_error(copy).is_empty(), "reordered membership rejected")
	for metadata in [{"variant_id": ""}, {"variant_id": 1}, {"catalog_ref": "user://test.tres"}]:
		copy = valid.duplicate(true)
		copy.deposits[0].presentation = metadata
		_check(not Descriptors.location_error(copy).is_empty(), "invalid presentation rejected")
	var metadata: Array[Dictionary] = [{"variant_id": "test_variant"}]
	var result := Descriptors.create_location("v2", 1, Vector2i.ZERO, 0, &"cuprite",
		[Rect2i(-1, -1, 4, 4)], metadata)
	metadata[0].variant_id = "changed"
	_check(result.ok and result.location.deposits[0].presentation.variant_id == "test_variant", "caller metadata copied")
	result = Descriptors.create_location("v2", 1, Vector2i.ZERO, 0, &"cuprite",
		[Rect2i(0, 0, 4, 4), Rect2i(4, 0, 4, 4)], metadata)
	_check(not result.ok and not result.has("location"), "metadata membership mismatch rejected")
	result = Descriptors.create_location("v2", 1, Vector2i.ZERO, 0, &"cuprite",
		[Rect2i(0, 0, 4, 4), Rect2i(4, 0, 4, 4)])
	_check(result.ok, "edge contact is not overlap; spacing deferred")


func _initialize() -> void:
	_definitions()
	_membership_and_identity()
	_invalid_descriptors()
	print("Resource v2 contracts: %d checks, %d failures" % [_checks, _failures])
	quit(0 if _failures == 0 else 1)
