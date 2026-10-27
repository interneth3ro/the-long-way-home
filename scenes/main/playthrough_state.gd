class_name PlaythroughState
extends Node

signal ferrite_discovery_completed
signal extractor_recovery_completed

const EXTRACTOR: ItemDefinition = preload("res://inventory/extractor.tres")

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

# Configure on Main/PlaythroughState before a new playthrough begins.
@export var world_seed: int = 26026
var planet: PlanetWorldState


func _ready() -> void:
	planet = PlanetWorldState.new(world_seed)
	add_to_group(&"playthrough")


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
