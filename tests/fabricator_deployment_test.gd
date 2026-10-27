extends SceneTree

# Standalone regression coverage, intentionally unexecuted while Godot execution
# is restricted. Fixture confirmations exercise construction's physics commit;
# actual mouse routing, graphics and hatch travel still need owner playtesting.
const MAIN: PackedScene = preload("res://scenes/main/main.tscn")
const FABRICATOR: MachineDefinition = preload("res://inventory/fabricator.tres")
const INGOT: ItemDefinition = preload("res://inventory/ferrite_ingot.tres")
const ORE: ItemDefinition = preload("res://inventory/ferrite_ore.tres")

var _failures: int = 0


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		push_error(message)


func _seed(state: PlanetWorldState, definition: MachineDefinition = FABRICATOR) -> void:
	state._machines[1] = {"id": 1, "definition": definition, "cell": Vector2i.ZERO,
		"turns": 0, "recipe_id": &"", "inputs": {}, "cycle_progress": 0.0, "output": 0}
	state._next_machine_id = 2


func _check_material_transactions() -> void:
	var state := PlanetWorldState.new()
	var inventory := InventoryState.new()
	_seed(state)
	inventory.add_item(INGOT, 35)
	inventory.add_item(ORE, 7)
	var point := Vector2(32, 32)
	_check(not state.transfer_input(1, inventory, point, 96), "Unconfigured rejects inputs")
	_check(not state.select_initial_recipe(1, &"unknown"), "Invalid recipe rejected")
	_check(state.select_initial_recipe(1, &"ferrite_plate"), "Initial recipe selected")
	_check(not state.select_initial_recipe(1, &"ferrite_rod"), "Recipe switching rejected")
	_check(not state.transfer_input(1, inventory, Vector2(500, 500), 96), "Range enforced")
	var nested: Array[bool] = []
	var retry := func() -> void:
		nested.append(state.transfer_input(1, inventory, point, 96))
		nested.append(state.recover_machine(1, inventory, point, 160))
	inventory.changed.connect(retry)
	_check(state.transfer_input(1, inventory, point, 96), "Transfer succeeds")
	inventory.changed.disconnect(retry)
	_check(nested == [false, false], "Transfer callbacks cannot reenter")
	_check(state.get_machine(1).inputs == {&"ferrite_ingot": 20}, "Only accepted input stored")
	_check(inventory.get_quantity(&"ferrite_ingot") == 15, "Capacity preserves remainder")
	_check(inventory.get_quantity(&"ferrite_ore") == 7, "Ore untouched")
	_check(state.transfer_input(1, inventory, point, 96), "Repeated full transfer is a no-op")
	_check(inventory.get_quantity(&"ferrite_ingot") == 15, "Repeated transfer cannot duplicate")
	var snapshot := state.get_machine(1)
	snapshot.inputs[&"ferrite_ingot"] = 0
	var listed := state.get_machines()
	listed[0].inputs.clear()
	var located := state.machine_at(point)
	located.inputs.clear()
	_check(state.get_machine(1).inputs[&"ferrite_ingot"] == 20, "Snapshots cannot mutate nested storage")
	state.advance_production(4.0)
	_check(state.machine_status(state.get_machine(1)) == PlanetWorldState.OperatingStatus.INACTIVE,
		"Configured Fabricator stays inactive")
	_check(state.get_machine(1).cycle_progress == 0.0 and state.get_machine(1).output == 0,
		"No progress or output")
	_check(state.get_machine(1).inputs[&"ferrite_ingot"] == 20, "No production consumption")
	_check(inventory.get_quantity(&"ferrite_plate") == 0, "No fabricated product awarded")

	# A real definition conflict rejects the whole equipment/material payload.
	var conflict := ItemDefinition.new()
	conflict.item_id = &"fabricator"
	conflict.display_name = "Conflict"
	inventory.add_item(conflict)
	_check(not state.recover_machine(1, inventory, point, 160), "Recovery insertion conflict rejected")
	_check(state.get_machine(1).recipe_id == &"ferrite_plate", "Failed recovery preserves recipe")
	_check(state.get_machine(1).inputs[&"ferrite_ingot"] == 20, "Failed recovery preserves inputs")
	_check(inventory.get_quantity(&"ferrite_ingot") == 15, "Failed recovery preserves inventory")
	inventory.remove_item(conflict)
	nested.clear()
	inventory.changed.connect(retry)
	_check(state.recover_machine(1, inventory, point, 160), "Recovery succeeds")
	inventory.changed.disconnect(retry)
	_check(nested == [false, false], "Recovery callbacks cannot duplicate awards")
	_check(state.get_machine(1).is_empty(), "Recovered record removed")
	_check(inventory.get_quantity(&"fabricator") == 1, "One equipment returned")
	_check(inventory.get_quantity(&"ferrite_ingot") == 35, "All inputs returned")
	_check(not state.select_initial_recipe(1, &"ferrite_rod"), "Recovered ID cannot be configured")
	_check(not state.recover_machine(1, inventory, point, 160), "Recovered ID cannot award twice")
	_check(PlanetWorldState.new().get_machines().is_empty(), "Fresh session resets machinery")


