class_name PlanetWorldState
extends RefCounted

# Authoritative session data, independent of disposable terrain presenters.
# Loading does not mark exploration or surveying. Neither system exists yet.
var seed_value: int
var revision: int = 0
var _terrain_changes: Dictionary[Vector2i, Color] = {}
var _removed_details: Dictionary[Vector2i, bool] = {}


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
