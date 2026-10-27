class_name PlaythroughState
extends Node

signal ferrite_discovery_completed

# Session state only. A fresh Main instance is a new playthrough.
# No disk save/load workflow exists yet; do not store this in project settings.
var first_exterior_reveal_completed: bool = false
var ferrite_discovered: bool = false

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