func _check_multi_material_atomicity() -> void:
	# Synthetic recipe tests future keyed storage without adding player content.
	var recipe := RecipeDefinition.new()
	recipe.recipe_id = &"test_two_inputs"
	recipe.display_name = "Two inputs"
	recipe.output_item = INGOT
	for item in [INGOT, ORE]:
		var ingredient := RecipeIngredient.new()
		ingredient.item = item
		recipe.ingredients.append(ingredient)
	var definition := MachineDefinition.new()
	definition.item_id = &"test_machine"
	definition.display_name = "Test machine"
	definition.section = ItemDefinition.Section.EQUIPMENT
	definition.input_capacity = 20
	definition.recipes.append(recipe)
	var state := PlanetWorldState.new()
	_seed(state, definition)
	_check(state.select_initial_recipe(1, recipe.recipe_id), "Multi-input recipe valid")
	var inventory := InventoryState.new()
	inventory.add_item(INGOT, 35)
	var conflict := ItemDefinition.new()
	conflict.item_id = ORE.item_id
	conflict.display_name = "Conflicting ore"
	inventory.add_item(conflict, 25)
	var point := Vector2(32, 32)
	_check(not state.transfer_input(1, inventory, point, 96), "Later removal conflict rejects all")
	_check(inventory.get_quantity(INGOT.item_id) == 35, "First staged removal rolled back")
	_check(state.get_machine(1).inputs.is_empty(), "No partial machine write")
	inventory.remove_item(conflict, 25)
	inventory.add_item(ORE, 25)
	_check(state.transfer_input(1, inventory, point, 96), "Multi-input transfer succeeds")
	_check(state.get_machine(1).inputs == {&"ferrite_ingot": 20, &"ferrite_ore": 20},
		"Independent ingredient capacities")
	_check(inventory.get_quantity(INGOT.item_id) == 15 and inventory.get_quantity(ORE.item_id) == 5,
		"Both inventory remainders preserved")
	# Conflict in the last returned ingredient must not award equipment first.
	inventory.remove_item(ORE, 5)
	inventory.add_item(conflict, 5)
	_check(not state.recover_machine(1, inventory, point, 160), "Last insertion conflict rejects recovery")
	_check(inventory.get_quantity(definition.item_id) == 0, "Failed recovery awards no equipment")
	_check(inventory.get_quantity(INGOT.item_id) == 15, "Failed recovery adds no earlier ingredient")
	_check(state.get_machine(1).inputs.size() == 2, "Failed recovery retains both ingredients")
	inventory.remove_item(conflict, 5)
	inventory.add_item(ORE, 5)
	_check(state.recover_machine(1, inventory, point, 160), "Multi-input recovery succeeds")
	_check(inventory.get_quantity(INGOT.item_id) == 35 and inventory.get_quantity(ORE.item_id) == 25,
		"Multi-input recovery conserves quantities")


func _confirm(construction: ConstructionController, world: Node2D, cell: Vector2i) -> void:
	construction._requested_mode = ConstructionController.Mode.CONSTRUCTION
	construction._requested_world = world
	construction._requested_cell = cell
	construction._requested_turns = 1
	construction._physics_process(0.0)


