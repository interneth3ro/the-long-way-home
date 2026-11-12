class_name ResourcePresentationCatalog
extends RefCounted
## Presentation data only. Never consulted by generation or gameplay.

const MAX_BYTES: int = 16384
const MAX_VARIANTS: int = 8
const MAX_IMAGE_BYTES: int = 16777216
const MAX_IMAGE_AXIS: int = 2048
const MAX_REACH: float = 512.0


static func failure(message: String) -> Dictionary:
	return {"ok": false, "code": &"resource_presentation", "error": message}


static func read_catalog(path: String, resource_id: String) -> Dictionary:
	if not WorldResourceDefinition.is_catalog_reference(path) or path.get_extension() != "json":
		return failure("Missing or unsupported presentation catalog for " + resource_id)
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null or file.get_length() > MAX_BYTES:
		return failure("Missing or oversized catalog: " + path)
	var data: Variant = JSON.parse_string(file.get_as_text())
	if not data is Dictionary or data.get("resource_id") != resource_id \
			or data.get("version") != 1 or not data.get("variants") is Array \
			or data.variants.is_empty() or data.variants.size() > MAX_VARIANTS:
		return failure("Invalid catalog header: " + path)
	var variants: Dictionary = {}
	var reach := 0.0
	for entry: Variant in data.variants:
		var admitted := admit_entry(entry)
		if not admitted.ok:
			return admitted
		if variants.has(entry.id):
			return failure("Duplicate artwork variant: " + entry.id)
		variants[entry.id] = admitted.entry
		reach = maxf(reach, admitted.entry.reach)
	return {"ok": true, "variants": variants, "reach": reach}


static func admit_entry(value: Variant) -> Dictionary:
	if not value is Dictionary:
		return failure("Artwork entry must be a Dictionary")
	for key in ["id", "artwork", "sha256"]:
		if not value.get(key) is String:
			return failure("Missing artwork field: " + key)
	if not WorldResourceDefinition.is_token(value.id) \
			or not value.artwork.begins_with("res://assets/") or not value.artwork.ends_with(".png") \
			or value.artwork.contains("..") or value.artwork.contains("\\") \
			or value.sha256.length() != 64:
		return failure("Invalid artwork identity/path/hash")
	for character in value.sha256:
		if not "0123456789abcdef".contains(character):
			return failure("Artwork hash must be lowercase SHA-256")
	for key in ["size", "offset"]:
		if not value.get(key) is Array or value[key].size() != 2:
			return failure("Invalid artwork vector: " + key)
		for component: Variant in value[key]:
			if not (component is float or component is int) or not is_finite(float(component)):
				return failure("Nonfinite artwork vector: " + key)
	if not (value.get("scale") is float or value.get("scale") is int) \
			or not is_finite(float(value.scale)) or value.scale <= 0.0:
		return failure("Artwork requires finite positive uniform scale")
	var size := Vector2(value.size[0], value.size[1])
	var offset := Vector2(value.offset[0], value.offset[1])
	if size.x < 1 or size.y < 1 or size.x > MAX_IMAGE_AXIS or size.y > MAX_IMAGE_AXIS \
			or size != size.floor():
		return failure("Artwork dimensions exceed integer pixel budget")
	var envelope := Rect2(offset - size * float(value.scale) / 2.0, size * float(value.scale))
	var reach := maxf(maxf(absf(envelope.position.x), absf(envelope.end.x)),
		maxf(absf(envelope.position.y), absf(envelope.end.y)))
	if not envelope.is_finite() or not envelope.end.is_finite() or reach > MAX_REACH:
		return failure("Artwork exceeds presentation reach budget")
	return {"ok": true, "entry": {"id": value.id, "artwork": value.artwork,
		"sha256": value.sha256, "size": size, "scale": float(value.scale),
		"offset": offset, "envelope": envelope, "reach": reach}}


# Pure registration: caller has already validated the COMPLETE parent location.
# No random/query-order variation. Empty variation chooses lexical first ID.
static func registration(member: Dictionary, catalog_ref: String, catalog: Dictionary) -> Dictionary:
	var metadata: Dictionary = member.presentation
	if metadata.get("catalog_ref", catalog_ref) != catalog_ref:
		return failure("Descriptor catalog disagrees with resource configuration")
	var ids: Array = catalog.variants.keys()
	ids.sort()
	var variant: String = metadata.get("variant_id", ids[0])
	if not catalog.variants.has(variant):
		return failure("Unknown artwork variant: " + variant)
	var entry: Dictionary = catalog.variants[variant]
	var logical := Rect2(Vector2(member.anchor_cells.position) * 32.0, Vector2(128, 128))
	var center := logical.get_center()
	return {"ok": true, "resource_id": member.resource_type, "deposit_id": member.deposit_id,
		"anchor_cells": member.anchor_cells, "logical_bounds": logical,
		"artwork": entry.artwork, "sha256": entry.sha256, "size": entry.size,
		"scale": entry.scale, "offset": entry.offset, "variant_id": variant,
		"position": center + entry.offset,
		"illustrated_envelope": Rect2(center + entry.envelope.position, entry.envelope.size)}
