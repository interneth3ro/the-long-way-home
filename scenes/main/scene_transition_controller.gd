class_name SceneTransitionController
extends Node

# A future cinematic/musing presenter can listen without owning progression.
signal first_exterior_reveal_completed
signal transition_completed(source_scene: String, destination_scene: String)

enum Presentation { IMMEDIATE, FIRST_EXTERIOR_REVEAL }

const FADE_SECONDS: float = 0.65

@export var player: CharacterBody2D
@export var world_host: Node2D
@export var progression: PlaythroughState

@onready var _curtain: ColorRect = $Fade/Curtain

var _current_world: Node2D
var _worlds: Dictionary[String, Node2D] = {}
var _busy: bool = false


func _ready() -> void:
	add_to_group(&"scene_transitions")


# Called by the persistent Main after its children are ready.
func initialize() -> void:
	_current_world = world_host.get_child(0) as Node2D
	_worlds[_current_world.scene_file_path] = _current_world
	player.reparent(_current_world.get_node("GroundObjects"))


func is_transitioning() -> bool:
	return _busy


func request_transition(source_scene: String, destination_scene: String,
		spawn_name: StringName, presentation: Presentation) -> bool:
	if _busy or source_scene != _current_world.scene_file_path or destination_scene == source_scene:
		return false
	_busy = true
	# The interaction request originates in physics; defer all tree mutations.
	_perform_transition.call_deferred(source_scene, destination_scene, spawn_name, presentation)
	return true


func _perform_transition(source_scene: String, destination_scene: String,
		spawn_name: StringName, presentation: Presentation) -> void:
	var previous_process_mode := player.process_mode
	player.get_node("InteractionDetector").clear_for_transition()
	player.velocity = Vector2.ZERO
	player.process_mode = Node.PROCESS_MODE_DISABLED
	_curtain.show()
	var first_reveal := presentation == Presentation.FIRST_EXTERIOR_REVEAL \
		and not progression.first_exterior_reveal_completed
	if first_reveal:
		await _fade_to(1.0)

	# Load/instantiate only once obscured for the first reveal. Detached worlds
	# retain authored scene state, but take no part in physics or processing.
	var destination: Node2D = _worlds.get(destination_scene)
	var newly_created := destination == null
	if newly_created:
		var packed := load(destination_scene) as PackedScene
		if packed != null:
			var instance := packed.instantiate()
			destination = instance as Node2D
			if destination == null:
				instance.free()
	var spawn: Marker2D
	var ground_objects: Node2D
	if destination != null:
		spawn = destination.get_node_or_null("Spawns/" + String(spawn_name)) as Marker2D
		ground_objects = destination.get_node_or_null("GroundObjects") as Node2D
	if spawn == null or ground_objects == null:
		push_error("Transition rejected: invalid environment or spawn: %s / %s" % [destination_scene, spawn_name])
		if newly_created and destination != null:
			destination.free()
		if first_reveal:
			await _fade_to(0.0)
		_finish_transition(previous_process_mode)
		return

	# Keep the same Dave (including facing, animations, camera zoom and UI).
	player.reparent(world_host)
	world_host.remove_child(_current_world)
	world_host.add_child(destination)
	_worlds[destination_scene] = destination
	_current_world = destination
	player.reparent(ground_objects)
	player.global_position = spawn.global_position
	var camera := player.get_node("Camera2D") as Camera2D
	camera.reset_smoothing()
	# Camera processing is locked with Dave, so update before the reveal begins.
	camera.force_update_scroll()
	# Allow one physics frame for the destination's bodies to register before
	# accepting interaction queries. Immediate transitions have no fade/timer.
	await get_tree().physics_frame
	if first_reveal:
		await _fade_to(0.0)
		progression.first_exterior_reveal_completed = true
	_finish_transition(previous_process_mode)
	if first_reveal:
		first_exterior_reveal_completed.emit()
	transition_completed.emit(source_scene, destination_scene)


func _fade_to(alpha: float) -> void:
	var tween := create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(_curtain, "color:a", alpha, FADE_SECONDS)
	await tween.finished


func _finish_transition(previous_process_mode: Node.ProcessMode) -> void:
	_curtain.hide()
	player.process_mode = previous_process_mode
	_busy = false


func _exit_tree() -> void:
	# Detached environments are owned here rather than by the SceneTree.
	for world in _worlds.values():
		if is_instance_valid(world) and not world.is_inside_tree():
			world.free()