# Visibility notifications catch hide/show churn even when final visibility is
# correct. This is lifecycle coverage, not a physical mouse press/release test.
func _check_panel_refresh(panel: MachineUI, configured: bool, transfer_enabled: bool) -> void:
	var changes: Array[int] = [0]
	var changed := func() -> void: changes[0] += 1
	panel._input_section.visibility_changed.connect(changed)
	panel._transfer_button.visibility_changed.connect(changed)
	for _iteration in range(3):
		panel._process(0.0)
		_check(panel._input_section.is_visible_in_tree() == configured, "Input visibility matches configuration")
		_check(not panel._progress.visible and not panel._output_section.visible, "Fabricator production controls hidden")
		if configured:
			_check(panel._recipe_summary.visible and panel._status.text == "Inactive", "Configured inspection preserved")
			_check(panel._transfer_button.is_visible_in_tree(), "Transfer control accessible")
			_check(panel._transfer_button.disabled == (not transfer_enabled), "Transfer eligibility preserved")
		else:
			_check(panel._recipe_cards.visible and not panel._transfer_button.is_visible_in_tree(),
				"Chooser exposes no transfer control")
	_check(changes[0] == 0, "Steady refresh must not emit input/button visibility changes")
	panel._input_section.visibility_changed.disconnect(changed)
	panel._transfer_button.visibility_changed.disconnect(changed)


