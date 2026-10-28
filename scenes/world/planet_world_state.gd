class_name PlanetWorldState
extends RefCounted

signal machines_changed
signal machine_deployed(definition: MachineDefinition)

enum OperatingStatus { INACTIVE, PRODUCING, OUTPUT_FULL, INPUT_EMPTY }
enum RecipeChangeResult { OK, BUSY, MISSING_MACHINE, INVALID_CURRENT, INVALID_RECIPE,
	INVALID_INPUTS, INVENTORY_REJECTED }

# Authoritative session data, independent of disposable terrain presenters.
# Loading does not mark exploration or surveying. Neither system exists yet.
var seed_value: int
var revision: int = 0
var _terrain_changes: Dictionary[Vector2i, Color] = {}
var _removed_details: Dictionary[Vector2i, bool] = {}
var _deposits: Array[ResourceDeposit] = [preload("res://scenes/world/introductory_ferrite.tres")]
var _machines: Dictionary[int, Dictionary] = {}
var _next_machine_id: int = 1
var _machine_transaction: bool = false
# Transient leases, never part of machine snapshots or persistent configuration.
var _recipe_change_pauses: Dictionary[int, RefCounted] = {}


func get_deposits() -> Array[ResourceDeposit]:
	return _deposits.duplicate()


func get_machines() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for machine in _machines.values():
		result.append(machine.duplicate(true))
	return result


func machine_at(point: Vector2) -> Dictionary:
	for machine in _machines.values():
		var definition: MachineDefinition = machine.definition
		if definition.footprint(machine.cell, machine.turns).has_point(point):
			return machine.duplicate(true)
	return {}


# Synchronous transactions: no callbacks/await between item transfer and record
# mutation. Failure leaves both unchanged. The guard also covers signal callbacks.
# Compatibility entry point for callers that need only success/failure.
func deploy_machine(definition: MachineDefinition, cell: Vector2i, turns: int,
		inventory: InventoryState, player: CharacterBody2D, world: Node2D,
		construction_range: float) -> bool:
	return deploy_machine_instance(definition, cell, turns, inventory, player, world,
		construction_range) != 0


# Returns the committed identity, never a nearest-machine guess. Notifications
# finish under the transaction guard before the construction caller gets the ID.
func deploy_machine_instance(definition: MachineDefinition, cell: Vector2i, turns: int,
		inventory: InventoryState, player: CharacterBody2D, world: Node2D,
		construction_range: float) -> int:
	if _machine_transaction or inventory == null:
		return 0
	if not PlacementRules.rejection(self, definition, cell, turns, player, world,
			construction_range, inventory).is_empty():
		return 0
	_machine_transaction = true
	if not inventory.remove_item(definition, 1, false):
		_machine_transaction = false
		return 0
	var machine_id := _next_machine_id
	var machine := {"id": machine_id, "definition": definition,
		"cell": cell, "turns": posmod(turns, 4), "cycle_progress": 0.0, "output": 0}
	if definition.has_input():
		machine["input"] = 0
	if definition.has_recipes():
		machine["recipe_id"] = &""
		machine["inputs"] = {}
		machine["output_item_id"] = &""
	_machines[machine_id] = machine
	_next_machine_id += 1
	inventory.changed.emit()
	machines_changed.emit()
	machine_deployed.emit(definition)
	_machine_transaction = false
	return machine_id


