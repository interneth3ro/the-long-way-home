class_name PlaythroughState
extends Node

signal ferrite_discovery_completed
signal extractor_recovery_completed
signal extractor_deployment_completed
signal ferrite_acquisition_completed
signal smelter_recovery_completed
signal smelter_deployment_completed

const EXTRACTOR: ItemDefinition = preload("res://inventory/extractor.tres")
const FERRITE_ORE: ItemDefinition = preload("res://inventory/ferrite_ore.tres")
const SMELTER: ItemDefinition = preload("res://inventory/smelter.tres")

# Session state only. A fresh Main instance is a new playthrough.
# No disk save/load workflow exists yet; do not store this in project settings.
var first_exterior_reveal_completed: bool = false
var ferrite_discovered: bool = false
var inventory: InventoryState = InventoryState.new()
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
var smelter_recovered: bool:
	get:
		return _smelter_recovered
var _smelter_recovered: bool = false
var _recovering_smelter: bool = false
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
	if not ferrite_acquired and inventory.get_quantity(FERRITE_ORE.item_id) > 0:
		ferrite_acquired = true
		ferrite_acquisition_completed.emit()


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