func _run() -> void:
	_check(FABRICATOR.is_valid() and FABRICATOR.footprint_cells == Vector2i(2, 2),
		"Deployable 64x64 Fabricator")
	_check(FABRICATOR.recipes.size() == 2 and not FABRICATOR.has_production(), "Two recipes, no production")
	for recipe in FABRICATOR.recipes:
		_check(recipe.is_valid() and recipe.ingredients.size() == 1, "Valid starter recipe")
		_check(recipe.ingredients[0].item == INGOT and recipe.ingredients[0].quantity == 1, "One ingot input")
	_check(FABRICATOR.get_recipe(&"ferrite_plate").output_quantity == 1, "One plate output")
	_check(FABRICATOR.get_recipe(&"ferrite_rod").output_quantity == 2, "Two rods output")
	_check_material_transactions()
	_check_multi_material_atomicity()

	var main := MAIN.instantiate()
	root.add_child(main)
	# Disable autonomous gameplay during the fixture; invoke only scoped methods.
	main.process_mode = Node.PROCESS_MODE_DISABLED
	var state: PlaythroughState = main.get_node("PlaythroughState")
	var construction: ConstructionController = main.get_node("Construction")
	var panel: MachineUI = main.get_node("MachineUI")
	var transitions: SceneTransitionController = main.get_node("SceneTransitions")
	var world := PlanetExterior.new()
	world.add_to_group(&"construction_world")
	main.get_node("Worlds").add_child(world)
	transitions._current_world = world
	var cell := Vector2i(160, 160)
	var center := FABRICATOR.footprint(cell, 0).get_center()
	construction.player.global_position = center - Vector2(150, 0)
	state.inventory.add_item(FABRICATOR, 2)
	state.inventory.add_item(INGOT, 35)
	state._fabricator_recovered = true
	main.get_node("ObjectiveController").activate_objective(&"restore_computer")
	main._refresh_objective_tracker()
	var observed: Array[int] = []
	construction.deployment_completed.connect(func(machine_id: int) -> void:
		_check(construction._mode == ConstructionController.Mode.NONE, "Tool exited before panel notification")
		_check(not state.planet._machine_transaction, "Transaction completed before panel notification")
		observed.append(machine_id))
	await physics_frame
	_check(construction.begin_deployment(FABRICATOR), "Equipment starts construction")
	_confirm(construction, world, cell)
	_check(observed == [1] and state.planet.get_machines().size() == 1, "One exact committed ID")
	_check(state.inventory.get_quantity(&"fabricator") == 1, "Exactly one equipment consumed")
	_check(panel._recipe_cards.get_child_count() == 2, "Two selectable recipe cards")
	_check(panel.is_open() and panel._machine_id == 1 and panel._recipe_cards.visible,
		"Chooser targets placed instance beyond ordinary range")
	_check(state.planet.get_machine(1).recipe_id == &"", "Placement cannot also choose a card")
	_check_panel_refresh(panel, false, false)
	_check(not construction.begin_deployment(FABRICATOR), "Panel blocks construction")
	panel._select_recipe(1, &"ferrite_rod")
	_check(panel.is_open() and not panel._recipe_cards.visible, "Selection keeps inspection open")
	_check(state.planet.get_machine(1).recipe_id == &"ferrite_rod", "Exact ID configured")
	_check_panel_refresh(panel, true, false)
	panel._transfer()
	_check(state.inventory.get_quantity(&"ferrite_ingot") == 35, "Placement exception cannot transfer")
	panel.close()
	panel.open_machine(1)
	_check(not panel.is_open(), "Normal inspection range unchanged")
	construction.player.global_position = center - Vector2(70, 0)
	panel.open_machine(1)
	_check(panel.is_open() and panel._recipe_summary.visible, "Reopening preserves selected recipe")
	_check_panel_refresh(panel, true, true)
	panel._transfer()
	_check(state.planet.get_machine(1).inputs[&"ferrite_ingot"] == 20, "In-range panel loads materials")
	_check_panel_refresh(panel, true, false)
	panel.close()
	_check(construction.begin_deployment(FABRICATOR), "Second deployment starts")
	_confirm(construction, world, cell)
	_check(observed == [1] and not panel.is_open(), "Failed overlap opens no chooser")
	_check(state.inventory.get_quantity(&"fabricator") == 1, "Failed overlap consumes nothing")
	construction.cancel()
	_check(state.planet.recover_machine(1, state.inventory, center, 160), "Loaded Fabricator recovered")
	_check(construction.begin_deployment(FABRICATOR), "Redeployment starts")
	_confirm(construction, world, cell)
	_check(observed == [1, 2] and panel._machine_id == 2, "Redeployment has fresh ID")
	_check(state.planet.get_machine(2).recipe_id == &"" and state.planet.get_machine(2).inputs.is_empty(),
		"Redeployment resets recipe and storage")
	panel.close()
	panel.open_machine(2)
	_check(panel._recipe_cards.visible, "Dismissed unconfigured machine reopens chooser")
	_check_panel_refresh(panel, false, false)
	panel._select_recipe(2, &"ferrite_plate")
	_check_panel_refresh(panel, true, true)
	panel._transfer()
	var retained := state.planet.get_machine(2)
	var presenter := DeployedMachine.new()
	presenter.configure(state.planet.get_machine(2), state.planet)
	world.add_child(presenter)
	presenter.free()
	presenter = DeployedMachine.new()
	presenter.configure(state.planet.get_machine(2), state.planet)
	world.add_child(presenter)
	_check(state.planet.get_machine(2) == retained, "Presenter recreation preserves recipe and exact inputs")
	panel.close()
	main.get_node("Worlds").remove_child(world)
	transitions._current_world = null
	main.get_node("Worlds").add_child(world)
	transitions._current_world = world
	panel.open_machine(2)
	_check(state.planet.get_machine(2) == retained, "World detach/revisit preserves machine data")
	_check(state.planet.recover_machine(2, state.inventory, center, 160), "Recover open panel target")
	panel._select_recipe(2, &"ferrite_plate")
	panel._process(0.0)
	_check(not panel.is_open(), "Recovered target invalidates panel and stale card")
	main._refresh_objective_tracker()
	_check(main.get_node("ObjectiveTracker/HUD/Panel/Content/Description").text == "Craft a Ferrite Plate.",
		"Configuration/loading never advance crafting objective")
	# Exercise shared-panel transitions after Fabricator inspection without
	# modifying simulation. Existing fixed-recipe presentation must remain intact.
	panel._refresh({"definition": state.SMELTER, "cell": cell, "turns": 0,
		"input": 0, "output": 0, "cycle_progress": 0.0})
	_check(panel._input_section.visible and panel._progress.visible and panel._output_section.visible,
		"Smelter retains input, progress and output sections")
	_check(not panel._recipe_cards.visible and not panel._recipe_summary.visible, "Smelter hides recipe UI")
	panel._refresh({"definition": state.EXTRACTOR, "cell": cell, "turns": 0,
		"output": 0, "cycle_progress": 0.0})
	_check(not panel._input_section.visible and panel._progress.visible and panel._output_section.visible,
		"Extractor retains output-only production view")
	_check(not panel._recipe_cards.visible and not panel._recipe_summary.visible, "Extractor hides recipe UI")
	main.free()
	print("Fabricator deployment regression failures: %d" % _failures)
	quit(0 if _failures == 0 else 1)
