class_name SceneTransitionController
extends Node

# A future cinematic/musing presenter can listen without owning progression.
signal first_exterior_reveal_completed
signal transition_completed(source_scene: String, destination_scene: String)
signal transition_started

enum Presentation { IMMEDIATE, FIRST_EXTERIOR_REVEAL, QUICK_FADE }

const FADE_SECONDS: float = 0.65
const EXTERIOR_SCENE: String = "res://scenes/world/planet_exterior.tscn"
@export_range(0.01, 1.0, 0.01) var quick_fade_seconds: float = 0.15

@export var player: CharacterBody2D
@export var world_host: Node2D
@export var progression: PlaythroughState

@onready var _curtain: ColorRect = $Fade/Curtain

var _current_world: Node2D
var _worlds: Dictionary[String, Node2D] = {}
var _busy: bool = false
var _quick_active: bool = false
var _quick_cancelled: bool = false
var _quick_committed: bool = false
var _quick_previous_mode: Node.ProcessMode


func _ready() -> void:
	add_to_group(&"scene_transitions")


# Called by the persistent Main after its children are ready.
func initialize() -> void:
	_current_world = world_host.get_child(0) as Node2D
	_worlds[_current_world.scene_file_path] = _current_world
	player.reparent(_current_world.get_node("GroundObjects"))
	_reset_camera()


func is_transitioning() -> bool:
	return _busy


func get_current_world() -> Node2D:
	return _current_world


func request_transition(source_scene: String, destination_scene: String,
		spawn_name: StringName, presentation: Presentation) -> bool:
	if _busy or source_scene != _current_world.scene_file_path or destination_scene == source_scene:
		return false
	_busy = true
	if presentation == Presentation.QUICK_FADE:
		_quick_active = true
		_quick_cancelled = false
		_quick_committed = false
		_quick_previous_mode = player.process_mode
		# Lock synchronously with acceptance, before any deferred tree mutation.
		player.get_node("InteractionDetector").clear_for_transition()
		player.velocity = Vector2.ZERO
		player.process_mode = Node.PROCESS_MODE_DISABLED
	transition_started.emit()
	# The interaction request originates in physics; defer all tree mutations.
	_perform_transition.call_deferred(source_scene, destination_scene, spawn_name, presentation)
	return true


func _perform_transition(source_scene: String, destination_scene: String,
		spawn_name: StringName, presentation: Presentation) -> void:
	if presentation == Presentation.QUICK_FADE:
		await _perform_quick_transition(source_scene, destination_scene, spawn_name)
		return
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
	if destination.has_method("prepare_for_arrival"):
		await destination.call("prepare_for_arrival", player, progression.planet)
	# Camera processing is locked with Dave, so update before the reveal begins.
	_reset_camera()
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


func cancel_quick_transition() -> bool:
	# Once fade-in begins the destination is committed. Before that, finish the
	# current fade under the lock and restore the source while still obscured.
	if _quick_active and not _quick_committed:
		_quick_cancelled = true
		return true
	return false


func _perform_quick_transition(source_scene: String, destination_scene: String,
		spawn_name: StringName) -> void:
	_curtain.show()
	await _fade_to(1.0, quick_fade_seconds)
	if _quick_cancelled:
		await _finish_quick_transition()
		return

	var destination: Node2D = _worlds.get(destination_scene)
	var newly_created := destination == null
	if newly_created and ResourceLoader.exists(destination_scene, "PackedScene"):
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
	if destination == null or destination.scene_file_path != destination_scene \
			or spawn == null or ground_objects == null:
		push_warning("Quick transition rejected: invalid environment or spawn: %s / %s" % [destination_scene, spawn_name])
		if newly_created and destination != null:
			destination.free()
		await _finish_quick_transition()
		return

	var source := _current_world
	var source_position := player.global_position
	player.reparent(world_host)
	world_host.remove_child(source)
	world_host.add_child(destination)
	_worlds[destination_scene] = destination
	_current_world = destination
	player.reparent(ground_objects)
	player.global_position = spawn.global_position
	if destination.has_method("prepare_for_arrival"):
		await destination.call("prepare_for_arrival", player, progression.planet)
	_reset_camera()
	await get_tree().physics_frame
	if _quick_cancelled:
		# Roll back while still opaque, retaining the validated cached destination.
		player.reparent(world_host)
		world_host.remove_child(destination)
		world_host.add_child(source)
		_current_world = source
		player.reparent(source.get_node("GroundObjects"))
		player.global_position = source_position
		_reset_camera()
		await get_tree().physics_frame
	_quick_committed = true
	await _finish_quick_transition()
	if not _quick_cancelled:
		transition_completed.emit(source_scene, destination_scene)


func _reset_camera() -> void:
	var camera := player.get_node("Camera2D") as FollowCamera
	camera.set_exterior_zoom(_current_world.scene_file_path == EXTERIOR_SCENE)
	camera.reset_smoothing()
	camera.force_update_scroll()


func _finish_quick_transition() -> void:
	await _fade_to(0.0, quick_fade_seconds)
	player.velocity = Vector2.ZERO
	player.get_node("InteractionDetector").clear_for_transition()
	_finish_transition(_quick_previous_mode)
	_quick_active = false


func _fade_to(alpha: float, seconds: float = FADE_SECONDS) -> void:
	var tween := create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(_curtain, "color:a", alpha, seconds)
	await tween.finished


func _finish_transition(previous_process_mode: Node.ProcessMode) -> void:
	_curtain.color.a = 0.0
	_curtain.hide()
	player.process_mode = previous_process_mode
	_busy = false


func _exit_tree() -> void:
	if _quick_active and is_instance_valid(player):
		player.velocity = Vector2.ZERO
		player.process_mode = _quick_previous_mode
		_quick_active = false
		_busy = false
		_curtain.color.a = 0.0
		_curtain.hide()
	# Detached environments are owned here rather than by the SceneTree.
	for world in _worlds.values():
		if is_instance_valid(world) and not world.is_inside_tree():
			world.free()
