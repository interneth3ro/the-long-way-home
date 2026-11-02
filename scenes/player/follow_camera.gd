class_name FollowCamera
extends Camera2D

const MIN_ZOOM: float = 0.75
const EXTERIOR_MIN_ZOOM: float = 0.5
const MAX_ZOOM: float = 1.5
const ZOOM_STEP: float = 0.1
const ZOOM_DURATION: float = 0.15

var _target_zoom: float = 1.0
var _zoom_tween: Tween
var _minimum_zoom: float = MIN_ZOOM


func set_exterior_zoom(is_exterior: bool) -> void:
	_minimum_zoom = EXTERIOR_MIN_ZOOM if is_exterior else MIN_ZOOM
	var clamped_target := clampf(_target_zoom, _minimum_zoom, MAX_ZOOM)
	var clamped_zoom := clampf(zoom.x, _minimum_zoom, MAX_ZOOM)
	if is_equal_approx(clamped_target, _target_zoom) and is_equal_approx(clamped_zoom, zoom.x):
		return
	# Stop an exterior scroll tween before it can write below the interior limit.
	if _zoom_tween and _zoom_tween.is_valid():
		_zoom_tween.kill()
	_target_zoom = clamped_target
	zoom = Vector2.ONE * clamped_zoom
	if not is_equal_approx(clamped_zoom, _target_zoom):
		_tween_to_target()


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
	var next_zoom := clampf(_target_zoom + zoom_change, _minimum_zoom, MAX_ZOOM)
	if is_equal_approx(next_zoom, _target_zoom):
		return
	_target_zoom = next_zoom
	_tween_to_target()


func _tween_to_target() -> void:
	# Retarget from the current visual zoom, accumulating rapid scrolls on the target.
	if _zoom_tween and _zoom_tween.is_valid():
		_zoom_tween.kill()
	_zoom_tween = create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	_zoom_tween.tween_property(self, "zoom", Vector2.ONE * _target_zoom, ZOOM_DURATION)
