class_name ExtractorAnchorRules
extends RefCounted
## Shared v2 logical contract. No presenter, physics or inventory mutation.

const Generator = preload("res://scenes/world/ordinary_resource_generator.gd")
const ANCHOR_CELLS := Vector2i(4, 4)
const CELL: int = 32
# Cursor may be inside the anchor or at most one cell beyond its nearest edge.
const SNAP_TOLERANCE: float = 32.0


static func bounds(anchor: Rect2i) -> Rect2:
	return Rect2(Vector2(anchor.position) * CELL, Vector2(anchor.size) * CELL)


# Pure selector for already admitted descriptors. Includes unavailable anchors so
# an occupied/incompatible target never silently redirects to a farther deposit.
# Candidate count is bounded by the generator query (<=775), including reservations.
static func select(cursor: Vector2, deposits: Array) -> Dictionary:
	if not cursor.is_finite() or deposits.size() > 775:
		return {}
	var best: Dictionary = {}
	var best_distance := INF
	for member: Dictionary in deposits:
		var anchor: Rect2i = member.anchor_cells
		if anchor.size != ANCHOR_CELLS:
			continue
		var rectangle := bounds(anchor)
		var distance := cursor.distance_squared_to(cursor.clamp(rectangle.position, rectangle.end))
		if distance > SNAP_TOLERANCE * SNAP_TOLERANCE:
			continue
		if distance < best_distance or (distance == best_distance and (
				best.is_empty() or member.deposit_id < best.deposit_id)):
			best = member
			best_distance = distance
	return best.duplicate(true)


# Existing generator owns broad-phase reach, cross-region ownership and admission.
# This filters its conservative results by logical geometry, never visual geometry.
static func target(source: OrdinaryResourceGenerator, cursor: Vector2) -> Dictionary:
	if source == null or not source.is_ready() or not cursor.is_finite():
		return {}
	var result := source.query(Rect2(cursor - Vector2.ONE * SNAP_TOLERANCE,
		Vector2.ONE * SNAP_TOLERANCE * 2.0))
	return select(cursor, result.deposits) if result.ok else {}


# Resolve ID again at confirmation; never run nearest-target selection at commit.
# Ticket retains source identity, so same-policy replacements also invalidate it.
static func rejection(source: OrdinaryResourceGenerator, ticket: Dictionary,
		definition: MachineDefinition, cell: Vector2i, turns: int,
		occupant: int, gameplay_eligible: bool = false) -> String:
	if source == null or not source.is_ready() or ticket.get("source") != source \
			or ticket.get("policy") != source.identity_policy() \
			or not ticket.get("deposit_id") is String:
		return "Unavailable anchor"
	var resolved := source.descriptor_by_id(ticket.deposit_id)
	if not resolved.ok or not resolved.descriptor.has("anchor_cells"):
		return "Unavailable anchor"
	var member: Dictionary = resolved.descriptor
	if ticket.get("anchor_cells") != member.anchor_cells:
		return "Unavailable anchor"
	var reason := member_rejection(member, definition, cell, turns, occupant)
	if not reason.is_empty():
		return reason
	if not gameplay_eligible:
		return "Inactive resource"
	return ""


# Both live authority and the isolated harness use the same compatibility/geometry.
static func member_rejection(member: Dictionary, definition: MachineDefinition,
		cell: Vector2i, turns: int, occupant: int) -> String:
	if definition == null or not definition.is_valid() or definition.item_id != &"extractor" \
			or not definition.compatible_resources.has(StringName(member.resource_type)):
		return "Incompatible resource"
	var anchor: Rect2i = member.anchor_cells
	if anchor.size != ANCHOR_CELLS or definition.footprint_cells != ANCHOR_CELLS \
			or cell != anchor.position or definition.footprint(cell, turns) != bounds(anchor):
		return "Requires exact 4x4 anchor alignment"
	if occupant != 0:
		return "Occupied anchor"
	return ""
