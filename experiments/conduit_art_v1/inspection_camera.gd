extends "res://scenes/player/follow_camera.gd"

# Viewing controls only; the scene contains no gameplay or simulation nodes.
func _ready() -> void:
	set_exterior_zoom(true)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_MIDDLE):
		position -= event.relative / zoom
		get_viewport().set_input_as_handled()
		return
	# Preserve the game's 0.1 steps, 0.15-second easing and exterior zoom limits.
	super(event)
