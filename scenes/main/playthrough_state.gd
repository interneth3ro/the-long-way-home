class_name PlaythroughState
extends Node

signal ferrite_discovery_completed
signal extractor_recovery_completed
signal extractor_deployment_completed
signal ferrite_acquisition_completed
signal smelter_recovery_completed
signal smelter_deployment_completed
signal ferrite_ingot_acquisition_completed
signal ferrite_plate_acquisition_completed
signal fabricator_recovery_completed
signal hotbar_changed

const EXTRACTOR: ItemDefinition = preload("res://inventory/extractor.tres")
const FERRITE_ORE: ItemDefinition = preload("res://inventory/ferrite_ore.tres")
const SMELTER: ItemDefinition = preload("res://inventory/smelter.tres")
const FERRITE_INGOT: ItemDefinition = preload("res://inventory/ferrite_ingot.tres")
const FERRITE_PLATE: ItemDefinition = preload("res://inventory/ferrite_plate.tres")
const FABRICATOR: ItemDefinition = preload("res://inventory/fabricator.tres")

# Session state only. A fresh Main instance is a new playthrough.
# No disk save/load workflow exists yet; do not store this in project settings.
var first_exterior_reveal_completed: bool = false
var ferrite_discovered: bool = false
var inventory: InventoryState = InventoryState.new()
# Type assignments belong to the session, never the disposable HUD or inventory.
const HOTBAR_SIZE := 10
var _hotbar: Array[MachineDefinition] = [null, null, null, null, null, null, null, null, null, null]
var _hotbar_customized: Array[bool] = [false, false, false, false, false, false, false, false, false, false]
var _hotbar_defaults_seen: Dictionary[StringName, bool] = {}
var extractor_recovered: bool:
	get:
		return _extractor_recovered
var _extractor_recovered: bool = false
var _recovering_extractor: bool = false
var extractor_deployed: bool:
	get:
		return _extractor_deployed
var _extractor_deployed: bool = false
var ferrite_acquired: bool = false
var ferrite_ingot_acquired: bool = false
var ferrite_plate_acquired: bool = false
var smelter_recovered: bool:
	get:
		return _smelter_recovered
var _smelter_recovered: bool = false
var _recovering_smelter: bool = false
var fabricator_recovered: bool:
	get:
		return _fabricator_recovered
var _fabricator_recovered: bool = false
var _recovering_fabricator: bool = false
var smelter_deployed: bool:
	get:
		return _smelter_deployed
var _smelter_deployed: bool = false

# Configure on Main/PlaythroughState before a new playthrough begins.
@export var world_seed: int = 26026
var planet: PlanetWorldState


func _ready() -> void:
	planet = PlanetWorldState.new(world_seed)
	planet.machine_deployed.connect(_on_machine_deployed)
	inventory.changed.connect(_on_inventory_changed)
	add_to_group(&"playthrough")


func _process(delta: float) -> void:
	planet.advance_production(delta)


func _on_inventory_changed() -> void:
	_apply_hotbar_defaults()
	if not ferrite_acquired and inventory.get_quantity(FERRITE_ORE.item_id) > 0:
		ferrite_acquired = true
		ferrite_acquisition_completed.emit()
	if not ferrite_ingot_acquired and inventory.get_quantity(FERRITE_INGOT.item_id) > 0:
		ferrite_ingot_acquired = true
		ferrite_ingot_acquisition_completed.emit()
	if not ferrite_plate_acquired and inventory.get_quantity(FERRITE_PLATE.item_id) > 0:
		ferrite_plate_acquired = true
		ferrite_plate_acquisition_completed.emit()


func get_hotbar_assignment(slot: int) -> MachineDefinition:
	return _hotbar[slot] if slot >= 0 and slot < HOTBAR_SIZE else null


func assign_hotbar(slot: int, definition: MachineDefinition) -> bool:
	if slot < 0 or slot >= HOTBAR_SIZE or definition == null or not definition.is_valid() \
			or inventory.get_quantity(definition.item_id) < 1:
		return false
	_hotbar[slot] = definition
	_hotbar_customized[slot] = true
	hotbar_changed.emit()
	return true


func clear_hotbar(slot: int) -> void:
	if slot < 0 or slot >= HOTBAR_SIZE:
		return
	_hotbar[slot] = null
	_hotbar_customized[slot] = true
	hotbar_changed.emit()


func _apply_hotbar_defaults() -> void:
	# First possession is the existing packaged-machine availability boundary.
	# Consider each default once, even when its preferred slot is customized.
	var defaults: Array[MachineDefinition] = [EXTRACTOR as MachineDefinition,
		SMELTER as MachineDefinition, FABRICATOR as MachineDefinition]
	for slot in defaults.size():
		var definition := defaults[slot]
		if _hotbar_defaults_seen.has(definition.item_id) \
				or inventory.get_quantity(definition.item_id) < 1:
			continue
		_hotbar_defaults_seen[definition.item_id] = true
		var already_assigned := false
		for assigned in _hotbar:
			if assigned != null and assigned.item_id == definition.item_id:
				already_assigned = true
		if not _hotbar_customized[slot] and _hotbar[slot] == null and not already_assigned:
			_hotbar[slot] = definition
			hotbar_changed.emit()


func _on_machine_deployed(definition: MachineDefinition) -> void:
	if definition.item_id == EXTRACTOR.item_id and not _extractor_deployed:
		_extractor_deployed = true
		extractor_deployment_completed.emit()
	elif definition.item_id == SMELTER.item_id and not _smelter_deployed:
		_smelter_deployed = true
		smelter_deployment_completed.emit()


func discover_ferrite(deposit_id: StringName) -> bool:
	if ferrite_discovered or planet == null:
		return false
	var deposit := planet.get_deposit(deposit_id)
	if deposit == null or deposit.resource_type != &"ferrite":
		return false
	ferrite_discovered = true
	ferrite_discovery_completed.emit()
	return true


func recover_extractor() -> bool:
	if not ferrite_discovered or _extractor_recovered or _recovering_extractor:
		return false
	# Guard synchronous inventory signal callbacks as well as repeated input.
	_recovering_extractor = true
	if not inventory.add_item(EXTRACTOR):
		_recovering_extractor = false
		return false
	_extractor_recovered = true
	_recovering_extractor = false
	extractor_recovery_completed.emit()
	return true


func recover_smelter() -> bool:
	if not ferrite_acquired or _smelter_recovered or _recovering_smelter:
		return false
	# Guard synchronous inventory signal callbacks as well as repeated input.
	_recovering_smelter = true
	if not inventory.add_item(SMELTER):
		_recovering_smelter = false
		return false
	_smelter_recovered = true
	_recovering_smelter = false
	smelter_recovery_completed.emit()
	return true


func recover_fabricator() -> bool:
	if not ferrite_ingot_acquired or _fabricator_recovered or _recovering_fabricator:
		return false
	# Guard synchronous inventory signal callbacks as well as repeated input.
	_recovering_fabricator = true
	if not inventory.add_item(FABRICATOR):
		_recovering_fabricator = false
		return false
	_fabricator_recovered = true
	_recovering_fabricator = false
	fabricator_recovery_completed.emit()
	return true
