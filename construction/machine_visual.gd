class_name MachineVisual
extends Node2D

# Shared adapter for deployed machines and the neutral placement ghost.
const EXTRACTOR_SCENE := preload("res://construction/extractor_visual.tscn")

var definition: MachineDefinition:
	set(value):
		if definition == value:
			return
		definition = value
		_refresh_presentation()
var turns: int = 0:
	set(value):
		var direction := posmod(value, 4)
		if turns == direction:
			return
		turns = direction
		_refresh_presentation()
# Set before entering the tree. Only the active tool uses ghost compositing.
var is_ghost: bool = false
var _extractor: ExtractorVisual
var _art_container: Node2D
var show_status: bool = false
var status: PlanetWorldState.OperatingStatus = PlanetWorldState.OperatingStatus.INACTIVE:
	set(value):
		if status == value:
			return
		status = value
		_refresh_presentation()


func _ready() -> void:
	_refresh_presentation()


func _exit_tree() -> void:
	# Children stop on exit; refresh after their next entry/ready, too.
	request_ready()


func _refresh_presentation() -> void:
	if not is_node_ready() or not is_inside_tree():
		return
	var illustrated := definition != null and definition.item_id == &"extractor"
	# CanvasGroup.self_modulate fades the completed composite, not its layers.
	modulate = Color.WHITE if illustrated or not is_ghost else Color(1, 1, 1, 0.5)
	if illustrated:
		if _extractor == null:
			if is_ghost:
				var group := CanvasGroup.new()
				group.self_modulate = Color(1, 1, 1, 0.5)
				_art_container = group
			else:
				_art_container = Node2D.new()
			add_child(_art_container)
			_extractor = EXTRACTOR_SCENE.instantiate() as ExtractorVisual
			_art_container.add_child(_extractor)
		_art_container.show()
		_extractor.configure(turns)
		_extractor.set_producing(not is_ghost and status == PlanetWorldState.OperatingStatus.PRODUCING)
	elif _art_container != null:
		_extractor.set_producing(false)
		_art_container.hide()
	queue_redraw()


func _draw() -> void:
	if definition == null or definition.item_id == &"extractor":
		return
	var size := Vector2(definition.footprint_cells) * WorldCoordinates.CONSTRUCTION_SIZE
	var origin := definition.rotated_point(Vector2.ZERO, turns)
	draw_set_transform(origin, posmod(turns, 4) * PI / 2.0)
	if definition.item_id == &"smelter":
		_draw_smelter(size)
	elif definition.item_id == &"fabricator":
		_draw_fabricator(size)
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


func _draw_fabricator(size: Vector2) -> void:
	# A teal assembly bed with a transverse gantry; no physical port promises.
	draw_rect(Rect2(Vector2(4, 4), size - Vector2(8, 8)), Color(0.15, 0.27, 0.29))
	draw_rect(Rect2(Vector2(9, 10), size - Vector2(18, 20)), Color(0.35, 0.53, 0.54))
	draw_rect(Rect2(Vector2(17, 17), size - Vector2(34, 32)), Color(0.13, 0.20, 0.23))
	for x in [12.0, size.x - 12.0]:
		draw_line(Vector2(x, 10), Vector2(x, size.y - 10), Color(0.65, 0.73, 0.73), 4.0)
	draw_rect(Rect2(Vector2(7, 18), Vector2(size.x - 14, 9)), Color(0.73, 0.63, 0.39))
	draw_rect(Rect2(Vector2(size.x / 2.0 - 5, 21), Vector2(10, 15)), Color(0.62, 0.70, 0.71))
