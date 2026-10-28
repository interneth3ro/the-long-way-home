extends Node2D

const DaveController = preload("res://scenes/player/dave.gd")

@onready var _outlines: Node2D = $PhysicsShapeOutlines
@onready var _readout: Label = $PreviewHUD/Readout


func _ready() -> void:
	# Keep the existing movement, camera and radius-10 feet. Isolate interactions.
	$Dave/CollisionShape2D.disabled = false
	$Dave/InteractionDetector.process_mode = Node.PROCESS_MODE_DISABLED
	$Dave/InteractionUI.hide()
	$Dave/DialogueUI.hide()
	$Dave.last_facing = DaveController.Facing.WEST


func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	match event.keycode:
		KEY_C:
			_outlines.visible = not _outlines.visible
			_readout.text = _readout.text.get_slice("Outlines:", 0) + (
				"Outlines: ON" if _outlines.visible else "Outlines: OFF"
			)
		KEY_H:
			_readout.visible = not _readout.visible
		_:
			return
	get_viewport().set_input_as_handled()