func recover_machine(machine_id: int, inventory: InventoryState,
		player_point: Vector2, recovery_range: float) -> bool:
	if _machine_transaction or not _machines.has(machine_id) or inventory == null:
		return false
	var machine: Dictionary = _machines[machine_id]
	var definition: MachineDefinition = machine.definition
	if PlacementRules.distance_to_footprint(player_point,
			definition.footprint(machine.cell, machine.turns)) > recovery_range:
		return false
	_machine_transaction = true
	var recovered: Array[Dictionary] = [{"definition": definition, "quantity": 1}]
	if definition.has_input() and machine.get("input", 0) > 0:
		recovered.append({"definition": definition.input_item, "quantity": machine.input})
	if definition.has_recipes():
		var recipe := definition.get_recipe(machine.get("recipe_id", &""))
		var inputs: Dictionary = machine.get("inputs", {})
		# Unconfigured records cannot hold materials. Reject inconsistent records
		# rather than silently losing an unknown item on recovery.
		var accepted: Dictionary = {}
		if recipe != null:
			for ingredient in recipe.ingredients:
				accepted[ingredient.item.item_id] = ingredient.item
		for item_id in inputs:
			if not accepted.has(item_id) or not inputs[item_id] is int or inputs[item_id] < 0:
				_machine_transaction = false
				return false
			if inputs[item_id] > 0:
				recovered.append({"definition": accepted[item_id], "quantity": inputs[item_id]})
	if definition.has_recipes() and not _valid_recipe_output(machine):
		_machine_transaction = false
		return false
	if machine.output > 0:
		recovered.append({"definition": stored_output_item(machine), "quantity": machine.output})
	if not inventory.add_items(recovered, false):
		_machine_transaction = false
		return false
	_machines.erase(machine_id)
	_recipe_change_pauses.erase(machine_id)
	inventory.changed.emit()
	machines_changed.emit()
	_machine_transaction = false
	return true


func get_machine(machine_id: int) -> Dictionary:
	return _machines[machine_id].duplicate(true) if _machines.has(machine_id) else {}


func machine_status(machine: Dictionary) -> OperatingStatus:
	if machine.is_empty():
		return OperatingStatus.INACTIVE
	var definition: MachineDefinition = machine.definition
	if definition.has_recipes():
		return _recipe_status(machine)
	if not definition.has_production():
		return OperatingStatus.INACTIVE
	var point := Vector2(machine.cell) * WorldCoordinates.CONSTRUCTION_SIZE \
		+ definition.rotated_point(definition.extraction_point, machine.turns)
	var compatible := definition.compatible_resources.is_empty()
	for resource_type in definition.compatible_resources:
		if deposit_at(point, resource_type) != null:
			compatible = true
	if not compatible:
		return OperatingStatus.INACTIVE
	if machine.output > definition.output_capacity - definition.output_per_cycle:
		return OperatingStatus.OUTPUT_FULL
	if definition.has_input() and machine.get("input", 0) < definition.input_per_cycle:
		return OperatingStatus.INPUT_EMPTY
	# Electrical requirements are provisionally bypassed for this milestone.
	return OperatingStatus.PRODUCING


# Resolve completed products from stored identity, never from selected recipe.
# Recipe definitions form the small existing product catalog for this machine.
func stored_output_item(machine: Dictionary) -> ItemDefinition:
	var definition: MachineDefinition = machine.definition
	if not definition.has_recipes():
		return definition.output_item
	var item_id: Variant = machine.get("output_item_id", &"")
	if not item_id is StringName:
		return null
	var product: ItemDefinition = null
	for recipe in definition.recipes:
		if recipe == null or not recipe.is_valid() or recipe.output_item.item_id != item_id:
			continue
		if product != null and product != recipe.output_item:
			return null
		product = recipe.output_item
	return product


func _valid_recipe_output(machine: Dictionary) -> bool:
	var definition: MachineDefinition = machine.definition
	var quantity: Variant = machine.get("output")
	if not quantity is int or quantity < 0 or quantity > definition.output_capacity:
		return false
	if quantity == 0:
		return machine.get("output_item_id", &"") == &""
	return stored_output_item(machine) != null


