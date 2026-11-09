class_name MachineVisual
extends Node2D

# Shared adapter for deployed machines and the neutral placement ghost.
const EXTRACTOR_SCENE := preload("res://construction/extractor_visual.tscn")
const SMELTER_SCENE := preload("res://construction/smelter_visual.tscn")

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
var _smelter: SmelterVisual
var _smelter_art_container: Node2D
var _smelter_status: Node2D
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
	var illustrated := definition != null and definition.item_id in [&"extractor", &"smelter"]
	# CanvasGroup.self_modulate fades the completed composite, not its layers.
	modulate = Color.WHITE if illustrated or not is_ghost else Color(1, 1, 1, 0.5)
	if definition != null and definition.item_id == &"extractor":
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
	if definition != null and definition.item_id == &"smelter":
		if _smelter == null:
			if is_ghost:
				var group := CanvasGroup.new()
				group.self_modulate = Color(1, 1, 1, 0.5)
				_smelter_art_container = group
			else:
				_smelter_art_container = Node2D.new()
			add_child(_smelter_art_container)
			_smelter = SMELTER_SCENE.instantiate() as SmelterVisual
			_smelter_art_container.add_child(_smelter)
		_smelter_art_container.show()
		_smelter.configure(turns)
		_smelter.set_operating_status(status, not is_ghost)
	elif _smelter_art_container != null:
		_smelter.reset_thermal()
		_smelter_art_container.hide()
	_refresh_smelter_status()
	queue_redraw()


func _refresh_smelter_status() -> void:
	var visible_status := definition != null and definition.item_id == &"smelter" and show_status and not is_ghost
	if visible_status:
		if _smelter_status == null:
			# Last sibling: above the art, outside its scale and ghost composite.
			_smelter_status = Node2D.new()
			_smelter_status.draw.connect(_draw_smelter_status)
			add_child(_smelter_status)
		var size := Vector2(definition.footprint_cells) * WorldCoordinates.CONSTRUCTION_SIZE
		_smelter_status.position = definition.rotated_point(size - Vector2(13, 13), turns)
		_smelter_status.show()
		_smelter_status.queue_redraw()
	elif _smelter_status != null:
		_smelter_status.hide()


func _draw_smelter_status() -> void:
	_smelter_status.draw_circle(Vector2.ZERO, 3.5, _status_color())


func _status_color() -> Color:
	if status == PlanetWorldState.OperatingStatus.PRODUCING:
		return Color(0.35, 0.78, 0.46)
	if status == PlanetWorldState.OperatingStatus.OUTPUT_FULL:
		return Color(0.94, 0.69, 0.28)
	if status == PlanetWorldState.OperatingStatus.INPUT_EMPTY:
		return Color(0.35, 0.60, 0.90)
	return Color(0.55, 0.58, 0.59)


func _draw() -> void:
	if definition == null or definition.item_id in [&"extractor", &"smelter"]:
		return
	var size := Vector2(definition.footprint_cells) * WorldCoordinates.CONSTRUCTION_SIZE
	var origin := definition.rotated_point(Vector2.ZERO, turns)
	draw_set_transform(origin, posmod(turns, 4) * PI / 2.0)
	if definition.item_id == &"fabricator":
		_draw_fabricator(size)
	if show_status:
		draw_circle(Vector2(size.x - 13, size.y - 13), 3.5, _status_color())


func _draw_fabricator(size: Vector2) -> void:
	# A teal assembly bed with a transverse gantry; no physical port promises.
	draw_rect(Rect2(Vector2(4, 4), size - Vector2(8, 8)), Color(0.15, 0.27, 0.29))
	draw_rect(Rect2(Vector2(9, 10), size - Vector2(18, 20)), Color(0.35, 0.53, 0.54))
	draw_rect(Rect2(Vector2(17, 17), size - Vector2(34, 32)), Color(0.13, 0.20, 0.23))
	for x in [12.0, size.x - 12.0]:
		draw_line(Vector2(x, 10), Vector2(x, size.y - 10), Color(0.65, 0.73, 0.73), 4.0)
	draw_rect(Rect2(Vector2(7, 18), Vector2(size.x - 14, 9)), Color(0.73, 0.63, 0.39))
	draw_rect(Rect2(Vector2(size.x / 2.0 - 5, 21), Vector2(10, 15)), Color(0.62, 0.70, 0.71))
