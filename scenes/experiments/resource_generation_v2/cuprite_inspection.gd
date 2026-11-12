extends Node2D
## Explicit editor-only standalone inspection. Never instanced by ordinary gameplay.

const Generator = preload("res://scenes/world/starting_resource_generator.gd")
const Context = preload("res://scenes/world/resource_generation_crash_site.gd")
const Presenter = preload("res://scenes/world/resource_presenter_v2.gd")
const FERRITE = preload("res://scenes/world/resource_definitions/v2/ferrite.tres")
const CARBITE = preload("res://scenes/world/resource_definitions/v2/carbite.tres")
const CUPRITE = preload("res://scenes/world/resource_definitions/v2/cuprite.tres")
const AREA_SIZE := Vector2(4096, 4096)

@export var development_inspection_enabled: bool = false
# Same default seed as PlaythroughState/PlanetWorldState; never writes either.
@export var world_seed: int = 26026
var _generator: StartingResourceGenerator
var _presenter: ResourcePresenterV2
var _token: int = 0
var _center := Vector2.INF
var _anchors: Array[Rect2] = []
var _running: bool = false
@onready var _camera: Camera2D = $Camera2D


func _ready() -> void:
	set_process(false)
	if not development_inspection_enabled or not OS.has_feature("editor") \
			or get_tree().current_scene != self:
		$HUD/Instructions.text = "Cuprite inspection disabled. See docs/RESOURCE_GENERATION_V2_PRESENTATION.md."
		return
	var definitions: Array[WorldResourceDefinition] = [FERRITE, CARBITE, CUPRITE]
	_generator = Generator.new(world_seed, definitions, Context.protected_bounds(), Context.SHIP_REFERENCE)
	if not _generator.is_ready():
		_stop(_generator.initialization_error())
		return
	var reserved := _generator.reservations()
	var counts := {"ferrite": 0, "carbite": 0, "cuprite": 0}
	for location: Dictionary in reserved.locations:
		counts[location.resource_type] += location.deposits.size()
		if location.resource_type == "cuprite":
			for member: Dictionary in location.deposits:
				_anchors.append(Rect2(Vector2(member.anchor_cells.position) * 32, Vector2(128, 128)))
	if counts != Generator.REQUIRED:
		_stop("Complete seven-deposit reservation policy required")
		return
	_presenter = Presenter.new()
	add_child(_presenter)
	# Presentation subset only. Generator retains ALL three definitions/seven members.
	var configured := _presenter.configure(_generator, world_seed, [CUPRITE])
	if not configured.ok:
		_stop(configured.error)
		return
	_camera.position = Context.SHIP_REFERENCE
	_running = true
	set_process(true)
	queue_redraw()


func _process(delta: float) -> void:
	var direction := Vector2(float(Input.is_physical_key_pressed(KEY_RIGHT)) - float(Input.is_physical_key_pressed(KEY_LEFT)),
		float(Input.is_physical_key_pressed(KEY_DOWN)) - float(Input.is_physical_key_pressed(KEY_UP)))
	_camera.position += direction.limit_length() * 800.0 * minf(delta, 0.1)
	# Quantized movement avoids cancelling every frame; requested area stays bounded.
	var center := (_camera.position / 512.0).floor() * 512.0
	if center != _center:
		_center = center
		var requested := _presenter.request(Rect2(center - AREA_SIZE / 2, AREA_SIZE))
		if not requested.ok:
			_stop(requested.get("error", "Inspection query failed"))
			return
		_token = requested.token
	# Fixed work count, never a while loop or performance/latency claim.
	var result := _presenter.step(_token)
	if not result.ok:
		_stop(result.error)


func _draw() -> void:
	if not _running:
		return
	for anchor in _anchors:
		draw_rect(anchor, Color(0.2, 0.9, 0.9, 0.8), false, 2.0)
		draw_circle(anchor.get_center(), 4.0, Color.CYAN)
	# Ship reference marker only; no scene, collision or legacy resource is loaded.
	draw_circle(Context.SHIP_REFERENCE, 12.0, Color.WHITE, false, 2.0)


func _stop(message: String) -> void:
	_running = false
	set_process(false)
	if _presenter != null:
		_presenter.dispose()
	$HUD/Instructions.text = "Cuprite inspection stopped: " + message
	push_error(message)
	queue_redraw()
