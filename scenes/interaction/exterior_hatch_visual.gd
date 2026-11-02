class_name ExteriorHatchVisual
extends Node2D

# Presentation only. Exterior boarding reads readiness; it owns collision/travel.
const OPEN_SECONDS: float = 0.6
const CLOSE_SECONDS: float = 0.7
const CLOSE_DELAY: float = 1.0
const DOOR_TRAVEL := Vector2(10, -140)

var openness: float = 0.0
var _target_open: bool = false
var _outside_seconds: float = 0.0
var _registration_frames: int = 2

@onready var _approach: Area2D = $Approach
@onready var _hold_open: Area2D = $HoldOpen
@onready var _door: Sprite2D = $Artwork/Recess/Door
@onready var _transitions: SceneTransitionController = get_tree().get_first_node_in_group(&"scene_transitions") as SceneTransitionController


func _enter_tree() -> void:
	# Cached exterior reattachment must not consume stale empty overlap data.
	_registration_frames = 2
	_outside_seconds = 0.0


func is_boarding_ready() -> bool:
	return openness == 1.0


func prepare_for_arrival() -> void:
	# Explicitly initialize cached as well as fresh arrivals before reveal.
	openness = 1.0
	_target_open = true
	_outside_seconds = 0.0
	_registration_frames = 2
	_door.position = DOOR_TRAVEL


func _physics_process(delta: float) -> void:
	if _transitions == null or _transitions.is_transitioning():
		_registration_frames = 2
		return
	var world := _transitions.get_current_world()
	if world == null or not world.is_ancestor_of(self):
		return
	if _registration_frames > 0:
		_registration_frames -= 1
		return
	var player := _transitions.player
	var approaching := _approach.get_overlapping_bodies().has(player)
	var holding := _hold_open.get_overlapping_bodies().has(player)
	_update_proximity(delta, approaching, holding)


func _update_proximity(delta: float, approaching: bool, holding: bool) -> void:
	if approaching or (holding and (_target_open or openness > 0.0)):
		_target_open = true
		_outside_seconds = 0.0
	elif _target_open:
		# Continue opening during the delay. Split a boundary frame so closing
		# consumes only time AFTER the full one-second grace period expires.
		var grace := minf(delta, maxf(0.0, CLOSE_DELAY - _outside_seconds))
		_advance_animation(grace)
		_outside_seconds += delta
		if _outside_seconds >= CLOSE_DELAY:
			_target_open = false
			_advance_animation(delta - grace)
		return
	_advance_animation(delta)


func _advance_animation(delta: float) -> void:
	# Fixed travel rates preserve position on reversal and scale remaining time
	# by remaining distance. No tween restarts, endpoint toggles or sprite swaps.
	var duration := OPEN_SECONDS if _target_open else CLOSE_SECONDS
	var target := 1.0 if _target_open else 0.0
	openness = move_toward(openness, target, delta / duration)
	_door.position = DOOR_TRAVEL * openness
