class_name PlanetWorldState
extends RefCounted

# Authoritative session data, independent of disposable terrain presenters.
# Loading does not mark exploration or surveying. Neither system exists yet.
var seed_value: int
var revision: int = 0
var _terrain_changes: Dictionary[Vector2i, Color] = {}
var _removed_details: Dictionary[Vector2i, bool] = {}
var _deposits: Array[ResourceDeposit] = [preload("res://scenes/world/introductory_ferrite.tres")]


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
