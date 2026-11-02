extends StaticBody2D

# Exterior-only travel. Retain this body and its construction layer/terrain anchor.
@export_file("*.tscn") var source_scene: String
@export_file("*.tscn") var destination_scene: String
@export var destination_spawn: StringName

const BOARDING_LINE: float = 8.0
const LANE_HALF_WIDTH: float = 22.0
enum EntryState { WAIT_FOR_SEPARATION, ARMED, PENDING, ENTERED }

var _state: EntryState = EntryState.WAIT_FOR_SEPARATION
var _registration_frames: int = 2
var _previous_feet: Vector2
var _has_previous: bool = false

@onready var _sensor: Area2D = $BoardingSensor
@onready var _blocker: CollisionShape2D = $CollisionShape2D
@onready var _visual: ExteriorHatchVisual = $"../CrashedShip/HatchVisual"
@onready var _controller: SceneTransitionController = get_tree().get_first_node_in_group(&"scene_transitions") as SceneTransitionController


func _enter_tree() -> void:
	_reset_entry()


func _reset_entry() -> void:
	_state = EntryState.WAIT_FOR_SEPARATION
	_registration_frames = 2
	_has_previous = false


func prepare_for_arrival() -> void:
	_reset_entry()
	_visual.prepare_for_arrival()
	# Arrival preparation runs under the transition lock, before reveal.
	set_deferred("collision_layer", 4)


func _physics_process(_delta: float) -> void:
	if _controller == null:
		return
	var world := _controller.get_current_world()
	if _controller.is_transitioning() or world == null or not world.is_ancestor_of(self):
		_reset_entry()
		return
	if _registration_frames > 0:
		_registration_frames -= 1
		return
	var player := _controller.player
	_update_blocker(player)
	var feet := to_local(player.global_position)
	var overlapping := _sensor.get_overlapping_bodies().has(player)
	if _state == EntryState.WAIT_FOR_SEPARATION or _state == EntryState.ENTERED:
		# Require southern separation after fresh physics registration, including
		# rejected/cancelled travel and cached-world rollback. Never arm inside.
		if not overlapping and feet.y > 16.0:
			_state = EntryState.ARMED
	elif player.can_process():
		var crossed := _has_previous and _crossed_inward(_previous_feet, feet)
		if crossed:
			_state = EntryState.PENDING
		if _state == EntryState.PENDING:
			# A deliberate crossing may wait for readiness, but leaving cancels it.
			var within_threshold := absf(feet.x) <= LANE_HALF_WIDTH and feet.y >= 0.0 and feet.y <= BOARDING_LINE
			if not within_threshold and not (crossed and _visual.is_boarding_ready()):
				_state = EntryState.WAIT_FOR_SEPARATION
			elif _visual.is_boarding_ready():
				_state = EntryState.ENTERED
				_controller.request_transition(source_scene, destination_scene,
					destination_spawn, SceneTransitionController.Presentation.QUICK_FADE)
	_previous_feet = feet
	_has_previous = true


func _crossed_inward(previous: Vector2, current: Vector2) -> bool:
	if previous.y <= BOARDING_LINE or current.y > BOARDING_LINE or current.y >= previous.y:
		return false
	# Interpolate the actual movement segment; fast/diagonal steps cannot skip
	# the narrow sensor or accept a crossing beyond the center clearance lane.
	var fraction := (BOARDING_LINE - previous.y) / (current.y - previous.y)
	var crossing_x := lerpf(previous.x, current.x, fraction)
	return absf(crossing_x) <= LANE_HALF_WIDTH


func _update_blocker(player: CharacterBody2D) -> void:
	if _visual.is_boarding_ready():
		set_deferred("collision_layer", 4)
	elif _visual.openness == 0.0 and not _doorway_occupied(player):
		# Restore only at the closed endpoint and with fresh occupancy clearance.
		# Layer 3 stays active for construction throughout the complete animation.
		set_deferred("collision_layer", 5)


func _doorway_occupied(player: CharacterBody2D) -> bool:
	var query := PhysicsShapeQueryParameters2D.new()
	query.shape = _blocker.shape
	query.transform = _blocker.global_transform
	query.margin = 4.0
	query.collision_mask = 1
	query.collide_with_areas = false
	query.exclude = [get_rid()]
	for hit in get_world_2d().direct_space_state.intersect_shape(query):
		if hit["collider"] == player:
			return true
	return false
