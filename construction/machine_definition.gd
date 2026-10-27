class_name MachineDefinition
extends ItemDefinition

# A packaged item is also its machine definition; inventory keeps one identity.
@export var footprint_cells: Vector2i = Vector2i(2, 2)
@export var extraction_point: Vector2 = Vector2(32, 32)
@export var compatible_resources: Array[StringName] = []


func is_valid() -> bool:
	return super.is_valid() and footprint_cells.x > 0 and footprint_cells.y > 0


func footprint(cell: Vector2i, quarter_turns: int) -> Rect2:
	var cells := footprint_cells
	if posmod(quarter_turns, 2) == 1:
		cells = Vector2i(cells.y, cells.x)
	return Rect2(Vector2(cell) * WorldCoordinates.CONSTRUCTION_SIZE,
		Vector2(cells) * WorldCoordinates.CONSTRUCTION_SIZE)


# Clockwise rotation in screen coordinates, translated back to a top-left origin.
# Asymmetric footprints and off-center extraction points use this same mapping.
func rotated_point(point: Vector2, quarter_turns: int) -> Vector2:
	var size := Vector2(footprint_cells) * WorldCoordinates.CONSTRUCTION_SIZE
	match posmod(quarter_turns, 4):
		1:
			return Vector2(size.y - point.y, point.x)
		2:
			return size - point
		3:
			return Vector2(point.y, size.x - point.x)
	return point
