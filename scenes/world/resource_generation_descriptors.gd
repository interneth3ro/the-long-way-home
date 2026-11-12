class_name ResourceGenerationDescriptors
extends RefCounted
## Pure construction/validation of complete v2 locations; no generation or I/O.
## See docs/RESOURCE_GENERATION_V2_CONTRACTS.md for native Variant schema 1.

const Definition = preload("res://scenes/world/world_resource_definition.gd")
const SCHEMA_VERSION: int = 1
const MAX_CELL_COORDINATE: int = 2147483647
const LOCATION_FIELDS := ["schema_version", "generation_policy", "world_seed",
	"owner_region", "location_slot", "location_id", "resource_type", "deposits"]
const DEPOSIT_FIELDS := ["deposit_id", "location_id", "member_index", "resource_type",
	"anchor_cells", "presentation"]


# Internal formatting; constructed results are validated before publication.
static func _location_id(policy: String, seed_value: int, owner: Vector2i, slot: int) -> String:
	return "resource-location:%s:%d:%d:%d:%d" % [policy, seed_value, owner.x, owner.y, slot]


static func _deposit_id(policy: String, seed_value: int, owner: Vector2i, slot: int, index: int) -> String:
	return "resource:%s:%d:%d:%d:%d:%d" % [policy, seed_value, owner.x, owner.y, slot, index]


# Exact keys prevent silently ignoring a misspelled authoritative field.
static func _has_fields(data: Dictionary, fields: Array) -> bool:
	if data.size() != fields.size():
		return false
	for key: Variant in data:
		if not key is String:
			return false
	for field: String in fields:
		if not data.has(field):
			return false
	return true


static func _presentation_error(data: Variant) -> String:
	if not data is Dictionary:
		return "presentation must be a Dictionary"
	for key: Variant in data:
		if not key is String or key not in ["catalog_ref", "variant_id"]:
			return "presentation supports only catalog_ref and variant_id"
		if not data[key] is String:
			return "presentation.%s must be a String" % key
		if key == "catalog_ref" and not Definition.is_catalog_reference(data[key]):
			return "presentation.catalog_ref must be a canonical res:// .tres/.json reference"
		if key == "variant_id" and not Definition.is_token(data[key]):
			return "presentation.variant_id must be a nonempty lowercase ASCII token"
	return ""


static func location_error(data: Variant) -> String:
	if not data is Dictionary or not _has_fields(data, LOCATION_FIELDS):
		return "location must be a Dictionary with exactly the schema 1 location fields"
	if not data.schema_version is int or data.schema_version != SCHEMA_VERSION:
		return "schema_version must be integer 1"
	if not data.generation_policy is String or not Definition.is_token(data.generation_policy):
		return "generation_policy must be a nonempty lowercase ASCII token"
	if not data.world_seed is int or not data.owner_region is Vector2i \
			or not data.location_slot is int or data.location_slot < 0:
		return "identity requires int world_seed, Vector2i owner_region and nonnegative int location_slot"
	var identity := _location_id(data.generation_policy, data.world_seed, data.owner_region, data.location_slot)
	if not data.location_id is String or data.location_id != identity:
		return "location_id does not match generation-policy/seed/owner/slot inputs"
	if not data.resource_type is String or not Definition.is_token(data.resource_type):
		return "resource_type must be a nonempty lowercase ASCII token"
	if not data.deposits is Array or data.deposits.size() < 1 or data.deposits.size() > 3:
		return "deposits must contain the complete set of 1, 2 or 3 members"
	var anchors: Array[Rect2i] = []
	for index in range(data.deposits.size()):
		var member: Variant = data.deposits[index]
		var prefix := "deposits[%d]: " % index
		if not member is Dictionary or not _has_fields(member, DEPOSIT_FIELDS):
			return prefix + "must contain exactly the schema 1 deposit fields"
		if not member.member_index is int or member.member_index != index:
			return prefix + "member_index must equal its zero-based position in the complete member array"
		if not member.location_id is String or member.location_id != identity \
				or not member.resource_type is String or member.resource_type != data.resource_type:
			return prefix + "parent location_id and resource_type must match the location"
		var expected := _deposit_id(data.generation_policy, data.world_seed, data.owner_region, data.location_slot, index)
		if not member.deposit_id is String or member.deposit_id != expected:
			return prefix + "deposit_id does not match parent identity and member_index"
		if not member.anchor_cells is Rect2i or member.anchor_cells.size != Definition.ANCHOR_CELLS:
			return prefix + "anchor_cells must be a grid-aligned Rect2i of size (4, 4) in construction cells"
		var anchor: Rect2i = member.anchor_cells
		# Check with int64 before Rect2i end/intersection arithmetic can overflow.
		if int(anchor.position.x) + 4 > MAX_CELL_COORDINATE or int(anchor.position.y) + 4 > MAX_CELL_COORDINATE:
			return prefix + "anchor end must fit signed 32-bit construction-cell coordinates"
		for other in anchors:
			if anchor.intersects(other):
				return prefix + "extraction anchor overlaps another member"
		anchors.append(anchor)
		var error := _presentation_error(member.presentation)
		if not error.is_empty():
			return prefix + error
	return ""


# Caller supplies anchors: this does not choose positions, owners, slots or types.
# A failure publishes no partial location. Success owns a deep copy of metadata.
static func create_location(policy: String, seed_value: int, owner: Vector2i,
		slot: int, resource_type: StringName, anchors: Array[Rect2i],
		presentation: Array[Dictionary] = []) -> Dictionary:
	if anchors.size() < 1 or anchors.size() > 3:
		return {"ok": false, "error": "anchors must contain the complete set of 1, 2 or 3 members"}
	if not presentation.is_empty() and presentation.size() != anchors.size():
		return {"ok": false, "error": "presentation must be empty or have one entry per anchor"}
	var identity := _location_id(policy, seed_value, owner, slot)
	var members: Array[Dictionary] = []
	for index in range(anchors.size()):
		members.append({"deposit_id": _deposit_id(policy, seed_value, owner, slot, index),
			"location_id": identity, "member_index": index, "resource_type": String(resource_type),
			"anchor_cells": anchors[index],
			"presentation": {} if presentation.is_empty() else presentation[index].duplicate(true)})
	var location := {"schema_version": SCHEMA_VERSION, "generation_policy": policy,
		"world_seed": seed_value, "owner_region": owner, "location_slot": slot,
		"location_id": identity, "resource_type": String(resource_type), "deposits": members}
	var error := location_error(location)
	if not error.is_empty():
		return {"ok": false, "error": error}
	return {"ok": true, "location": location}


# Policy admission is explicit and separate from structural decoding.
static func configured_location_error(data: Variant, definitions: Array[WorldResourceDefinition],
		supported_geology: Array[StringName] = [],
		supported_environments: Array[StringName] = []) -> String:
	var error := location_error(data)
	if not error.is_empty():
		return error
	error = Definition.definitions_error(definitions, supported_geology, supported_environments)
	if not error.is_empty():
		return error
	for definition in definitions:
		if String(definition.resource_id) == data.resource_type:
			return ""
	return "resource_type has no configured definition: %s" % data.resource_type
