class_name InteractionDetector
extends Area2D

@export var interaction_ui: InteractionUI
@export var dialogue_ui: DialogueUI
# Machine inspection has its own range, independent of construction/recovery.
@export_range(1.0, 256.0, 1.0) var machine_interaction_range: float = 96.0
var machine_panel: Node

@onready var _player: CharacterBody2D = get_parent()
@onready var _range_shape: CircleShape2D = $CollisionShape2D.shape

var _target: WorldInteractable
var _machine_target: DeployedMachine
var _interaction_requested: bool = false
var _tool_active: bool = false


func set_tool_active(active: bool) -> void:
	_tool_active = active
	if active:
		clear_for_transition()


func clear_for_transition() -> void:
	_interaction_requested = false
	_target = null
	_machine_target = null
	interaction_ui.set_prompt("")
	interaction_ui.dismiss_response()


func _physics_process(_delta: float) -> void:
	if _tool_active or dialogue_ui.is_conversation_open() \
			or (machine_panel != null and machine_panel.interaction_blocked()):
		_interaction_requested = false
		interaction_ui.set_prompt("")
		return
	_refresh_target()
	if _interaction_requested:
		_interaction_requested = false
		if is_instance_valid(_machine_target) and not interaction_ui.is_response_open():
			machine_panel.open_machine(_machine_target.machine_id)
		elif is_instance_valid(_target) and not interaction_ui.is_response_open():
			if _target.has_valid_conversation():
				dialogue_ui.show_conversation(_target.conversation)
				interaction_ui.set_prompt("")
			else:
				interaction_ui.show_response(_target.interact())
				if not is_instance_valid(_target) or not _target.can_interact():
					_target = null
					interaction_ui.set_prompt("")


func _unhandled_input(event: InputEvent) -> void:
	if _tool_active or event.is_echo():
		return
	if dialogue_ui.is_conversation_open():
		if event.is_action_pressed("ui_cancel"):
			dialogue_ui.dismiss()
		elif event.is_action_pressed("interact"):
			dialogue_ui.advance()
		else:
			return
		get_viewport().set_input_as_handled()
		return
	if machine_panel != null and machine_panel.interaction_blocked():
		return
	if interaction_ui.is_response_open() and event.is_action_pressed("ui_cancel"):
		interaction_ui.dismiss_response()
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("interact"):
		# A new key press closes the response; it cannot also reopen it.
		if interaction_ui.is_response_open():
			interaction_ui.dismiss_response()
		else:
			# Query physics only during the physics callback, including on activation.
			_interaction_requested = true
		get_viewport().set_input_as_handled()


func _refresh_target() -> void:
	_target = null
	_machine_target = null
	var nearest_distance: float = INF
	var maximum_distance_squared := _range_shape.radius * _range_shape.radius
	# Query the current position after movement instead of the cached Area2D overlaps.
	var proximity := PhysicsShapeQueryParameters2D.new()
	proximity.shape = _range_shape
	if machine_panel != null:
		var shape := CircleShape2D.new()
		shape.radius = maxf(_range_shape.radius, machine_interaction_range)
		proximity.shape = shape
	proximity.transform = $CollisionShape2D.global_transform
	proximity.collision_mask = collision_mask
	proximity.collide_with_areas = true
	proximity.exclude = [_player.get_rid()]
	var space := get_world_2d().direct_space_state
	for result in space.intersect_shape(proximity):
		var collider: CollisionObject2D = result["collider"]
		var body := collider as WorldInteractable
		var machine := collider as DeployedMachine
		if body == null and (machine == null or machine_panel == null):
			continue
		if body != null and not body.can_interact():
			continue
		var point: Vector2 = body.to_global(body.interaction_point) if body != null \
			else machine.to_global(machine.interaction_point)
		var distance := global_position.distance_squared_to(point)
		var limit := maximum_distance_squared if body != null else machine_interaction_range * machine_interaction_range
		# Optional target caps use the same global distance for prompt and dispatch.
		if body != null and body.max_interaction_distance > 0.0:
			limit = minf(limit, body.max_interaction_distance * body.max_interaction_distance)
		# The search radius remains the outer limit; target caps can only tighten it.
		if distance > limit or distance >= nearest_distance:
			continue
		# A nonblocking target can coincide with Dave's interaction origin.
		if is_zero_approx(distance):
			_target = body
			_machine_target = machine
			nearest_distance = distance
			continue
		# Keep both areas and bodies in the ray query: the target must be first.
		var query := PhysicsRayQueryParameters2D.create(global_position, point, collision_mask)
		query.exclude = [_player.get_rid()]
		query.collide_with_areas = true
		query.hit_from_inside = true
		var hit := space.intersect_ray(query)
		if hit.get("collider") == collider:
			_target = body
			_machine_target = machine
			nearest_distance = distance
	var prompt: String = ""
	if is_instance_valid(_target):
		prompt = _target.interaction_prompt
	elif is_instance_valid(_machine_target):
		prompt = "E · Inspect " + _machine_target.display_name
	interaction_ui.set_prompt(prompt)
