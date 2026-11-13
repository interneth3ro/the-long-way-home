extends "res://scenes/world/planet_world_state.gd"
## Development-only, nonvisual validation harness. Never installed in PlaythroughState.
## Synthetic environmental inputs are NOT authority for normal gameplay placement.

const Rules = preload("res://construction/extractor_anchor_rules.gd")
var _source: OrdinaryResourceGenerator
var _epoch: int = 0
# Derived index into the inherited authoritative machine registry; no machine copy.
var _claims: Dictionary[String, int] = {}


func configure(source: OrdinaryResourceGenerator) -> bool:
	if _machine_transaction or not _machines.is_empty() or source == null or not source.is_ready():
		return false
	# Inspection-only read of the generator's immutable input; no public accessor
	# exists, and production generator/schema APIs remain unchanged.
	if source._seed != seed_value:
		return false
	_source = source
	_epoch += 1
	return true


func occupant(deposit_id: String) -> int:
	var machine_id: int = _claims.get(deposit_id, 0)
	# Inherited recovery removes the record before notifying. Thus callbacks see
	# released occupancy even before the stale index entry is erased below.
	return machine_id if _machines.has(machine_id) else 0


# Preview and confirmation use exactly the same validator. Rotation is absent
# from selection and cannot move the chosen square anchor.
func preview(cursor: Vector2, definition: MachineDefinition, turns: int,
		context: Dictionary) -> Dictionary:
	if _source == null or _source._seed != seed_value:
		return {"reason": "Unavailable anchor", "ticket": {}}
	var member := Rules.target(_source, cursor)
	if member.is_empty():
		return {"reason": "No valid target", "ticket": {}}
	var ticket := {"source": _source, "epoch": _epoch, "seed": seed_value,
		"policy": _source.identity_policy(),
		"deposit_id": member.deposit_id, "anchor_cells": member.anchor_cells}
	return {"reason": inspect_rejection(ticket, definition, member.anchor_cells.position, turns, context),
		"ticket": ticket, "bounds": Rules.bounds(member.anchor_cells)}


# Environmental context must be complete. Missing inputs fail closed. Available
# means logically valid for inspection, never eligible for gameplay activation.
func inspect_rejection(ticket: Dictionary, definition: MachineDefinition,
		cell: Vector2i, turns: int, context: Dictionary) -> String:
	if _source == null or _source._seed != seed_value \
			or ticket.get("epoch") != _epoch or ticket.get("seed") != seed_value \
			or not ticket.get("deposit_id") is String:
		return "Unavailable anchor"
	var reason := Rules.rejection(_source, ticket, definition, cell, turns,
		occupant(ticket.get("deposit_id", "")), true)
	if not reason.is_empty():
		return reason
	if definition.has_input() or definition.has_recipes():
		return "Unsupported inspection machine"
	var footprint := definition.footprint(cell, turns)
	for machine in _machines.values():
		var other: MachineDefinition = machine.definition
		if footprint.intersects(other.footprint(machine.cell, machine.turns)):
			return "Overlaps a deployed machine"
	if not context.get("player_point") is Vector2 or not context.player_point.is_finite() \
			or not (context.get("range") is float or context.get("range") is int) \
			or not is_finite(float(context.range)) or context.range < 0:
		return "Unavailable environment"
	if PlacementRules.distance_to_footprint(context.player_point, footprint) > context.range:
		return "Out of construction range"
	if context.get("obstacle_clear") != true:
		return "Blocked by a solid obstacle"
	if context.get("player_clear") != true:
		return "Dave is in the footprint"
	var inventory: InventoryState = context.get("inventory") as InventoryState
	if inventory == null or not inventory.get_items().has(definition) \
			or inventory.get_quantity(definition.item_id) < 1:
		return "No packaged machine in inventory"
	return ""


# Inspection transaction only. No await/callback between removal and registration.
# No standalone public claim setter: a claim exists iff its machine committed.
func confirm(ticket: Dictionary, definition: MachineDefinition, cell: Vector2i,
		turns: int, context: Dictionary, inventory: InventoryState) -> int:
	# Always validate the inventory that will actually participate in the commit.
	var current := context.duplicate()
	current["inventory"] = inventory
	if _machine_transaction or inventory == null \
			or not inspect_rejection(ticket, definition, cell, turns, current).is_empty():
		return 0
	_machine_transaction = true
	if not inventory.remove_item(definition, 1, false):
		_machine_transaction = false
		return 0
	var machine_id := _next_machine_id
	_machines[machine_id] = {"id": machine_id, "definition": definition,
		"cell": cell, "turns": posmod(turns, 4), "cycle_progress": 0.0, "output": 0,
		"v2_deposit_id": ticket.deposit_id}
	_claims[ticket.deposit_id] = machine_id
	_next_machine_id += 1
	inventory.changed.emit()
	machines_changed.emit()
	# Inspection intentionally emits no progression/deployment event.
	_machine_transaction = false
	return machine_id


func recover_machine(machine_id: int, inventory: InventoryState,
		player_point: Vector2, recovery_range: float) -> bool:
	if not player_point.is_finite() or not is_finite(recovery_range) or recovery_range < 0:
		return false
	var identity: String = get_machine(machine_id).get("v2_deposit_id", "")
	if not super.recover_machine(machine_id, inventory, player_point, recovery_range):
		return false
	_claims.erase(identity)
	return true


# Fail closed even if an inspection instance is accidentally given to a controller.
func deploy_machine_instance(_definition: MachineDefinition, _cell: Vector2i, _turns: int,
		_inventory: InventoryState, _player: CharacterBody2D, _world: Node2D,
		_construction_range: float) -> int:
	return 0


func advance_production(_delta: float) -> void:
	pass
