extends Area2D

@export var interaction_ui: InteractionUI

@onready var _player: CharacterBody2D = get_parent()
@onready var _range_shape: CircleShape2D = $CollisionShape2D.shape

var _target: WorldInteractable
var _interaction_requested: bool = false


func _physics_process(_delta: float) -> void:
	_refresh_target()
	if _interaction_requested:
		_interaction_requested = false
		if is_instance_valid(_target):
			interaction_ui.show_response(_target.interact())


func _unhandled_input(event: InputEvent) -> void:
	if event.is_echo():
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
	var nearest_distance: float = INF
	var maximum_distance_squared := _range_shape.radius * _range_shape.radius
	# Query the current position after movement instead of the cached Area2D overlaps.
	var proximity := PhysicsShapeQueryParameters2D.new()
	proximity.shape = _range_shape
	proximity.transform = $CollisionShape2D.global_transform
	proximity.collision_mask = collision_mask
	proximity.exclude = [_player.get_rid()]
	var space := get_world_2d().direct_space_state
	for result in space.intersect_shape(proximity):
		var body := result["collider"] as WorldInteractable
		if body == null or not body.can_interact():
			continue
		var point: Vector2 = body.to_global(body.interaction_point)
		var distance := global_position.distance_squared_to(point)
		# The circle's radius is also the explicit maximum distance to the target point.
		if distance > maximum_distance_squared or distance >= nearest_distance:
			continue
		# Keep the target in the ray query: its body must be the first solid hit.
		var query := PhysicsRayQueryParameters2D.create(global_position, point, collision_mask)
		query.exclude = [_player.get_rid()]
		var hit := space.intersect_ray(query)
		if hit.get("collider") == body:
			_target = body
			nearest_distance = distance
	var prompt: String = ""
	if is_instance_valid(_target):
		prompt = _target.interaction_prompt
	interaction_ui.set_prompt(prompt)
