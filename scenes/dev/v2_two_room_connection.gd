extends Node2D

const DaveController = preload("res://scenes/player/dave.gd")

@onready var _transitions: SceneTransitionController = $SceneTransitions
@onready var _outlines: Node2D = $PhysicsShapeOutlines
@onready var _readout: Label = $PreviewHUD/Readout

var _completed: int = 0


func _ready() -> void:
	var dave := _transitions.player
	_transitions.initialize()
	# Startup faces toward the left exit; reciprocal arrivals face inward.
	dave.set("last_facing", DaveController.Facing.WEST)
	var animation := dave.get_node("Visual/AnimationPlayer") as AnimationPlayer
	animation.play(&"idle_west")
	animation.advance(0.0)
	_transitions.transition_completed.connect(_on_transition_completed)


func _on_transition_completed(_source: String, _destination: String) -> void:
	_completed += 1


func _process(_delta: float) -> void:
	var world := _transitions.get_current_world()
	_outlines.environment = world
	_readout.text = ("DEVELOPMENT ONLY | Two V2 rooms | World 1.25x\n"
		+ "WASD/arrows: move | Wheel: zoom | C: collision/threshold outlines | H: HUD\n"
		+ "%s | busy: %s | completed: %d | Dave: %s" % [
			world.scene_file_path.get_file(), _transitions.is_transitioning(),
			_completed, _transitions.player.global_position])
	queue_redraw()


func _draw() -> void:
	if not is_instance_valid(_outlines) or not _outlines.visible:
		return
	var world := _transitions.get_current_world()
	for doorway in world.get_node("Doorways").get_children():
		var shape_node := doorway.get_node("Shape") as CollisionShape2D
		var rectangle := shape_node.shape as RectangleShape2D
		draw_set_transform_matrix(global_transform.affine_inverse() * shape_node.global_transform)
		draw_rect(Rect2(-rectangle.size * 0.5, rectangle.size), Color(1, 0.4, 0.1, 0.8), false, 2.0)


func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	match event.keycode:
		KEY_C:
			_outlines.visible = not _outlines.visible
		KEY_H:
			_readout.visible = not _readout.visible
		_:
			return
	get_viewport().set_input_as_handled()
