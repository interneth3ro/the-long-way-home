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
	draw_rect(Rect2(Vector2(4, 4), size - Vector2(8, 8)), Color(0.20, 0.25, 0.28))
	draw_rect(Rect2(Vector2(8, 8), size - Vector2(16, 16)), Color(0.53, 0.58, 0.60))
	draw_circle(size * 0.5, 16.0, Color(0.26, 0.31, 0.34))
	draw_circle(size * 0.5, 9.0, Color(0.62, 0.66, 0.67))
	# The north-facing arm makes every quarter turn readable, even on a square.
	draw_rect(Rect2(Vector2(size.x * 0.5 - 5, 2), Vector2(10, 23)), Color(0.73, 0.63, 0.39))
	draw_line(Vector2(12, size.y - 12), Vector2(size.x - 12, size.y - 12),
		Color(0.12, 0.15, 0.17), 4.0)
	if show_status:
		var color := Color(0.55, 0.58, 0.59)
		if status == PlanetWorldState.OperatingStatus.PRODUCING:
			color = Color(0.35, 0.78, 0.46)
		elif status == PlanetWorldState.OperatingStatus.OUTPUT_FULL:
			color = Color(0.94, 0.69, 0.28)
		draw_circle(Vector2(size.x - 13, size.y - 13), 3.5, color)
