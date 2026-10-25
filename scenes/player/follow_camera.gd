extends Camera2D

const MIN_ZOOM: float = 0.75
const MAX_ZOOM: float = 1.5
const ZOOM_STEP: float = 0.1
const ZOOM_DURATION: float = 0.15

var _target_zoom: float = 1.0
var _zoom_tween: Tween


func _unhandled_input(event: InputEvent) -> void:
	if not event is InputEventMouseButton:
		return
	if not event.pressed:
		return

	var zoom_change: float
	match event.button_index:
		MOUSE_BUTTON_WHEEL_UP:
			zoom_change = ZOOM_STEP
		MOUSE_BUTTON_WHEEL_DOWN:
			zoom_change = -ZOOM_STEP
		_:
			return

	get_viewport().set_input_as_handled()
	var next_zoom := clampf(_target_zoom + zoom_change, MIN_ZOOM, MAX_ZOOM)
	if is_equal_approx(next_zoom, _target_zoom):
		return
	_target_zoom = next_zoom

	# Retarget from the current visual zoom, accumulating rapid scrolls on the target.
	if _zoom_tween and _zoom_tween.is_valid():
		_zoom_tween.kill()
	_zoom_tween = create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	_zoom_tween.tween_property(self, "zoom", Vector2.ONE * _target_zoom, ZOOM_DURATION)
