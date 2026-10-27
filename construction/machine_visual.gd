class_name MachineVisual
extends Node2D

# Provisional, shared by deployed machines and the neutral placement ghost.
var definition: MachineDefinition
var turns: int = 0
var show_status: bool = false
var status: PlanetWorldState.OperatingStatus = PlanetWorldState.OperatingStatus.INACTIVE


func _draw() -> void:
	if definition == null:
		return
	var size := Vector2(definition.footprint_cells) * WorldCoordinates.CONSTRUCTION_SIZE
	var origin := definition.rotated_point(Vector2.ZERO, turns)
	draw_set_transform(origin, posmod(turns, 4) * PI / 2.0)
	if definition.item_id == &"smelter":
		_draw_smelter(size)
	else:
		_draw_extractor(size)
	if show_status:
		var color := Color(0.55, 0.58, 0.59)
		if status == PlanetWorldState.OperatingStatus.PRODUCING:
			color = Color(0.35, 0.78, 0.46)
		elif status == PlanetWorldState.OperatingStatus.OUTPUT_FULL:
			color = Color(0.94, 0.69, 0.28)
		elif status == PlanetWorldState.OperatingStatus.INPUT_EMPTY:
			color = Color(0.35, 0.60, 0.90)
		draw_circle(Vector2(size.x - 13, size.y - 13), 3.5, color)


func _draw_smelter(size: Vector2) -> void:
	# Cold furnace chamber and side framing; the top vent makes rotation readable.
	draw_rect(Rect2(Vector2(4, 6), size - Vector2(8, 10)), Color(0.20, 0.25, 0.28))
	draw_rect(Rect2(Vector2(8, 10), size - Vector2(16, 18)), Color(0.45, 0.49, 0.51))
	draw_rect(Rect2(Vector2(size.x * 0.5 - 10, 2), Vector2(20, 12)), Color(0.28, 0.32, 0.34))
	draw_rect(Rect2(Vector2(17, 18), size - Vector2(34, 36)), Color(0.12, 0.15, 0.17))
	draw_rect(Rect2(Vector2(17, 18), size - Vector2(34, 36)), Color(0.62, 0.66, 0.67), false, 3.0)
	draw_line(Vector2(23, 25), Vector2(size.x - 23, 25), Color(0.34, 0.38, 0.40), 2.0)
	draw_line(Vector2(23, 33), Vector2(size.x - 23, 33), Color(0.34, 0.38, 0.40), 2.0)
	for x in [11.0, size.x - 11.0]:
		draw_line(Vector2(x, 16), Vector2(x, size.y - 20), Color(0.66, 0.69, 0.70), 3.0)


func _draw_extractor(size: Vector2) -> void:
	draw_rect(Rect2(Vector2(4, 4), size - Vector2(8, 8)), Color(0.20, 0.25, 0.28))
	draw_rect(Rect2(Vector2(8, 8), size - Vector2(16, 16)), Color(0.53, 0.58, 0.60))
	draw_circle(size * 0.5, 16.0, Color(0.26, 0.31, 0.34))
	draw_circle(size * 0.5, 9.0, Color(0.62, 0.66, 0.67))
	# The north-facing arm makes every quarter turn readable, even on a square.
	draw_rect(Rect2(Vector2(size.x * 0.5 - 5, 2), Vector2(10, 23)), Color(0.73, 0.63, 0.39))
	draw_line(Vector2(12, size.y - 12), Vector2(size.x - 12, size.y - 12),
		Color(0.12, 0.15, 0.17), 4.0)
