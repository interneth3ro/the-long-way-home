extends "res://experiments/conduit_art_v1/inspection_camera.gd"

# Inspection only. The inherited camera supplies middle-drag and gameplay zoom.
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_1, KEY_2, KEY_3:
				_set_view(Vector2(640, 360 + (event.keycode - KEY_1) * 768), 1.0)
			KEY_HOME:
				_set_view(position, 1.0)
			KEY_C:
				if zoom.x > MAX_ZOOM:
					_set_view(position, 1.0)
				else:
					_set_view(get_global_mouse_position(), 4.0)
			_:
				super(event)
				return
		get_viewport().set_input_as_handled()
		return
	if zoom.x > MAX_ZOOM and event is InputEventMouseButton:
		if event.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
			# Leave close-up before handing the wheel back to the gameplay camera.
			_set_view(position, 1.0)
	super(event)


func _set_view(center: Vector2, amount: float) -> void:
	if _zoom_tween and _zoom_tween.is_valid():
		_zoom_tween.kill()
	position = center
	_target_zoom = amount
	zoom = Vector2.ONE * amount
