extends Node2D
## Standalone owner inspection only. Never attached to the production exterior.

const Generator = preload("res://scenes/world/starting_resource_generator.gd")
const Context = preload("res://scenes/world/resource_generation_crash_site.gd")
const FERRITE = preload("res://scenes/experiments/resource_generation_v2/ferrite_preview.tres")
const CARBITE = preload("res://scenes/world/resource_definitions/v2/carbite.tres")
const CUPRITE = preload("res://scenes/world/resource_definitions/v2/cuprite.tres")
const WORLD_SEED: int = 26026
const AREA_SIZE := Vector2(2048, 2048)

@export var development_inspection_enabled: bool = false
var _generator: StartingResourceGenerator
var _ground: PlanetGenerator
var _presenter: ResourcePresenterV2
var _terrain: ContinuousTerrainPresenter
var _tint: ImageTexture
var _chunks: Array[Vector2i] = []
var _chunk_index: int = 0
var _chunk_started: bool = false
var _targets: Array[Dictionary] = []
var _selection: int = 0
var _token: int = 0
var _running: bool = false
var _show_anchors: bool = true
@onready var _camera: FollowCamera = $Camera2D


func _ready() -> void:
	set_process(false)
	if not development_inspection_enabled or not OS.has_feature("editor") \
			or get_tree().current_scene != self:
		$HUD/Instructions.text = "Standalone editor preview disabled. See docs/RESOURCE_GENERATION_V2_PRESENTATION.md."
		return
	var definitions: Array[WorldResourceDefinition] = [FERRITE, CARBITE, CUPRITE]
	_generator = Generator.new(WORLD_SEED, definitions, Context.protected_bounds(), Context.SHIP_REFERENCE)
	if not _generator.is_ready():
		_stop(_generator.initialization_error())
		return
	var reserved := _generator.reservations()
	var counts := {"ferrite": 0, "carbite": 0, "cuprite": 0}
	for location: Dictionary in reserved.locations:
		for member: Dictionary in location.deposits:
			counts[location.resource_type] += 1
			_targets.append({"resource": location.resource_type,
				"anchor": Rect2(Vector2(member.anchor_cells.position) * 32.0, Vector2(128, 128))})
	if counts != Generator.REQUIRED:
		_stop("Complete seven-deposit reservations required")
		return
	# Normal procedural terrain/material transitions, without authored crash-site
	# masks, terrain edits, simulation, saves or a live PlanetWorldState.
	_ground = PlanetGenerator.new(WORLD_SEED, [], PackedVector2Array(), PackedVector2Array())
	var image := Image.create(99, 99, false, Image.FORMAT_RGBAF)
	image.fill(Color.WHITE)
	_tint = ImageTexture.create_from_image(image)
	_presenter = ResourcePresenterV2.new()
	add_child(_presenter)
	var configured := _presenter.configure(_generator, WORLD_SEED, definitions)
	if not configured.ok:
		_stop(configured.error)
		return
	_camera.set_exterior_zoom(true)
	_running = true
	_focus(0)
	set_process(_running)


func _focus(index: int) -> void:
	_selection = posmod(index, _targets.size())
	var anchor: Rect2 = _targets[_selection].anchor
	_camera.position = anchor.get_center()
	var requested := _presenter.request(Rect2(anchor.get_center() - AREA_SIZE / 2, AREA_SIZE))
	if not requested.ok:
		_stop(requested.get("error", "Preview request failed"))
		return
	_token = requested.token
	if _terrain != null:
		_terrain.cancel()
		remove_child(_terrain)
		_terrain.free()
	_terrain = ContinuousTerrainPresenter.new()
	_terrain.z_index = -11
	add_child(_terrain)
	var initialized := _terrain.initialize(_tint, 3)
	if not initialized.ok:
		_stop(str(initialized))
		return
	_chunks.clear()
	var center := WorldCoordinates.world_to_chunk(anchor.get_center())
	# Center first, then its eight neighbors. One terrain slice per frame.
	_chunks.append(center)
	for y in range(-1, 2):
		for x in range(-1, 2):
			if x != 0 or y != 0:
				_chunks.append(center + Vector2i(x, y))
	_chunk_index = 0
	_chunk_started = false
	$HUD/Instructions.text = "FERRITE V2 PREVIEW — %s (%d/7)\nTab: next deposit | arrows: pan | wheel: normal exterior zoom | A: anchors\n128x128 cyan anchors; scale 0.225, offset (0,16). Neutral terrain tint. No gameplay." % [
		_targets[_selection].resource.capitalize(), _selection + 1]
	queue_redraw()


func _process(delta: float) -> void:
	var direction := Vector2(float(Input.is_physical_key_pressed(KEY_RIGHT)) - float(Input.is_physical_key_pressed(KEY_LEFT)),
		float(Input.is_physical_key_pressed(KEY_DOWN)) - float(Input.is_physical_key_pressed(KEY_UP)))
	var center: Vector2 = _targets[_selection].anchor.get_center()
	_camera.position = center + (_camera.position + direction.limit_length() * 400.0 * minf(delta, 0.1) - center).clamp(
		Vector2(-320, -320), Vector2(320, 320))
	var result := _presenter.step(_token)
	if not result.ok:
		_stop(result.error)
		return
	if _chunk_index >= _chunks.size():
		return
	var coordinate := _chunks[_chunk_index]
	if not _chunk_started:
		var registered := _terrain.begin_generation(coordinate, _chunk_index + 1, WORLD_SEED)
		if not registered.ok:
			_stop(str(registered))
			return
		_chunk_started = true
	var presented := _terrain.step(coordinate, _chunk_index + 1, Callable(_ground, "sample_ground_material"))
	if not presented.ok:
		_stop(str(presented))
		return
	if not presented.pending:
		_chunk_index += 1
		_chunk_started = false


func _unhandled_input(event: InputEvent) -> void:
	if not _running or not event is InputEventKey or not event.pressed or event.echo:
		return
	if event.physical_keycode == KEY_TAB:
		_focus(_selection + (-1 if event.shift_pressed else 1))
		get_viewport().set_input_as_handled()
	elif event.physical_keycode == KEY_A:
		_show_anchors = not _show_anchors
		queue_redraw()


func _draw() -> void:
	if not _running or not _show_anchors:
		return
	for target: Dictionary in _targets:
		var anchor: Rect2 = target.anchor
		draw_rect(anchor, Color(0.2, 0.9, 0.9, 0.8), false, 2.0)
		draw_circle(anchor.get_center(), 3.0, Color.CYAN)


func _stop(message: String) -> void:
	_running = false
	set_process(false)
	if _presenter != null:
		_presenter.dispose()
	if _terrain != null:
		_terrain.cancel()
	$HUD/Instructions.text = "Ferrite preview stopped: " + message
	push_error(message)
	queue_redraw()
