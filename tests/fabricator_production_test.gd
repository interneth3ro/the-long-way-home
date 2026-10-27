extends SceneTree

# Added regression coverage, unexecuted under the repository Godot restriction.
# Synthetic storage/recipes isolate boundary cases; they are not player content.
const MAIN: PackedScene = preload("res://scenes/main/main.tscn")
const FABRICATOR: MachineDefinition = preload("res://inventory/fabricator.tres")
const INGOT: ItemDefinition = preload("res://inventory/ferrite_ingot.tres")
const ORE: ItemDefinition = preload("res://inventory/ferrite_ore.tres")
const PLATE: ItemDefinition = preload("res://inventory/ferrite_plate.tres")
const ROD: ItemDefinition = preload("res://inventory/ferrite_rod.tres")
const POINT := Vector2(32, 32)
const Status = PlanetWorldState.OperatingStatus
var _failures: int = 0


func _check(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		push_error(message)


func _seed(state: PlanetWorldState, recipe: StringName = &"ferrite_plate",
		ingots: int = 5) -> void:
	state._machines[1] = {"id": 1, "definition": FABRICATOR, "cell": Vector2i.ZERO,
		"turns": 0, "recipe_id": recipe, "inputs": {INGOT.item_id: ingots},
		"cycle_progress": 0.0, "output": 0, "output_item_id": &""}


func _status(state: PlanetWorldState) -> int:
	return state.machine_status(state.get_machine(1))


func _check_cycles() -> void:
	for recipe in FABRICATOR.recipes:
		_check(recipe.cycle_seconds == 3.0, "Starter duration is recipe data")
		var state := PlanetWorldState.new()
		_seed(state, recipe.recipe_id)
		state.advance_production(1.8)
		_check(state.get_machine(1).inputs[INGOT.item_id] == 5
			and state.get_machine(1).output == 0, "Partial work reserves/consumes nothing")
		_check(is_equal_approx(state.get_machine(1).cycle_progress, 1.8), "Sixty percent work")
		var lease := state.begin_recipe_change(1)
		state.advance_production(1000.0)
		_check(is_equal_approx(state.get_machine(1).cycle_progress, 1.8), "Chooser freezes work")
		_check(state.change_recipe(1, recipe.recipe_id, InventoryState.new())
			== PlanetWorldState.RecipeChangeResult.OK, "Current is a no-op")
		state.end_recipe_change(1, lease)
		state.advance_production(1.2)
		_check(state.get_machine(1).output == recipe.output_quantity
			and state.get_machine(1).inputs[INGOT.item_id] == 4, "Three-second atomic cycle")
		state.advance_production(12.0)
		_check(state.get_machine(1).output == 5 * recipe.output_quantity
			and state.get_machine(1).inputs[INGOT.item_id] == 0, "Five cycles in fifteen seconds")
		_check(_status(state) == Status.INPUT_EMPTY, "Shortage status")
		_seed(state, recipe.recipe_id, 20)
		state.advance_production(1.0e30)
		_check(state.get_machine(1).output == 20 and state.get_machine(1).cycle_progress == 0.0,
			"Huge finite delta bounded by whole output batches")
		_check(state.get_machine(1).inputs[INGOT.item_id] == 20 - 20 / recipe.output_quantity,
			"Huge delta consumes exactly affordable cycles")
		var before := state.get_machine(1)
		for delta in [NAN, INF, -1.0, 0.0]:
			state.advance_production(delta)
		_check(state.get_machine(1) == before, "Invalid deltas are no-ops")
	var recipe := FABRICATOR.recipes[0].duplicate() as RecipeDefinition
	for duration in [0.0, -1.0, INF, NAN]:
		recipe.cycle_seconds = duration
		_check(not recipe.is_valid(), "Reject nonpositive/nonfinite duration")
	var state := PlanetWorldState.new()
	_seed(state)
	state.advance_production(2.999)
	_check(state.get_machine(1).output == 0, "No early completion")
	state.advance_production(0.002)
	_check(state.get_machine(1).output == 1
		and is_equal_approx(state.get_machine(1).cycle_progress, 0.001), "Boundary remainder retained")


func _check_blockage() -> void:
	var state := PlanetWorldState.new()
	var inventory := InventoryState.new()
	_seed(state, &"ferrite_rod", 0)
	state._machines[1].cycle_progress = 1.8
	state.advance_production(1000.0)
	_check(state.get_machine(1).cycle_progress == 1.8, "Shortage retains work")
	inventory.add_item(INGOT, 5)
	_check(state.transfer_input(1, inventory, POINT, 96), "Supply shortage")
	state.advance_production(0.3)
	_check(state.get_machine(1).output == 0
		and is_equal_approx(state.get_machine(1).cycle_progress, 2.1), "No shortage backlog")
	state._machines[1].output = 19
	state._machines[1].output_item_id = ROD.item_id
	_check(_status(state) == Status.OUTPUT_FULL, "Nineteen rods cannot fit batch")
	state.advance_production(1000.0)
	_check(state.get_machine(1).output == 19
		and is_equal_approx(state.get_machine(1).cycle_progress, 2.1), "Full output retains work")
	state._machines[1].output = 18
	state.advance_production(0.9)
	_check(state.get_machine(1).output == 20 and state.get_machine(1).inputs[INGOT.item_id] == 4,
		"Eighteen rods admit one whole batch")
	state._machines[1].cycle_progress = 1.8
	state.advance_production(1000.0)
	_check(state.collect_output(1, inventory, POINT, 96), "Collect full output")
	state.advance_production(0.3)
	_check(state.get_machine(1).output == 0
		and is_equal_approx(state.get_machine(1).cycle_progress, 2.1), "No output backlog")
	# Actual manufactured identity must survive switching and copied snapshots.
	_seed(state)
	state.advance_production(4.8)
	_check(state.change_recipe(1, &"ferrite_rod", inventory) == PlanetWorldState.RecipeChangeResult.OK,
		"Switch with completed Plate")
	_check(state.get_machine(1).output_item_id == PLATE.item_id
		and state.get_machine(1).cycle_progress == 0.0, "Switch preserves product; resets work")
	var snapshot := state.get_machines()[0]
	snapshot.output_item_id = ROD.item_id
	snapshot.inputs.clear()
	_check(state.stored_output_item(state.machine_at(POINT)) == PLATE, "Isolated snapshots preserve identity")
	var before := state.get_machine(1)
	_check(_status(state) == Status.OUTPUT_FULL, "Incompatible output blocks")
	state.advance_production(1000.0)
	_check(state.get_machine(1) == before, "Incompatible output earns no backlog")
	_check(state.collect_output(1, inventory, POINT, 96), "Collect Plate after selecting Rod")
	_check(inventory.get_quantity(PLATE.item_id) == 1, "Collection uses stored product")
	_check(state.get_machine(1).output_item_id == &"", "Empty buffer clears identity")
	state.advance_production(3.0)
	_check(state.get_machine(1).output == 2 and state.get_machine(1).output_item_id == ROD.item_id,
		"Collection unblocks selected recipe")
	state.change_recipe(1, &"ferrite_plate", inventory)
	_check(_status(state) == Status.OUTPUT_FULL, "Reverse incompatible output blocks too")
	state.collect_output(1, inventory, POINT, 96)
	_check(inventory.get_quantity(ROD.item_id) == 22, "Reverse collection retrieves rods")


func _check_transactions() -> void:
	var state := PlanetWorldState.new()
	var inventory := InventoryState.new()
	_seed(state)
	var observations: Array[bool] = []
	var on_produce := func() -> void:
		observations.append(state.get_machine(1).output == 1
			and state.get_machine(1).inputs[INGOT.item_id] == 4)
		var before := state.get_machine(1)
		state.advance_production(30.0)
		observations.append(state.get_machine(1) == before)
		observations.append(not state.collect_output(1, inventory, POINT, 96))
		observations.append(not state.recover_machine(1, inventory, POINT, 160))
	state.machines_changed.connect(on_produce)
	state.advance_production(3.0)
	state.machines_changed.disconnect(on_produce)
	_check(observations.size() == 4 and not observations.has(false), "Production notifies committed guarded state")
	var conflict := PLATE.duplicate() as ItemDefinition
	inventory.add_item(conflict)
	var before := state.get_machine(1)
	_check(not state.collect_output(1, inventory, POINT, 96), "Collection insertion failure")
	_check(not state.recover_machine(1, inventory, POINT, 160), "Late recovery insertion failure")
	_check(state.get_machine(1) == before and inventory.get_quantity(INGOT.item_id) == 0
		and inventory.get_quantity(FABRICATOR.item_id) == 0, "Failed transactions roll back every item")
	inventory.remove_item(conflict)
	_check(not state.collect_output(1, inventory, Vector2(500, 500), 96), "Collection range enforced")
	state._machines[1].cycle_progress = 0.4
	var on_collect := func() -> void:
		_check(state.get_machine(1).output == 0 and state.get_machine(1).output_item_id == &"",
			"Inventory sees cleared output")
		_check(not state.collect_output(1, inventory, POINT, 96), "Collection reentry rejected")
	inventory.changed.connect(on_collect)
	_check(state.collect_output(1, inventory, POINT, 96), "Collection succeeds")
	inventory.changed.disconnect(on_collect)
	state.collect_output(1, inventory, POINT, 96)
	_check(inventory.get_quantity(PLATE.item_id) == 1, "Output transferred exactly once")
	_check(state.get_machine(1).cycle_progress == 0.4
		and state.get_machine(1).inputs == before.inputs, "Collection preserves incomplete work and input")
	state.advance_production(4.0)
	var lease := state.begin_recipe_change(1)
	_check(state.recover_machine(1, inventory, POINT, 160), "Recover equipment, input and completed output")
	_check(inventory.get_quantity(FABRICATOR.item_id) == 1
		and inventory.get_quantity(INGOT.item_id) == 3 and inventory.get_quantity(PLATE.item_id) == 2,
		"Recovery conserves equipment and materials")
	_check(not state.is_recipe_change_paused(1) and state.get_machine(1).is_empty(), "Recovery removes pause and record")
	state.end_recipe_change(1, lease)
	for identity in [&"unknown", &"", 17, null]:
		_seed(state)
		state._machines[1].output = 1
		state._machines[1].output_item_id = identity
		before = state.get_machine(1)
		state.advance_production(100.0)
		_check(_status(state) == Status.INACTIVE and state.get_machine(1) == before, "Invalid identity stops production")
		_check(not state.collect_output(1, inventory, POINT, 96)
			and not state.recover_machine(1, inventory, POINT, 160), "Invalid identity preserves output")
		_check(state.get_machine(1) == before, "Invalid record unchanged")
	for quantity in [-1, 21, 1.5]:
		_seed(state)
		state._machines[1].output = quantity
		state._machines[1].output_item_id = PLATE.item_id
		_check(not state.collect_output(1, inventory, POINT, 96)
			and not state.recover_machine(1, inventory, POINT, 160), "Invalid output quantity rejects transfers")
	_seed(state)
	state._machines[1].output_item_id = PLATE.item_id
	_check(not state.recover_machine(1, inventory, POINT, 160), "Stale empty-buffer identity is rejected")


func _check_multi_ingredient() -> void:
	var recipe := FABRICATOR.recipes[0].duplicate(true) as RecipeDefinition
	# Keep inventory identities canonical; fixture adds no production resource.
	recipe.output_item = PLATE
	recipe.ingredients[0].item = INGOT
	recipe.ingredients[0].quantity = 2
	recipe.cycle_seconds = 0.7
	var extra := RecipeIngredient.new()
	extra.item = ORE
	extra.quantity = 3
	recipe.ingredients.append(extra)
	var definition := FABRICATOR.duplicate() as MachineDefinition
	definition.recipes = [recipe]
	var state := PlanetWorldState.new()
	_seed(state)
	state._machines[1].definition = definition
	state._machines[1].inputs = {INGOT.item_id: 8, ORE.item_id: 9}
	state.advance_production(2.1)
	_check(state.get_machine(1).output == 3 and state.get_machine(1).cycle_progress == 0.0,
		"Nonbinary duration completes all three affordable cycles at clamp")
	_check(state.get_machine(1).inputs == {INGOT.item_id: 2, ORE.item_id: 0}, "All ingredients limit and consume atomically")
	state._machines[1].cycle_progress = 0.4
	var before := state.get_machine(1)
	state.advance_production(100.0)
	_check(state.get_machine(1) == before, "One missing ingredient blocks all consumption")


func _check_milestone() -> void:
	var main := MAIN.instantiate()
	root.add_child(main)
	main.process_mode = Node.PROCESS_MODE_DISABLED
	var state: PlaythroughState = main.get_node("PlaythroughState")
	var objectives: ObjectiveController = main.get_node("ObjectiveController")
	var description: Label = main.get_node("ObjectiveTracker/HUD/Panel/Content/Description")
	objectives.activate_objective(&"restore_computer")
	state._fabricator_recovered = true
	main._refresh_objective_tracker()
	_seed(state.planet)
	state.planet.advance_production(3.0)
	_check(not state.ferrite_plate_acquired and description.text == "Craft a Ferrite Plate.",
		"Manufacture alone cannot complete acquisition guidance")
	var count: Array[int] = [0]
	state.ferrite_plate_acquisition_completed.connect(func() -> void: count[0] += 1)
	var conflict := PLATE.duplicate() as ItemDefinition
	state.inventory.add_item(conflict, 1, false)
	_check(not state.planet.collect_output(1, state.inventory, POINT, 96)
		and not state.ferrite_plate_acquired and count[0] == 0, "Failed collection cannot award milestone")
	state.inventory.remove_item(conflict, 1, false)
	state.planet.collect_output(1, state.inventory, POINT, 96)
	_check(state.ferrite_plate_acquired and count[0] == 1 and description.text.is_empty(), "Collection clears guidance once")
	state.inventory.remove_item(PLATE)
	state.planet.advance_production(3.0)
	state.planet.collect_output(1, state.inventory, POINT, 96)
	_check(state.ferrite_plate_acquired and count[0] == 1, "Spending and reacquisition never reset milestone")
	_check(objectives.get_objective_state(&"restore_computer") == ObjectiveController.State.ACTIVE
		and objectives.definitions.size() == 1, "Restore Computer remains active; no invented objective")
	_check(not main.get_node("Dave/DialogueUI").is_conversation_open(), "No new conversation")
	_check(not main.get_node("MusingUI/HUD/Panel").visible, "No acquisition musing")
	main.free()
	# Recovery also follows the established legitimate inventory-acquisition route.
	var recovered := PlaythroughState.new()
	root.add_child(recovered)
	_seed(recovered.planet)
	recovered.planet.advance_production(3.0)
	recovered.planet.recover_machine(1, recovered.inventory, POINT, 160)
	_check(recovered.ferrite_plate_acquired, "Recovered completed Plate qualifies")
	recovered.free()


func _initialize() -> void:
	_run.call_deferred()


func _check_fixed_machine_regression() -> void:
	var state := PlanetWorldState.new()
	var smelter: MachineDefinition = preload("res://inventory/smelter.tres")
	state._machines[1] = {"id": 1, "definition": smelter, "cell": Vector2i.ZERO,
		"turns": 0, "input": 5, "output": 0, "cycle_progress": 0.0}
	state.advance_production(1.0)
	_check(state.get_machine(1).input == 5 and state.get_machine(1).output == 0,
		"Smelter does not consume partial cycle")
	state.advance_production(9.0)
	_check(state.get_machine(1).input == 0 and state.get_machine(1).output == 5,
		"Smelter retains two-second scalar cycles")
	var inventory := InventoryState.new()
	state.collect_output(1, inventory, POINT, 96)
	_check(inventory.get_quantity(INGOT.item_id) == 5, "Smelter scalar collection")
	state.recover_machine(1, inventory, POINT, 160)
	_check(inventory.get_quantity(smelter.item_id) == 1, "Smelter equipment recovery")
	var extractor: MachineDefinition = preload("res://inventory/extractor.tres")
	# Extraction point (288, 256) lies inside the authored introductory deposit.
	var cell := Vector2i(8, 7)
	state._machines[2] = {"id": 2, "definition": extractor, "cell": cell,
		"turns": 0, "output": 0, "cycle_progress": 0.0}
	state.advance_production(5.0)
	_check(state.get_machine(2).output == 5 and not state.get_machine(2).has("inputs")
		and not state.get_machine(2).has("output_item_id"), "Extractor retains scalar one-second cycles")
	var center := extractor.footprint(cell, 0).get_center()
	state.recover_machine(2, inventory, center, 160)
	_check(inventory.get_quantity(ORE.item_id) == 5
		and inventory.get_quantity(extractor.item_id) == 1, "Extractor recovery conserves products")


func _run() -> void:
	_check_cycles()
	_check_blockage()
	_check_transactions()
	_check_multi_ingredient()
	_check_milestone()
	_check_fixed_machine_regression()
	print("Fabricator production regression failures: %d" % _failures)
	quit(0 if _failures == 0 else 1)
