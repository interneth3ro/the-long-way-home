class_name ResourceMigrationDiagnostics
extends RefCounted
## Temporary read-only broad-phase checks. Never called by generation/gameplay.

const Descriptors = preload("res://scenes/world/resource_generation_descriptors.gd")
const Geometry = preload("res://scenes/world/ordinary_resource_generator.gd")
const MAX_LEGACY: int = 128
const MAX_LOCATIONS: int = 128
const MAX_PROTECTION: int = 32
const MAX_REPORTS: int = 256
const VISUAL_PROXIMITY: int = 128


# Caller obtains polygon/envelope from the EXISTING legacy query/resource APIs.
# Introductory Ferrite can use its authored footprint and padded artwork bounds.
static func legacy_snapshot(identity: String, polygon: PackedVector2Array,
		envelope: Rect2) -> Dictionary:
	if identity.is_empty() or polygon.size() < 3 or polygon.size() > 128 or not _bounds_valid(envelope):
		return {"ok": false, "error": "invalid legacy snapshot"}
	var logical := Rect2(polygon[0], Vector2.ZERO)
	for vertex in polygon:
		if not vertex.is_finite():
			return {"ok": false, "error": "nonfinite legacy polygon"}
		logical = logical.expand(vertex)
	if not envelope.encloses(logical):
		return {"ok": false, "error": "legacy artwork envelope must enclose logical bounds"}
	return {"ok": true, "snapshot": {"deposit_id": identity,
		"logical_bounds": logical, "illustrated_envelope": envelope}}


static func _bounds_valid(value: Variant) -> bool:
	return value is Rect2 and value.is_finite() and value.end.is_finite() \
		and value.size.x >= 0.0 and value.size.y >= 0.0


static func _report(reports: Array[Dictionary], first: String, second: String,
		kind: String, first_bounds: Rect2, second_bounds: Rect2) -> bool:
	if reports.size() >= MAX_REPORTS:
		return false
	reports.append({"first_id": first, "second_id": second, "kind": kind,
		"first_bounds": first_bounds, "second_bounds": second_bounds,
		"owner_review_required": kind != "visual_proximity"})
	return true


static func _overflow(reports: Array[Dictionary]) -> Dictionary:
	return {"ok": false, "complete": false, "owner_review_required": true,
		"error": "migration diagnostic report budget exhausted; page the input explicitly",
		"reports": reports}


static func inspect(legacy: Array[Dictionary], locations: Array[Dictionary],
		protected_bounds: Array[Rect2]) -> Dictionary:
	if legacy.size() > MAX_LEGACY or locations.size() > MAX_LOCATIONS \
			or protected_bounds.size() > MAX_PROTECTION:
		return {"ok": false, "error": "migration diagnostic input budget exceeded"}
	var seen: Dictionary = {}
	for snapshot in legacy:
		if not snapshot.get("deposit_id") is String or snapshot.deposit_id.is_empty() \
				or seen.has(snapshot.deposit_id) or not _bounds_valid(snapshot.get("logical_bounds")) \
				or not _bounds_valid(snapshot.get("illustrated_envelope")) \
				or not snapshot.illustrated_envelope.encloses(snapshot.logical_bounds):
			return {"ok": false, "error": "invalid or duplicate legacy snapshot"}
		seen[snapshot.deposit_id] = true
	for location in locations:
		if not Descriptors.location_error(location).is_empty() or seen.has(location.location_id):
			return {"ok": false, "error": "invalid or duplicate v2 location"}
		seen[location.location_id] = true
	for bounds in protected_bounds:
		if not _bounds_valid(bounds):
			return {"ok": false, "error": "invalid authored protection"}
	# Copies alone are sorted; caller snapshots/descriptors are never edited.
	var ordered_legacy := legacy.duplicate(true)
	ordered_legacy.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a.deposit_id < b.deposit_id)
	var ordered_locations := locations.duplicate(true)
	ordered_locations.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a.location_id < b.location_id)
	var reports: Array[Dictionary] = []
	for snapshot: Dictionary in ordered_legacy:
		for location: Dictionary in ordered_locations:
			for member: Dictionary in location.deposits:
				var anchor := Geometry.anchor_bounds(member)
				var visual := Geometry.visual_bounds(member)
				var kind := ""
				var first: Rect2 = snapshot.illustrated_envelope
				var second := visual
				if snapshot.logical_bounds.intersects(anchor, true):
					kind = "potential_gameplay_overlap"
					first = snapshot.logical_bounds
					second = anchor
				elif first.intersects(visual, true):
					kind = "visual_overlap"
				elif first.grow(VISUAL_PROXIMITY).intersects(visual, true):
					kind = "visual_proximity"
				if not kind.is_empty() and not _report(reports, snapshot.deposit_id,
						member.deposit_id, kind, first, second):
					return _overflow(reports)
		for index in range(protected_bounds.size()):
			var bounds := protected_bounds[index]
			if snapshot.illustrated_envelope.intersects(bounds, true):
				var blocking: bool = snapshot.logical_bounds.intersects(bounds, true)
				if not _report(reports, snapshot.deposit_id, "authored:%d" % index,
						"potential_authored_overlap" if blocking else "visual_overlap",
						snapshot.logical_bounds if blocking else snapshot.illustrated_envelope, bounds):
					return _overflow(reports)
	for location: Dictionary in ordered_locations:
		for member: Dictionary in location.deposits:
			for index in range(protected_bounds.size()):
				var bounds := protected_bounds[index]
				if Geometry.visual_bounds(member).intersects(bounds, true):
					if not _report(reports, member.deposit_id, "authored:%d" % index,
							"v2_authored_clearance", Geometry.visual_bounds(member), bounds):
						return _overflow(reports)
	var review := false
	for report in reports:
		review = review or report.owner_review_required
	return {"ok": true, "complete": true, "owner_review_required": review, "reports": reports}
