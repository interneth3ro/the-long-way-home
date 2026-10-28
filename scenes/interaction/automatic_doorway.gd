class_name AutomaticDoorway
extends Area2D

@export_file("*.tscn") var destination_scene: String
@export var destination_spawn: StringName
@export var presentation: SceneTransitionController.Presentation = SceneTransitionController.Presentation.QUICK_FADE

enum EntryState { WAIT_FOR_SEPARATION, ARMED, ENTERED }

var _state: EntryState = EntryState.WAIT_FOR_SEPARATION
# Physics registration synchronization, not a gameplay cooldown. Never arm from
# stale empty overlap data when a cached world is reattached or Dave is moved.
var _registration_frames: int = 2


func _enter_tree() -> void:
	_reset_entry()


func _reset_entry() -> void:
	_state = EntryState.WAIT_FOR_SEPARATION
	_registration_frames = 2


func _physics_process(_delta: float) -> void:
	var controller := get_tree().get_first_node_in_group(&"scene_transitions") as SceneTransitionController
	if controller == null:
		return
	var world := controller.get_current_world()
	if controller.is_transitioning() or world == null or not world.is_ancestor_of(self):
		_reset_entry()
		return
	if _registration_frames > 0:
		_registration_frames -= 1
		return
	# Area2D aggregates body shapes. No exit signal from one of several overlapping
	# shapes can falsely arm us; deferred entry/exit signals do not drive requests.
	var overlapping := get_overlapping_bodies().has(controller.player)
	if not overlapping:
		_state = EntryState.ARMED
	elif _state == EntryState.ARMED and controller.player.can_process():
		_state = EntryState.ENTERED
		# Even on rejection, stepping out rearms the entry. Never spin requests
		# every frame while Dave stays inside an invalid doorway.
		controller.request_transition(world.scene_file_path, destination_scene,
			destination_spawn, presentation)
