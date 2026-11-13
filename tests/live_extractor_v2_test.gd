extends SceneTree
## Authored only. No approved runner dispatches this physics/behavior fixture.

const EXTRACTOR = preload("res://inventory/extractor.tres")
const Rules = preload("res://construction/extractor_anchor_rules.gd")
var _failures: int = 0

class RejectRemoval:
	extends InventoryState
	func remove_item(_definition: ItemDefinition, _quantity: int = 1, _notify: bool = true) -> bool:
		return false

class RejectRecovery:
	extends InventoryState
	func add_items(_items: Array[Dictionary], _notify: bool = true) -> bool:
		return false

func _check(condition: bool, label: String) -> void:
	if not condition:
		_failures += 1
		push_error(label)

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var members := [
		{"deposit_id": "a", "anchor_cells": Rect2i(-2, -2, 4, 4)},
		{"deposit_id": "b", "anchor_cells": Rect2i(4, -2, 4, 4)}]
	_check(Rules.select(Vector2(96, 0), members).deposit_id == "a", "stable tie")
	members.reverse()
	_check(Rules.select(Vector2(96, 0), members).deposit_id == "a", "stable tie independent of order")
	_check(Rules.select(Vector2(-96, 0), members).deposit_id == "a", "inclusive snapping")
	_check(Rules.select(Vector2(-96.01, 0), members).is_empty(), "outside snapping")
	var state := PlanetWorldState.new(42)
	var context := state.resource_generation_v2_context()
	_check(context.ok, "healthy authoritative context")
	if not context.ok:
		quit(1)
		return
	var layout := state.starting_resource_reservations_v2(context.token)
	var cuprite: Dictionary = {}
	var carbite: Dictionary = {}
	for location: Dictionary in layout.locations:
		if location.resource_type == "cuprite":
			cuprite = location.deposits[0]
		if location.resource_type == "carbite":
			carbite = location.deposits[0]
	var cell: Vector2i = cuprite.anchor_cells.position
	var center := Rules.bounds(cuprite.anchor_cells).get_center()
	# Use the authoritative descriptor ticket directly for transaction tests;
	# live routing is separately asserted wherever legacy ground does not win.
	var ticket := {"token": context.token, "deposit_id": cuprite.deposit_id,
		"resource_type": cuprite.resource_type, "anchor_cells": cuprite.anchor_cells}
	for turn in range(4):
		_check(state.extractor_anchor_rejection_v2(ticket, EXTRACTOR, cell, turn).is_empty(), "exact rotated 4x4 alignment")
		var selected := state.extractor_target_v2(center, EXTRACTOR, turn)
		if state.deposit_at(center, &"ferrite") == null:
			_check(selected.ticket == ticket and selected.cell == cell, "live authoritative snapping")
	var incompatible := {"token": context.token, "deposit_id": carbite.deposit_id,
		"resource_type": carbite.resource_type, "anchor_cells": carbite.anchor_cells}
	_check(state.extractor_anchor_rejection_v2(incompatible, EXTRACTOR,
		carbite.anchor_cells.position, 0) == "Incompatible resource", "incompatible feedback")
	var ground := Node2D.new()
	ground.add_to_group(&"construction_world")
	root.add_child(ground)
	var player := CharacterBody2D.new()
	player.position = center - Vector2(90, 0)
	var feet := CollisionShape2D.new()
	var feet_shape := CircleShape2D.new()
	feet_shape.radius = 10.0
	feet.shape = feet_shape
	player.add_child(feet)
	ground.add_child(player)
	await physics_frame
	var rejecting := RejectRemoval.new()
	rejecting.add_item(EXTRACTOR, 2)
	_check(state.deploy_extractor_v2(ticket, EXTRACTOR, cell, 0, rejecting, player, ground, 160) == 0
		and rejecting.get_quantity(&"extractor") == 2 and state.get_machines().is_empty()
		and state.extractor_occupant_v2(cuprite.deposit_id) == 0, "failed removal leaves all state unchanged")
	var relabeled := ticket.duplicate()
	relabeled.resource_type = "ferrite"
	_check(state.extractor_anchor_rejection_v2(relabeled, EXTRACTOR, cell, 0) == "Unavailable anchor", "changed resource rejected")
	relabeled = ticket.duplicate()
	relabeled.anchor_cells = Rect2i(cell + Vector2i.ONE, Vector2i(4, 4))
	_check(state.extractor_anchor_rejection_v2(relabeled, EXTRACTOR, cell, 0) == "Unavailable anchor", "changed anchor rejected")
	var inventory := InventoryState.new()
	inventory.add_item(EXTRACTOR, 2)
	_check(state.deploy_extractor_v2(ticket, EXTRACTOR, cell + Vector2i.ONE, 0,
		inventory, player, ground, 160) == 0 and inventory.get_quantity(&"extractor") == 2,
		"failed placement alignment consumes nothing")
	_check(state.deploy_extractor_v2(ticket, EXTRACTOR, cell, 0,
		inventory, player, ground, 0) == 0, "failed placement distance")
	state._machines[99] = {"id": 99, "definition": EXTRACTOR, "cell": cell, "turns": 0}
	_check(state.deploy_extractor_v2(ticket, EXTRACTOR, cell, 0, inventory, player, ground, 160) == 0
		and state.extractor_occupant_v2(cuprite.deposit_id) == 0, "failed placement machine overlap without claim")
	state._machines.erase(99)
	var blocker := StaticBody2D.new()
	blocker.collision_layer = PlacementRules.BLOCKING_LAYER
	blocker.position = center
	var solid := CollisionShape2D.new()
	var solid_shape := RectangleShape2D.new()
	solid_shape.size = Vector2(20, 20)
	solid.shape = solid_shape
	blocker.add_child(solid)
	ground.add_child(blocker)
	await physics_frame
	_check(PlacementRules.rejection(state, EXTRACTOR, cell, 0, player, ground, 160,
		inventory, ticket) == "Blocked by a solid obstacle", "failed placement physics obstacle")
	blocker.free()
	player.position = center
	await physics_frame
	_check(PlacementRules.rejection(state, EXTRACTOR, cell, 0, player, ground, 160,
		inventory, ticket) == "Dave is in the footprint", "failed placement player safety")
	player.position = center - Vector2(90, 0)
	await physics_frame
	var notifications: Array[int] = []
	inventory.changed.connect(func() -> void:
		notifications.append(state.extractor_occupant_v2(cuprite.deposit_id))
		_check(state._machine_transaction, "notifications guarded")
		_check(state.deploy_extractor_v2(ticket, EXTRACTOR, cell, 0,
			inventory, player, ground, 160) == 0, "reentrant deployment rejected"))
	var machine_id := state.deploy_extractor_v2(ticket, EXTRACTOR, cell, 0, inventory, player, ground, 160)
	_check(machine_id == 1 and notifications == [1] and state.get_machine(1).v2_deposit_id == cuprite.deposit_id,
		"successful deployment and consistent claim notification")
	_check(state.extractor_anchor_rejection_v2(ticket, EXTRACTOR, cell, 0) == "Occupied anchor", "occupied feedback")
	_check(state.deploy_extractor_v2(ticket, EXTRACTOR, cell, 0, inventory, player, ground, 160) == 0
		and inventory.get_quantity(&"extractor") == 1, "duplicate claim")
	var before := state.get_machine(machine_id)
	state.advance_production(5.0)
	_check(state.get_machine(machine_id) == before and state.machine_status(before) == PlanetWorldState.OperatingStatus.INACTIVE,
		"no Cuprite production or legacy Ferrite output")
	_check(not state.recover_machine(machine_id, RejectRecovery.new(), center, 160)
		and state.extractor_occupant_v2(cuprite.deposit_id) == machine_id
		and state.get_machine(machine_id) == before, "failed recovery retains machine and claim")
	_check(not state.recover_machine(machine_id, inventory, center + Vector2(1000, 0), 1), "failed recovery distance")
	_check(state.recover_machine(machine_id, inventory, center, 160)
		and state.extractor_occupant_v2(cuprite.deposit_id) == 0 and notifications == [1, 0]
		and inventory.get_quantity(&"extractor") == 2, "successful recovery releases before notification")
	var next := state.deploy_extractor_v2(ticket, EXTRACTOR, cell, 0, inventory, player, ground, 160)
	_check(next == 2, "monotonic ID after recovery")
	_check(state.recover_machine(next, inventory, center, 160), "second recovery")
	state.invalidate_resource_generation_v2()
	state.configure_resource_generation_v2()
	_check(state.deploy_extractor_v2(ticket, EXTRACTOR, cell, 0, inventory, player, ground, 160) == 0,
		"stale context cannot redirect confirmation")
	# Legacy geometry wins even when the v2 context is unavailable.
	state.invalidate_resource_generation_v2()
	var legacy := state.get_deposits()[0]
	var legacy_cell := WorldCoordinates.world_to_construction(legacy.footprint[0])
	var found := false
	for y in range(legacy_cell.y - 16, legacy_cell.y + 16):
		for x in range(legacy_cell.x - 16, legacy_cell.x + 16):
			var candidate := Vector2i(x, y)
			var extraction := EXTRACTOR.footprint(candidate, 0).get_center()
			if not found and state.deposit_at(extraction, &"ferrite") != null:
				found = true
				var selected := state.extractor_target_v2(Vector2(candidate) * 32, EXTRACTOR, 0)
				_check(selected.ticket.is_empty() and selected.reason.is_empty(), "legacy Ferrite route independent of v2")
				player.position = extraction - Vector2(90, 0)
				await physics_frame
				var identity := state.deploy_machine_instance(EXTRACTOR, candidate, 0, inventory, player, ground, 160)
				_check(identity == 3, "legacy Ferrite deployment")
				state.advance_production(1.0)
				_check(state.get_machine(identity).output == 1, "legacy Ferrite production preserved")
				_check(state.recover_machine(identity, inventory, extraction, 160)
					and inventory.get_quantity(&"ferrite_ore") == 1, "legacy Ferrite recovery returns stored contents")
	_check(found, "legacy Ferrite fixture found")
	ground.free()
	print("Live extractor v2 regression failures: %d" % _failures)
	quit(0 if _failures == 0 else 1)
