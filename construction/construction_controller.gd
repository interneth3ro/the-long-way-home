class_name ConstructionController
extends Node2D

enum Mode { NONE, CONSTRUCTION, RECOVERY }

@export var player: CharacterBody2D
@export var progression: PlaythroughState
@export var transitions: SceneTransitionController
@export var inventory_ui: InventoryUI
@export_range(0.0, 1024.0, 1.0) var construction_range: float = 160.0
@export_range(0.0, 1024.0, 1.0) var recovery_range: float = 160.0

@onready var _detector: InteractionDetector = player.get_node("InteractionDetector")
@onready var _dialogue: DialogueUI = player.get_node("DialogueUI")
@onready var _interaction: InteractionUI = player.get_node("InteractionUI")
@onready var _hint: Label = $HUD/Root/Hint

var _mode: Mode = Mode.NONE
var _definition: MachineDefinition
var _world: Node2D
var _cell := Vector2i.ZERO
var _turns: int = 0
var _reason: String = ""
var _target: Dictionary = {}
var _ghost: MachineVisual
var _aim_visible: bool = false
var _confirm_requested: bool = false
var _requested_cell := Vector2i.ZERO
var _requested_turns: int = 0
var _requested_id: int = 0


func _ready() -> void:
	z_index = 10
	_ghost = MachineVisual.new()
	_ghost.modulate = Color(1, 1, 1, 0.5)
	_ghost.hide()
	add_child(_ghost)
	transitions.transition_started.connect(cancel)
	inventory_ui.opened.connect(cancel)


# Public entry point independent of inventory layout; future callers can reuse it.
func begin_deployment(definition: MachineDefinition) -> bool:
	if definition == null or not definition.is_valid() or _context_blocked(false):
		return false
	var world := transitions.get_current_world()
	if world == null or progression.inventory.get_quantity(definition.item_id) < 1:
		return false
	cancel()
	inventory_ui.close()
	_world = world
	_definition = definition
	_turns = 0
	_mode = Mode.CONSTRUCTION
	_ghost.definition = definition
	if _world is PlanetExterior:
		_world.set_construction_definition(definition)
	_detector.set_tool_active(true)
	return true


func cancel() -> void:
	if is_instance_valid(_world) and _world is PlanetExterior:
		_world.set_construction_definition(null)
	_mode = Mode.NONE
	_definition = null
	_target = {}
	_confirm_requested = false
	_aim_visible = false
	_ghost.hide()
	_hint.hide()
	_detector.set_tool_active(false)
	queue_redraw()


func _context_blocked(include_inventory: bool = true) -> bool:
	return transitions.is_transitioning() or _dialogue.is_conversation_open() \
		or _interaction.is_response_open() or (include_inventory and inventory_ui.is_open())


func _process(_delta: float) -> void:
	if _context_blocked():
		if _mode != Mode.NONE:
			cancel()
		_hint.hide()
		return
	if _mode == Mode.NONE and not transitions.get_current_world() is PlanetExterior:
		_hint.hide()
		return
	if _mode == Mode.CONSTRUCTION:
		_hint.text = "Deploy: left-click · R rotate · Right-click / Esc cancel"
		if not _reason.is_empty():
			_hint.text += "\n" + _reason
	elif _mode == Mode.RECOVERY:
		_hint.text = "Recovery mode · Left-click machine · Right-click / Esc cancel"
	else:
		_hint.text = "Press B to recover" if not _target.is_empty() else ""
	_hint.visible = not _hint.text.is_empty()


