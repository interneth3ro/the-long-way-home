class_name PlanetWorldState
extends RefCounted

signal machines_changed
signal machine_deployed(definition: MachineDefinition)

enum OperatingStatus { INACTIVE, PRODUCING, OUTPUT_FULL }

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


func get_deposits() -> Array[ResourceDeposit]:
	return _deposits.duplicate()


func get_machines() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for machine in _machines.values():
		result.append(machine.duplicate())
	return result


func machine_at(point: Vector2) -> Dictionary:
	for machine in _machines.values():
		var definition: MachineDefinition = machine.definition
		if definition.footprint(machine.cell, machine.turns).has_point(point):
			return machine.duplicate()
	return {}


# Synchronous transactions: no callbacks/await between item transfer and record
# mutation. Failure leaves both unchanged. The guard also covers signal callbacks.
func deploy_machine(definition: MachineDefinition, cell: Vector2i, turns: int,
		inventory: InventoryState, player: CharacterBody2D, world: Node2D,
		construction_range: float) -> bool:
	if _machine_transaction or inventory == null:
		return false
	if not PlacementRules.rejection(self, definition, cell, turns, player, world,
			construction_range, inventory).is_empty():
		return false
	_machine_transaction = true
	if not inventory.remove_item(definition, 1, false):
		_machine_transaction = false
		return false
	var machine := {"id": _next_machine_id, "definition": definition,
		"cell": cell, "turns": posmod(turns, 4), "cycle_progress": 0.0, "output": 0}
	_machines[_next_machine_id] = machine
	_next_machine_id += 1
	inventory.changed.emit()
	machines_changed.emit()
	machine_deployed.emit(definition)
	_machine_transaction = false
	return true


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
	if not inventory.add_item(definition, 1, false):
		_machine_transaction = false
		return false
	if machine.output > 0 and not inventory.add_item(definition.output_item, machine.output, false):
		# No notifications have fired: undo the packaged item on transfer failure.
		inventory.remove_item(definition, 1, false)
		_machine_transaction = false
		return false
	_machines.erase(machine_id)
	inventory.changed.emit()
	machines_changed.emit()
	_machine_transaction = false
	return true


func get_machine(machine_id: int) -> Dictionary:
	return _machines[machine_id].duplicate() if _machines.has(machine_id) else {}


func machine_status(machine: Dictionary) -> OperatingStatus:
	if machine.is_empty():
		return OperatingStatus.INACTIVE
	var definition: MachineDefinition = machine.definition
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
	# Electrical requirements are provisionally bypassed for this milestone.
	return OperatingStatus.PRODUCING


# Called only by persistent PlaythroughState, never by terrain or UI nodes.
func advance_production(delta: float) -> void:
	if _machine_transaction or not is_finite(delta) or delta <= 0.0:
		return
	for machine in _machines.values():
		if machine_status(machine) != OperatingStatus.PRODUCING:
			continue
		var definition: MachineDefinition = machine.definition
		@warning_ignore("integer_division")
		var available_cycles: int = (definition.output_capacity - machine.output) / definition.output_per_cycle
		# Bound elapsed working time before converting to integer cycles. Time spent
		# blocked earns no backlog; existing fractional work survives the pause.
		var total := minf(machine.cycle_progress + delta,
			available_cycles * definition.cycle_seconds)
		var cycles := mini(int(floor(total / definition.cycle_seconds)), available_cycles)
		machine.output += cycles * definition.output_per_cycle
		machine.cycle_progress = 0.0 if cycles == available_cycles \
			else total - cycles * definition.cycle_seconds


func collect_output(machine_id: int, inventory: InventoryState,
		player_point: Vector2, interaction_range: float) -> bool:
	if _machine_transaction or inventory == null or not _machines.has(machine_id):
		return false
	var machine: Dictionary = _machines[machine_id]
	var definition: MachineDefinition = machine.definition
	if player_point.distance_to(definition.footprint(machine.cell, machine.turns).get_center()) > interaction_range:
		return false
	if machine.output == 0:
		return true
	_machine_transaction = true
	if not inventory.add_item(definition.output_item, machine.output, false):
		_machine_transaction = false
		return false
	machine.output = 0
	inventory.changed.emit()
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
