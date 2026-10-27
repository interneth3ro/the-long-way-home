extends SceneTree

# Standalone synthetic regression coverage. Added but unexecuted: Godot execution
# is restricted. Seeded progress/output are boundary fixtures, never gameplay.
const FABRICATOR: MachineDefinition = preload("res://inventory/fabricator.tres")
const INGOT: ItemDefinition = preload("res://inventory/ferrite_ingot.tres")
const ORE: ItemDefinition = preload("res://inventory/ferrite_ore.tres")
const Result = PlanetWorldState.RecipeChangeResult

var _failures: int = 0


func _check(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		push_error(message)


func _seed(state: PlanetWorldState, definition: MachineDefinition = FABRICATOR) -> void:
	state._machines[1] = {"id": 1, "definition": definition, "cell": Vector2i(5, 7),
		"turns": 3, "recipe_id": definition.recipes[0].recipe_id,
		"inputs": {&"ferrite_ingot": 15}, "cycle_progress": 0.75, "output": 0}
	state._next_machine_id = 2


func _recipe(id: StringName, items: Array[ItemDefinition]) -> RecipeDefinition:
	var recipe := RecipeDefinition.new()
	recipe.recipe_id = id
	recipe.display_name = String(id)
	recipe.output_item = INGOT
	for item in items:
		var ingredient := RecipeIngredient.new()
		ingredient.item = item
		recipe.ingredients.append(ingredient)
	return recipe


func _check_starter_switches() -> void:
	var state := PlanetWorldState.new()
	var inventory := InventoryState.new()
	_seed(state)
	var before := state.get_machine(1)
	var notifications: Array[int] = [0, 0]
	inventory.changed.connect(func() -> void: notifications[0] += 1)
	state.machines_changed.connect(func() -> void: notifications[1] += 1)
	var lease := state.begin_recipe_change(1)
	_check(lease != null and state.is_recipe_change_paused(1), "Acquire exact pause")
	_check(not state.is_recipe_change_paused(2), "Other machine is not paused")
	_check(state.begin_recipe_change(1) == null, "Cannot replace an active lease")
	state.end_recipe_change(1, RefCounted.new())
	_check(state.is_recipe_change_paused(1), "Wrong lease cannot release pause")
	state.advance_production(4.0)
	_check(state.get_machine(1) == before, "Pause preserves seeded progress and all data")
	# Existing fixed-recipe simulation keeps advancing for unrelated machines.
	state._machines[2] = {"id": 2, "definition": preload("res://inventory/smelter.tres"),
		"cell": Vector2i(20, 20), "turns": 0, "input": 2, "output": 0, "cycle_progress": 0.0}
	state.advance_production(0.5)
	_check(state.get_machine(2).cycle_progress == 0.5 and state.get_machine(2).input == 2,
		"Targeted pause does not stop unrelated Smelter simulation")
	_check(state.get_machine(1) == before, "Other machine advancing does not change paused target")
	_check(state.change_recipe(1, &"ferrite_plate", inventory) == Result.OK, "Current recipe succeeds")
	_check(state.get_machine(1) == before and notifications == [0, 0], "Same recipe is a true no-op")
	_check(state.change_recipe(1, &"unknown", inventory) == Result.INVALID_RECIPE, "Unknown recipe reason")
	_check(state.get_machine(1) == before and state.is_recipe_change_paused(1), "Failure preserves progress and pause")
	_check(state.change_recipe(1, &"ferrite_rod", inventory) == Result.OK, "Plate to Rod")
	var expected := before.duplicate(true)
	expected.recipe_id = &"ferrite_rod"
	expected.cycle_progress = 0.0
	_check(state.get_machine(1) == expected, "Only recipe and incomplete progress change")
	_check(notifications == [0, 1], "No inventory notification for retained materials")
	_check(state.is_recipe_change_paused(1), "Transaction leaves lease lifecycle to its owner")
	state.end_recipe_change(1, lease)
	_check(not state.is_recipe_change_paused(1), "Owner releases pause")
	_check(state.change_recipe(1, &"ferrite_plate", inventory) == Result.OK, "Rod to Plate")
	_check(state.get_machine(1).inputs == before.inputs, "Reverse retains exactly fifteen ingots")
	var snapshot := state.get_machine(1)
	snapshot.inputs.clear()
	_check(state.get_machine(1).inputs == before.inputs, "Switched snapshots remain isolated")
	_check(state.change_recipe(99, &"ferrite_plate", inventory) == Result.MISSING_MACHINE, "Stale ID rejected")
	_check(state.begin_recipe_change(99) == null, "Stale ID cannot pause")
	state._machines[1].recipe_id = &""
	_check(state.begin_recipe_change(1) == null, "Initial configuration has no pause")
	_check(state.change_recipe(1, &"ferrite_plate", inventory) == Result.INVALID_CURRENT, "Switch cannot configure")
	state._machines[1].definition = preload("res://inventory/smelter.tres")
	_check(state.begin_recipe_change(1) == null, "Smelter has no recipe pause")
	_check(state.change_recipe(1, &"ferrite_plate", inventory) == Result.INVALID_CURRENT, "Smelter cannot switch")
	_check(not PlanetWorldState.new().is_recipe_change_paused(1), "Fresh playthrough has no pauses")


func _check_synthetic_returns() -> void:
	var old := _recipe(&"two_inputs", [INGOT, ORE])
	var retain_one := _recipe(&"retain_ingot", [INGOT])
	var other := ItemDefinition.new()
	other.item_id = &"synthetic_material"
	other.display_name = "Synthetic material"
	var return_both := _recipe(&"return_both", [other])
	var definition := MachineDefinition.new()
	definition.item_id = &"synthetic_machine"
	definition.display_name = "Synthetic machine"
	definition.section = ItemDefinition.Section.EQUIPMENT
	definition.input_capacity = 20
	definition.recipes.assign([old, retain_one, return_both])
	var state := PlanetWorldState.new()
	var inventory := InventoryState.new()
	_seed(state, definition)
	state._machines[1].inputs[ORE.item_id] = 7
	# A future output identity must survive independently of the selected recipe.
	state._machines[1].output = 3
	state._machines[1]["output_item_id"] = &"synthetic_old_product"
	var before := state.get_machine(1)
	var conflict := ItemDefinition.new()
	conflict.item_id = ORE.item_id
	conflict.display_name = "Conflicting ore definition"
	inventory.add_item(conflict, 2)
	var notifications: Array[int] = [0]
	inventory.changed.connect(func() -> void: notifications[0] += 1)
	var lease := state.begin_recipe_change(1)
	_check(state.change_recipe(1, return_both.recipe_id, inventory) == Result.INVENTORY_REJECTED,
		"Later ingredient rejection aborts entire staged return")
	_check(state.get_machine(1) == before, "Failed return preserves complete machine snapshot")
	_check(inventory.get_quantity(INGOT.item_id) == 0 and inventory.get_quantity(ORE.item_id) == 2,
		"Earlier staged return rolls back; conflict quantity is unchanged")
	_check(notifications[0] == 0 and state.is_recipe_change_paused(1), "Failure emits nothing and keeps pause")
	inventory.remove_item(conflict, 2)
	var observed: Array[bool] = []
	var on_return := func() -> void:
		observed.append(state.get_machine(1).recipe_id == retain_one.recipe_id)
		observed.append(state.get_machine(1).inputs == {INGOT.item_id: 15})
		observed.append(inventory.get_quantity(ORE.item_id) == 7)
		observed.append(state.change_recipe(1, old.recipe_id, inventory) == Result.BUSY)
		observed.append(not state.recover_machine(1, inventory, Vector2(192, 256), 160))
		observed.append(not state.transfer_input(1, inventory, Vector2(192, 256), 96))
		observed.append(state.begin_recipe_change(1) == null)
	inventory.changed.connect(on_return)
	state.machines_changed.connect(on_return)
	_check(state.change_recipe(1, retain_one.recipe_id, inventory) == Result.OK, "Retain compatible, return incompatible")
	inventory.changed.disconnect(on_return)
	state.machines_changed.disconnect(on_return)
	_check(observed.size() == 14 and not observed.has(false), "Both callbacks see committed state; reentry blocked")
	_check(state.get_machine(1).output == 3 and state.get_machine(1).output_item_id == &"synthetic_old_product",
		"Synthetic completed output quantity and independent identity untouched")
	state.end_recipe_change(1, lease)
	state._machines[1] = before.duplicate(true)
	_check(state.change_recipe(1, return_both.recipe_id, inventory) == Result.OK, "Entire two-item return succeeds")
	_check(state.get_machine(1).inputs.is_empty() and inventory.get_quantity(INGOT.item_id) == 15
		and inventory.get_quantity(ORE.item_id) == 14, "Both returned items conserved")
	# Clear the intentionally invalid synthetic identity before recovery.
	state._machines[1].output = 0
	state._machines[1].output_item_id = &""
	lease = state.begin_recipe_change(1)
	_check(state.recover_machine(1, inventory, Vector2(192, 256), 160), "Recover paused machine")
	_check(not state.is_recipe_change_paused(1), "Removal immediately clears pause")
	state.end_recipe_change(1, lease)


func _check_integrity() -> void:
	var state := PlanetWorldState.new()
	var inventory := InventoryState.new()
	_seed(state)
	for invalid in [{&"unknown": 1}, {INGOT.item_id: -1}, {INGOT.item_id: 21},
			{INGOT.item_id: 1.5}, {INGOT.item_id: "15"}]:
		state._machines[1].inputs = invalid
		var before := state.get_machine(1)
		_check(state.change_recipe(1, &"ferrite_rod", inventory) == Result.INVALID_INPUTS, "Invalid storage rejected")
		_check(state.get_machine(1) == before, "Integrity rejection preserves all state")
	state._machines[1].inputs = []
	_check(state.change_recipe(1, &"ferrite_rod", inventory) == Result.INVALID_INPUTS, "Non-dictionary inputs rejected")


func _initialize() -> void:
	_check_starter_switches()
	_check_synthetic_returns()
	_check_integrity()
	print("Fabricator recipe switching regression failures: %d" % _failures)
	quit(0 if _failures == 0 else 1)
