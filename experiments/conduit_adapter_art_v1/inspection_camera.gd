extends "res://experiments/conduit_bridge_layering_v1/inspection_camera.gd"

# Inherit boards 1-3, pan, gameplay zoom, Home and cursor-centered C close-up.
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode in [KEY_4, KEY_5]:
			_set_view(Vector2(640, 360 + (event.keycode - KEY_1) * 768), 1.0)
			get_viewport().set_input_as_handled()
			return
	super(event)