func _recipe_status(machine: Dictionary) -> OperatingStatus:
	var definition: MachineDefinition = machine.definition
	var recipe := definition.get_recipe(machine.get("recipe_id", &""))
	if recipe == null or is_recipe_change_paused(machine.id) \
			or definition.input_capacity <= 0 or not _valid_recipe_output(machine) \
			or not machine.get("inputs") is Dictionary \
			or not is_finite(machine.cycle_progress) or machine.cycle_progress < 0.0 \
			or machine.cycle_progress >= recipe.cycle_seconds:
		return OperatingStatus.INACTIVE
	var accepted: Dictionary = {}
	for ingredient in recipe.ingredients:
		accepted[ingredient.item.item_id] = true
		if ingredient.quantity > definition.input_capacity:
			return OperatingStatus.INACTIVE
	for item_id in machine.inputs:
		var quantity: Variant = machine.inputs[item_id]
		if not accepted.has(item_id) or not quantity is int \
				or quantity < 0 or quantity > definition.input_capacity:
			return OperatingStatus.INACTIVE
	if machine.output > definition.output_capacity - recipe.output_quantity \
			or (machine.output > 0 and stored_output_item(machine) != recipe.output_item):
		return OperatingStatus.OUTPUT_FULL
	for ingredient in recipe.ingredients:
		if machine.inputs.get(ingredient.item.item_id, 0) < ingredient.quantity:
			return OperatingStatus.INPUT_EMPTY
	return OperatingStatus.PRODUCING


func _advance_recipe(machine: Dictionary, delta: float) -> void:
	var definition: MachineDefinition = machine.definition
	var recipe := definition.get_recipe(machine.recipe_id)
	@warning_ignore("integer_division")
	var available: int = (definition.output_capacity - machine.output) / recipe.output_quantity
	for ingredient in recipe.ingredients:
		@warning_ignore("integer_division")
		var affordable: int = machine.inputs.get(ingredient.item.item_id, 0) / ingredient.quantity
		available = mini(available, affordable)
	# Use the fixed-machine boundary convention. Clamp before integer conversion;
	# even huge deltas do constant work per ingredient, with no blocked backlog.
	var capacity_time := available * recipe.cycle_seconds
	var total := minf(machine.cycle_progress + delta, capacity_time)
	var cycles := available if total == capacity_time \
		else mini(int(floor(total / recipe.cycle_seconds)), available)
	if cycles > 0:
		for ingredient in recipe.ingredients:
			machine.inputs[ingredient.item.item_id] -= cycles * ingredient.quantity
		machine.output += cycles * recipe.output_quantity
		machine.output_item_id = recipe.output_item.item_id
	machine.cycle_progress = 0.0 if cycles == available \
		else total - cycles * recipe.cycle_seconds


# Called only by persistent PlaythroughState, never by terrain or UI nodes.
func advance_production(delta: float) -> void:
	if _machine_transaction or not is_finite(delta) or delta <= 0.0:
		return
	_machine_transaction = true
	var changed := false
	for machine in _machines.values():
		# Pause only the instance whose chooser owns the lease.
		if is_recipe_change_paused(machine.id):
			continue
		if machine_status(machine) != OperatingStatus.PRODUCING:
			continue
		var definition: MachineDefinition = machine.definition
		if definition.has_recipes():
			var previous_output: int = machine.output
			_advance_recipe(machine, delta)
			changed = changed or machine.output != previous_output
			continue
		@warning_ignore("integer_division")
		var available_cycles: int = (definition.output_capacity - machine.output) / definition.output_per_cycle
		if definition.has_input():
			@warning_ignore("integer_division")
			var input_cycles: int = machine.get("input", 0) / definition.input_per_cycle
			available_cycles = mini(available_cycles, input_cycles)
		# Bound elapsed working time before converting to integer cycles. Time spent
		# blocked earns no backlog; existing fractional work survives the pause.
		var capacity_time := available_cycles * definition.cycle_seconds
		var total := minf(machine.cycle_progress + delta, capacity_time)
		# At the clamp every affordable cycle completed. Division can round down
		# for nonbinary durations (for example, three 0.7-second cycles).
		var cycles := available_cycles if total == capacity_time \
			else mini(int(floor(total / definition.cycle_seconds)), available_cycles)
		machine.output += cycles * definition.output_per_cycle
		if definition.has_input():
			machine.input -= cycles * definition.input_per_cycle
		machine.cycle_progress = 0.0 if cycles == available_cycles \
			else total - cycles * definition.cycle_seconds

	if changed:
		machines_changed.emit()
	_machine_transaction = false


