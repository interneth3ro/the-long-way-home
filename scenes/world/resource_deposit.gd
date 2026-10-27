class_name ResourceDeposit
extends Resource

# Read-only authored identity and mineral-bearing polygon in planet world units.
# Artwork and interaction solids are separate; no quantity or yield state exists.
@export var deposit_id: StringName
@export var resource_type: StringName
@export var footprint: PackedVector2Array


func contains_point(world_point: Vector2) -> bool:
	return Geometry2D.is_point_in_polygon(world_point, footprint)
