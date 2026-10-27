extends SceneTree

# Standalone regression checks; run only after owner authorization lifts the
# repository's Godot execution restriction. No third-party test runner required.
const MAIN: PackedScene = preload("res://scenes/main/main.tscn")
const BAY: PackedScene = preload("res://scenes/world/maintenance_bay.tscn")

var _failures: int = 0


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		push_error(message)


func _description(main: Node) -> String:
	return main.get_node("ObjectiveTracker/HUD/Panel/Content/Description").text


func _new_main() -> Node:
	var main := MAIN.instantiate()
	root.add_child(main)
	main.get_node("ObjectiveController").activate_objective(&"restore_computer")
	return main


func _new_bay() -> Node:
	var bay := BAY.instantiate()
	root.add_child(bay)
	return bay


func _check_acquisition_route(recover_smelter: bool) -> void:
	var state := PlaythroughState.new()
	root.add_child(state)
	var bay := _new_bay()
	var rack := bay.get_node("GroundObjects/FabricatorRack") as WorldInteractable
	# Seed only the deployed record to isolate acquisition from placement physics.
	state.planet._machines[1] = {"id": 1, "definition": state.SMELTER,
		"cell": Vector2i.ZERO, "turns": 0, "cycle_progress": 0.0, "input": 1, "output": 0}
	state.planet.advance_production(2.0)
	_check(state.planet.get_machine(1).output == 1, "Smelter fixture produces an ingot")
	_check(not state.ferrite_ingot_acquired and not rack.can_interact(), "Buffer-only ingot must not unlock rack")
	var acquired := state.planet.recover_machine(1, state.inventory, Vector2(32, 32), 96.0) \
		if recover_smelter else state.planet.collect_output(1, state.inventory, Vector2(32, 32), 96.0)
	_check(acquired and state.inventory.get_quantity(&"ferrite_ingot") == 1, "Acquire ingot through existing transaction")
	_check(state.ferrite_ingot_acquired and rack.can_interact(), "Collection and Smelter recovery both unlock rack")
	bay.free()
	state.free()


func _run() -> void:
	var main := _new_main()
	var state := main.get_node("PlaythroughState") as PlaythroughState
	var bay := _new_bay()
	var rack := bay.get_node("GroundObjects/FabricatorRack") as WorldInteractable
	var completions: Array[int] = [0]
	state.fabricator_recovery_completed.connect(func() -> void: completions[0] += 1)
	_check(not rack.can_interact(), "Rack must be locked before ingot acquisition")
	_check(not state.recover_fabricator(), "Locked recovery must fail")
	_check(state.inventory.get_quantity(&"fabricator") == 0, "Locked recovery awards nothing")
	_check(rack.get_node("Module").visible, "Failed recovery must preserve module")
	_check(completions[0] == 0, "Failed recovery must not emit completion")
	_check(_description(main) != "Craft a Ferrite Plate.", "Failed recovery must not advance objective")

	_check(state.inventory.add_item(state.FERRITE_INGOT), "Acquire first ingot")
	_check(state.ferrite_ingot_acquired and rack.can_interact(), "Acquisition must unlock rack")
	_check(_description(main) == "Locate the Fabricator in the maintenance bay.", "Acquisition keeps locate guidance")
	_check(not state.fabricator_recovered, "Acquisition alone must not recover Fabricator")
	_check(state.inventory.remove_item(state.FERRITE_INGOT), "Spend ingot")
	_check(rack.can_interact(), "Unlock must survive spending ingots")

	# Exercise the real inventory rejection path without mocking acceptance rules.
	var conflicting := ItemDefinition.new()
	conflicting.item_id = &"fabricator"
	conflicting.display_name = "Conflicting definition"
	_check(state.inventory.add_item(conflicting), "Set up conflicting item identity")
	rack.interact()
	_check(not state.fabricator_recovered and completions[0] == 0, "Rejected insertion cannot complete recovery")
	_check(state.inventory.get_quantity(&"fabricator") == 1, "Rejected insertion must not add equipment")
	_check(rack.get_node("Module").visible and not rack.get_node("Empty").visible, "Rejected insertion leaves rack intact")
	_check(_description(main) == "Locate the Fabricator in the maintenance bay.", "Rejected insertion keeps objective")
	_check(state.inventory.remove_item(conflicting), "Remove test conflict")

	# Inventory notification is synchronous: a nested recovery must be rejected.
	var nested_results: Array[bool] = []
	var retry := func() -> void: nested_results.append(state.recover_fabricator())
	state.inventory.changed.connect(retry)
	rack.interact()
	state.inventory.changed.disconnect(retry)
	_check(nested_results == [false], "Reentrant recovery must fail")
	_check(state.fabricator_recovered and completions[0] == 1, "Recovery completes exactly once")
	_check(state.inventory.get_quantity(&"fabricator") == 1, "Recovery awards exactly one Fabricator")
	_check(state.FABRICATOR.section == ItemDefinition.Section.EQUIPMENT, "Fabricator belongs in Equipment")
	_check(not state.FABRICATOR is MachineDefinition, "Packaged Fabricator must not be deployable")
	_check(not rack.get_node("Module").visible and not rack.get_node("Secured").visible, "Recovered module and straps hidden")
	_check(rack.get_node("Empty").visible and not rack.can_interact(), "Recovered rack empty and disabled")
	_check(_description(main) == "Craft a Ferrite Plate.", "Recovery advances directly to plate guidance")
	rack.interact()
	_check(not state.recover_fabricator(), "Repeated recovery must fail")
	_check(state.inventory.get_quantity(&"fabricator") == 1 and completions[0] == 1, "Repeated input cannot duplicate")

	# Normal transitions detach cached worlds while Main/state stay alive.
	root.remove_child(bay)
	root.add_child(bay)
	_check(rack.get_node("Empty").visible, "Cached bay revisit preserves empty rack")
	bay.free()
	bay = _new_bay()
	rack = bay.get_node("GroundObjects/FabricatorRack") as WorldInteractable
	_check(rack.get_node("Empty").visible and not rack.can_interact(), "New bay instance reads completed recovery")
	_check(state.inventory.remove_item(state.FABRICATOR), "Remove packaged Fabricator")
	main._refresh_objective_tracker()
	main._on_conversation_completed(&"computer_opening")
	_check(_description(main) == "Craft a Ferrite Plate.", "Travel, item removal and dialogue cannot revert guidance")
	_check(not state.recover_fabricator(), "Removing equipment cannot reset recovery")
	bay.free()
	main.free()

	main = _new_main()
	state = main.get_node("PlaythroughState") as PlaythroughState
	bay = _new_bay()
	rack = bay.get_node("GroundObjects/FabricatorRack") as WorldInteractable
	_check(not state.fabricator_recovered and not state.ferrite_ingot_acquired, "Fresh playthrough resets milestones")
	_check(state.inventory.get_quantity(&"fabricator") == 0, "Fresh playthrough resets inventory")
	_check(rack.get_node("Module").visible and rack.get_node("Secured").visible, "Fresh playthrough restores rack")
	_check(not rack.get_node("Empty").visible and not rack.can_interact(), "Fresh rack starts locked")
	_check(_description(main) != "Craft a Ferrite Plate.", "Fresh playthrough resets guidance")
	bay.free()
	main.free()
	_check_acquisition_route(false)
	_check_acquisition_route(true)
	print("Fabricator recovery regression failures: %d" % _failures)
	quit(0 if _failures == 0 else 1)