# Recipe configuration belongs to the persistent machine, never to its panel.
# Initial configuration remains separate from changing a configured recipe.
func select_initial_recipe(machine_id: int, recipe_id: StringName) -> bool:
	if _machine_transaction or not _machines.has(machine_id):
		return false
	var machine: Dictionary = _machines[machine_id]
	var definition: MachineDefinition = machine.definition
	if machine.get("recipe_id", &"") != &"" or not machine.get("inputs", {}).is_empty():
		return false
	var recipe := definition.get_recipe(recipe_id)
	if recipe == null or definition.input_capacity <= 0:
		return false
	_machine_transaction = true
	machine["recipe_id"] = recipe.recipe_id
	machines_changed.emit()
	_machine_transaction = false
	return true


func begin_recipe_change(machine_id: int) -> RefCounted:
	if _machine_transaction or _recipe_change_pauses.has(machine_id):
		return null
	var machine := get_machine(machine_id)
	if machine.is_empty():
		return null
	var definition: MachineDefinition = machine.definition
	if definition.get_recipe(machine.get("recipe_id", &"")) == null:
		return null
	var lease := RefCounted.new()
	_recipe_change_pauses[machine_id] = lease
	return lease


# A stale panel cannot release another panel's lease. Release is permitted during
# notification callbacks so a closing panel can never strand its pause.
func end_recipe_change(machine_id: int, lease: RefCounted) -> void:
	if lease != null and _recipe_change_pauses.get(machine_id) == lease:
		_recipe_change_pauses.erase(machine_id)


func is_recipe_change_paused(machine_id: int) -> bool:
	return _recipe_change_pauses.has(machine_id)


# Empty success payloads do not notify inventory. All mutations commit before
# notifications, under the same guard used by recovery and material transfers.
func change_recipe(machine_id: int, recipe_id: StringName,
		inventory: InventoryState) -> RecipeChangeResult:
	if _machine_transaction:
		return RecipeChangeResult.BUSY
	if not _machines.has(machine_id):
		return RecipeChangeResult.MISSING_MACHINE
	var machine: Dictionary = _machines[machine_id]
	var definition: MachineDefinition = machine.definition
	var old_recipe := definition.get_recipe(machine.get("recipe_id", &""))
	if old_recipe == null or definition.input_capacity <= 0:
		return RecipeChangeResult.INVALID_CURRENT
	var new_recipe := definition.get_recipe(recipe_id)
	if new_recipe == null:
		return RecipeChangeResult.INVALID_RECIPE
	var old_items: Dictionary = {}
	var accepted: Dictionary = {}
	for ingredient in old_recipe.ingredients:
		old_items[ingredient.item.item_id] = ingredient.item
	for ingredient in new_recipe.ingredients:
		accepted[ingredient.item.item_id] = true
	if not machine.get("inputs") is Dictionary:
		return RecipeChangeResult.INVALID_INPUTS
	var retained: Dictionary = {}
	var returns: Array[Dictionary] = []
	for item_id in machine.inputs:
		var quantity: Variant = machine.inputs[item_id]
		if not old_items.has(item_id) or not quantity is int \
				or quantity < 0 or quantity > definition.input_capacity:
			return RecipeChangeResult.INVALID_INPUTS
		if accepted.has(item_id):
			retained[item_id] = quantity
		elif quantity > 0:
			returns.append({"definition": old_items[item_id], "quantity": quantity})
	if old_recipe.recipe_id == new_recipe.recipe_id:
		return RecipeChangeResult.OK
	if inventory == null:
		return RecipeChangeResult.INVENTORY_REJECTED
	_machine_transaction = true
	if not returns.is_empty() and not inventory.add_items(returns, false):
		_machine_transaction = false
		return RecipeChangeResult.INVENTORY_REJECTED
	machine.recipe_id = new_recipe.recipe_id
	machine.inputs = retained
	machine.cycle_progress = 0.0
	# Completed output and its independent identity are deliberately untouched.
	if not returns.is_empty():
		inventory.changed.emit()
	machines_changed.emit()
	_machine_transaction = false
	return RecipeChangeResult.OK


