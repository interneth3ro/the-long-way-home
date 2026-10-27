class_name ResourceDeposit
extends Resource

# Read-only authored identity and mineral-bearing polygon in planet world units.
# Artwork and interaction solids are separate; no quantity or yield state exists.
@export var deposit_id: StringName
@export var resource_type: StringName
@export var footprint: PackedVector2Array
@export var construction_highlight: Color = Color(0.63, 0.76, 0.88, 0.18)


func contains_point(world_point: Vector2) -> bool:
	return Geometry2D.is_point_in_polygon(world_point, footprint)