func _input(event: InputEvent) -> void:
	if _mode == Mode.NONE or event.is_echo():
		return
	if event.is_action_pressed("ui_cancel") or (event is InputEventMouseButton \
			and event.pressed and event.button_index == MOUSE_BUTTON_RIGHT):
		cancel()
	elif event.is_action_pressed("construction_rotate") and _mode == Mode.CONSTRUCTION:
		_turns = posmod(_turns + 1, 4)
	elif event.is_action_pressed("interact") or event.is_action_pressed("machine_recovery"):
		pass # Active tools own these events; contextual interaction cannot also fire.
	else:
		return
	get_viewport().set_input_as_handled()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_echo() or _context_blocked():
		return
	var world := transitions.get_current_world()
	if world == null:
		return
	if event.is_action_pressed("machine_recovery") and _mode == Mode.NONE:
		if not world is PlanetExterior:
			return
		_world = world
		_mode = Mode.RECOVERY
		_detector.set_tool_active(true)
	elif _mode != Mode.NONE and event is InputEventMouseButton \
			and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		# GUI gets first refusal; a button click cannot also place/recover a machine.
		_confirm_requested = true
		var point := world.get_local_mouse_position()
		_requested_cell = WorldCoordinates.world_to_construction(point)
		_requested_turns = _turns
		var target := progression.planet.machine_at(point)
		_requested_id = target.get("id", 0)
	else:
		return
	get_viewport().set_input_as_handled()


func _physics_process(_delta: float) -> void:
	if _context_blocked():
		_confirm_requested = false
		_target = {}
		return
	_world = transitions.get_current_world()
	if _world == null:
		return
	_aim_visible = get_viewport().gui_get_hovered_control() == null
	var point := _world.get_local_mouse_position()
	_cell = WorldCoordinates.world_to_construction(point)
	_target = progression.planet.machine_at(point) if _aim_visible and _world is PlanetExterior else {}
	if not _target.is_empty():
		var target_definition: MachineDefinition = _target.definition
		if PlacementRules.distance_to_footprint(_world.to_local(player.global_position),
				target_definition.footprint(_target.cell, _target.turns)) > recovery_range:
			_target = {}
	if _mode == Mode.CONSTRUCTION:
		_reason = PlacementRules.rejection(progression.planet, _definition, _cell,
			_turns, player, _world, construction_range, progression.inventory)
		_ghost.transform = global_transform.affine_inverse() * _world.global_transform \
			* Transform2D(0.0, _definition.footprint(_cell, _turns).position)
		_ghost.turns = _turns
		_ghost.visible = _aim_visible
		_ghost.queue_redraw()
	if _confirm_requested:
		_confirm_requested = false
		if _mode == Mode.CONSTRUCTION:
			if progression.planet.deploy_machine(_definition, _requested_cell, _requested_turns,
					progression.inventory, player, _world, construction_range):
				cancel()
		elif _mode == Mode.RECOVERY:
			if progression.planet.recover_machine(_requested_id, progression.inventory,
					_world.to_local(player.global_position), recovery_range):
				cancel()
	queue_redraw()


func _draw() -> void:
	if not is_instance_valid(_world) or not _aim_visible:
		return
	draw_set_transform_matrix(global_transform.affine_inverse() * _world.global_transform)
	if _mode == Mode.CONSTRUCTION:
		var footprint := _definition.footprint(_cell, _turns)
		var color := Color(0.4, 0.82, 0.53) if _reason.is_empty() else Color(0.94, 0.3, 0.28)
		draw_rect(footprint, Color(color, 0.18))
		draw_rect(footprint, Color(color, 0.85), false, 2.0)
		# The footprint is also a small contextual construction-grid display.
		for x in range(WorldCoordinates.CONSTRUCTION_SIZE, int(footprint.size.x),
				WorldCoordinates.CONSTRUCTION_SIZE):
			draw_line(footprint.position + Vector2(x, 0),
				footprint.position + Vector2(x, footprint.size.y), Color(color, 0.35))
		for y in range(WorldCoordinates.CONSTRUCTION_SIZE, int(footprint.size.y),
				WorldCoordinates.CONSTRUCTION_SIZE):
			draw_line(footprint.position + Vector2(0, y),
				footprint.position + Vector2(footprint.size.x, y), Color(color, 0.35))
	elif _mode == Mode.RECOVERY and not _target.is_empty():
		var definition: MachineDefinition = _target.definition
		var footprint := definition.footprint(_target.cell, _target.turns)
		draw_rect(footprint, Color(0.96, 0.76, 0.4, 0.14))
		draw_rect(footprint, Color(0.96, 0.76, 0.4, 0.9), false, 2.0)