func _transfer_recipe_inputs(machine: Dictionary, inventory: InventoryState) -> bool:
	if is_recipe_change_paused(machine.id):
		return false
	var definition: MachineDefinition = machine.definition
	var recipe := definition.get_recipe(machine.get("recipe_id", &""))
	if recipe == null:
		return false
	var inputs: Dictionary = machine.inputs.duplicate()
	var removals: Array[Dictionary] = []
	for ingredient in recipe.ingredients:
		var item_id := ingredient.item.item_id
		var stored: int = inputs.get(item_id, 0)
		if stored < 0 or stored > definition.input_capacity:
			return false
		var quantity := mini(inventory.get_quantity(item_id), definition.input_capacity - stored)
		if quantity > 0:
			removals.append({"definition": ingredient.item, "quantity": quantity})
			inputs[item_id] = stored + quantity
	if removals.is_empty():
		return true
	_machine_transaction = true
	if not inventory.remove_items(removals, false):
		_machine_transaction = false
		return false
	machine.inputs = inputs
	inventory.changed.emit()
	machines_changed.emit()
	_machine_transaction = false
	return true


func transfer_input(machine_id: int, inventory: InventoryState,
		player_point: Vector2, interaction_range: float) -> bool:
	if _machine_transaction or inventory == null or not _machines.has(machine_id):
		return false
	var machine: Dictionary = _machines[machine_id]
	var definition: MachineDefinition = machine.definition
	if player_point.distance_to(definition.footprint(machine.cell, machine.turns).get_center()) > interaction_range:
		return false
	if definition.has_recipes():
		return _transfer_recipe_inputs(machine, inventory)
	if not definition.has_production() or not definition.has_input():
		return false
	var quantity := mini(inventory.get_quantity(definition.input_item.item_id),
		definition.input_capacity - int(machine.get("input", 0)))
	if quantity <= 0:
		return true
	_machine_transaction = true
	if not inventory.remove_item(definition.input_item, quantity, false):
		_machine_transaction = false
		return false
	machine.input += quantity
	inventory.changed.emit()
	_machine_transaction = false
	return true


func collect_output(machine_id: int, inventory: InventoryState,
		player_point: Vector2, interaction_range: float) -> bool:
	if _machine_transaction or inventory == null or not _machines.has(machine_id):
		return false
	var machine: Dictionary = _machines[machine_id]
	var definition: MachineDefinition = machine.definition
	if player_point.distance_to(definition.footprint(machine.cell, machine.turns).get_center()) > interaction_range:
		return false
	if definition.has_recipes() and not _valid_recipe_output(machine):
		return false
	if machine.output == 0:
		return true
	_machine_transaction = true
	if not inventory.add_item(stored_output_item(machine), machine.output, false):
		_machine_transaction = false
		return false
	machine.output = 0
	if definition.has_recipes():
		machine.output_item_id = &""
	inventory.changed.emit()
	machines_changed.emit()
	_machine_transaction = false
	return true


func get_deposit(deposit_id: StringName) -> ResourceDeposit:
	for deposit in _deposits:
		if deposit.deposit_id == deposit_id:
			return deposit
	return null


# A future machine's designated extraction point can query this independently
# of terrain tiles, artwork and its remaining 32-unit construction footprint.
func deposit_at(world_point: Vector2, resource_type: StringName) -> ResourceDeposit:
	for deposit in _deposits:
		if deposit.resource_type == resource_type and deposit.contains_point(world_point):
			return deposit
	return null


func _init(world_seed: int = 26026) -> void:
	seed_value = world_seed


func set_terrain_color(tile: Vector2i, color: Color) -> void:
	_terrain_changes[tile] = color
	revision += 1


func terrain_color(tile: Vector2i, baseline: Color) -> Color:
	return _terrain_changes.get(tile, baseline)


# A detail's stable identity is its world terrain tile (at most one per tile).
func remove_detail(tile: Vector2i) -> void:
	_removed_details[tile] = true
	revision += 1


func is_detail_removed(tile: Vector2i) -> bool:
	return _removed_details.has(tile)
