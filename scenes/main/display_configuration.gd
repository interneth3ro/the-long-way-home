extends Node

# Session-only window geometry; gameplay and UI scale do not depend on this node.
var _windowed_size := Vector2i(1280, 720)
var _windowed_position := Vector2i.ZERO
var _return_maximized: bool = false
var _switching: bool = false


func _ready() -> void:
	var window := get_window()
	window.min_size = Vector2i(1024, 576)
	_windowed_size = window.size
	_windowed_position = window.position
	window.size_changed.connect(_remember_windowed_geometry)


func _remember_windowed_geometry() -> void:
	var window := get_window()
	if not _switching and window.mode == Window.MODE_WINDOWED:
		_windowed_size = window.size
		_windowed_position = window.position


func _input(event: InputEvent) -> void:
	if event.is_echo() or not event.is_action_pressed("toggle_fullscreen"):
		return
	get_viewport().set_input_as_handled()
	if not _switching:
		_toggle_fullscreen()


func _toggle_fullscreen() -> void:
	var window := get_window()
	_switching = true
	if window.mode == Window.MODE_FULLSCREEN:
		window.mode = Window.MODE_WINDOWED
		# Let the native window leave fullscreen before restoring desktop geometry.
		await get_tree().process_frame
		var usable := DisplayServer.screen_get_usable_rect(window.current_screen)
		var restored_size := _windowed_size.min(usable.size)
		window.size = restored_size
		# Keep the client rectangle reachable if a monitor was removed or resized.
		window.position = _windowed_position.clamp(usable.position,
			usable.end - restored_size)
		if _return_maximized:
			window.mode = Window.MODE_MAXIMIZED
	else:
		_return_maximized = window.mode == Window.MODE_MAXIMIZED
		if window.mode == Window.MODE_WINDOWED:
			_windowed_size = window.size
			_windowed_position = window.position
		# MODE_FULLSCREEN is decorated-free, nonexclusive fullscreen on Windows.
		window.mode = Window.MODE_FULLSCREEN
	await get_tree().process_frame
	_switching = false
