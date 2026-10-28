extends Node2D

const INTERIOR := "res://scenes/dev/ship_interior_v2_transition_world.tscn"
const MAINTENANCE := "res://scenes/dev/transition_test_maintenance.tscn"

@onready var _transitions: SceneTransitionController = $SceneTransitions
@onready var _outlines: Node2D = $PhysicsShapeOutlines
@onready var _readout: Label = $PreviewHUD/Readout

var _completed: int = 0
var _debug_message: String = ""


func _ready() -> void:
	_transitions.initialize()
	_transitions.transition_completed.connect(_on_transition_completed)


func _on_transition_completed(_source: String, _destination: String) -> void:
	_completed += 1


func _process(_delta: float) -> void:
	var world := _transitions.get_current_world()
	_outlines.environment = world
	_readout.text = ("DEVELOPMENT ONLY | Automatic transitions | V2 1.25x\n"
		+ "WASD/arrows: move | Wheel: zoom | C: outlines/thresholds | H: HUD\n"
		+ "F7: missing scene | F8: missing spawn | X: cancel quick transition\n"
		+ "%s | busy: %s | completed: %d | Dave: %s\n%s" % [
			world.scene_file_path.get_file(), _transitions.is_transitioning(),
			_completed, _transitions.player.global_position, _debug_message])
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
		KEY_X:
			_debug_message = "Cancellation accepted: %s (before fade-in only)." % _transitions.cancel_quick_transition()
		KEY_F7, KEY_F8:
			var source := _transitions.get_current_world().scene_file_path
			var target := MAINTENANCE if source == INTERIOR else INTERIOR
			if event.keycode == KEY_F7:
				target = "res://scenes/dev/intentionally_missing_transition_world.tscn"
			var accepted := _transitions.request_transition(source, target,
				&"IntentionallyMissingSpawn", SceneTransitionController.Presentation.QUICK_FADE)
			_debug_message = "Failure probe accepted: %s; expect warning and source recovery." % accepted
		_:
			return
	get_viewport().set_input_as_handled()
