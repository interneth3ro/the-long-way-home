class_name ResourceGenerationV2Integration
extends RefCounted
## Owned by PlanetWorldState. No scene, activation, occupancy or legacy registry.
## All public reads require the current opaque, process-local context token.

const Starting = preload("res://scenes/world/starting_resource_generator.gd")
const Ordinary = preload("res://scenes/world/ordinary_resource_generator.gd")
const Descriptors = preload("res://scenes/world/resource_generation_descriptors.gd")
const CrashSite = preload("res://scenes/world/resource_generation_crash_site.gd")
const DEFINITION_PATHS := [
	"res://scenes/world/resource_definitions/v2/ferrite.tres",
	"res://scenes/world/resource_definitions/v2/carbite.tres",
	"res://scenes/world/resource_definitions/v2/cuprite.tres"]

var _source: StartingResourceGenerator
var _token: RefCounted
var _seed: int
var _error: String = "v2 context has not been initialized"


func is_ready() -> bool:
	return _source != null and _token != null and _error.is_empty()


func initialization_error() -> String:
	return _error


func invalidate(reason: String = "v2 context retired") -> void:
	# Dropping the only owned generator reference also releases its bounded cache.
	_source = null
	_token = null
	_error = reason


static func _failure(code: String, error: String) -> Dictionary:
	return {"ok": false, "code": code, "error": error}


func configure(world_seed: int, ordinary_policy: String = Ordinary.POLICY,
		starting_policy: String = Starting.STARTING_POLICY,
		schema_version: int = Descriptors.SCHEMA_VERSION) -> Dictionary:
	var supported := ordinary_policy == Ordinary.POLICY \
		and starting_policy == Starting.STARTING_POLICY \
		and schema_version == Descriptors.SCHEMA_VERSION
	if is_ready() and supported and world_seed == _seed:
		return context()
	# A changed/invalid request retires the previous world BEFORE any preparation.
	invalidate("v2 replacement is incomplete")
	if not supported:
		_error = "unsupported v2 ordinary/starting policy or descriptor schema"
		return _failure("incompatible_context", _error)
	var definitions: Array[WorldResourceDefinition] = []
	for path: String in DEFINITION_PATHS:
		var definition := load(path) as WorldResourceDefinition
		if definition == null:
			_error = "cannot load native v2 definition: " + path
			return _failure("initialization_failed", _error)
		definitions.append(definition.duplicate(true))
	var protection := CrashSite.protected_bounds()
	if protection.is_empty():
		_error = "authored crash-site protection snapshot is unavailable"
		return _failure("initialization_failed", _error)
	var candidate := Starting.new(world_seed, definitions, protection,
		CrashSite.SHIP_REFERENCE, starting_policy)
	if not candidate.is_ready():
		_error = candidate.initialization_error()
		return _failure("initialization_failed", _error)
	var layout := candidate.reservations()
	_error = _reservation_error(layout, definitions, world_seed)
	if not _error.is_empty():
		return _failure("initialization_failed", _error)
	# Single synchronous publication boundary; no callbacks/await or partial layout.
	_seed = world_seed
	_source = candidate
	_token = RefCounted.new()
	return context()


static func _reservation_error(layout: Dictionary,
		definitions: Array[WorldResourceDefinition], world_seed: int) -> String:
	if not layout.get("ok", false):
		return str(layout.get("error", "starting reservations unavailable"))
	var locations: Variant = layout.get("locations")
	if not locations is Array or locations.is_empty() or locations.size() > 7:
		return "starting reservations require complete bounded locations"
	var counts := {"ferrite": 0, "carbite": 0, "cuprite": 0}
	var seen: Dictionary = {}
	for location: Variant in locations:
		var error := Descriptors.configured_location_error(location, definitions, [&"terrain_geology"])
		if not error.is_empty():
			return error
		if location.world_seed != world_seed or location.generation_policy != Starting.STARTING_POLICY \
				or location.location_slot < Starting.START_SLOT \
				or location.location_slot >= Starting.START_SLOT + 7 \
				or not Ordinary.owner_is_supported(location.owner_region) \
				or location.owner_region != Ordinary.owner_at(Ordinary.anchor_bounds(location.deposits[0]).position) \
				or not counts.has(location.resource_type) or seen.has(location.location_id):
			return "starting reservation context or identity mismatch"
		seen[location.location_id] = true
		for member: Dictionary in location.deposits:
			if seen.has(member.deposit_id):
				return "duplicate starting deposit identity"
			seen[member.deposit_id] = true
		counts[location.resource_type] += location.deposits.size()
	if counts != Starting.REQUIRED:
		return "starting reservations must contain exactly 3 Ferrite, 2 Carbite, 2 Cuprite"
	return ""


func context() -> Dictionary:
	if not is_ready():
		return _failure("unavailable", _error)
	return {"ok": true, "token": _token, "world_seed": _seed,
		"ordinary_policy": Ordinary.POLICY, "starting_policy": Starting.STARTING_POLICY,
		"schema_version": Descriptors.SCHEMA_VERSION}


func _admission(token: RefCounted) -> Dictionary:
	if not is_ready():
		return _failure("unavailable", _error)
	if token == null or token != _token:
		return _failure("stale_context", "v2 context token is absent, foreign or retired")
	return {"ok": true}


func reservations(token: RefCounted) -> Dictionary:
	var admitted := _admission(token)
	if not admitted.ok:
		return admitted
	return _source.reservations().duplicate(true)


func query(area: Rect2, token: RefCounted) -> Dictionary:
	var admitted := _admission(token)
	if not admitted.ok:
		return admitted
	var result := _source.query(area)
	if not result.ok:
		return _failure("invalid_query", result.error)
	return result.duplicate(true)


func descriptor_by_id(identity: String, token: RefCounted) -> Dictionary:
	var admitted := _admission(token)
	if not admitted.ok:
		return admitted
	var result := _source.descriptor_by_id(identity)
	if not result.ok:
		var code := "invalid_identity"
		if result.error == "identity has no accepted descriptor":
			code = "not_found"
		elif result.error == "unsupported identity policy":
			code = "incompatible_context"
		return _failure(code, result.error)
	return result.duplicate(true)
