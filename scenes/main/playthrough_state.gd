class_name PlaythroughState
extends Node

# Session state only. A fresh Main instance is a new playthrough.
# No disk save/load workflow exists yet; do not store this in project settings.
var first_exterior_reveal_completed: bool = false

# Configure on Main/PlaythroughState before a new playthrough begins.
@export var world_seed: int = 26026
var planet: PlanetWorldState


func _ready() -> void:
	planet = PlanetWorldState.new(world_seed)
