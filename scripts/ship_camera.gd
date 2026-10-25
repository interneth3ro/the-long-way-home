extends Camera2D

@export var minimum_zoom: float = 0.85
@export var maximum_zoom: float = 1.4
@export var zoom_speed: float = 0.6


func _ready() -> void:
	apply_zoom(zoom.x)


func _process(delta: float) -> void:
	var direction := Input.get_axis("zoom_out", "zoom_in")
	apply_zoom(zoom.x + direction * zoom_speed * delta)


func apply_zoom(requested_zoom: float) -> void:
	# A resized viewport must also fit inside the room at the widest zoom.
	var viewport_size := get_viewport_rect().size
	var room_size := Vector2(limit_right - limit_left, limit_bottom - limit_top)
	var fit_zoom: float = maxf(viewport_size.x / room_size.x, viewport_size.y / room_size.y)
	var lower_bound := maxf(minimum_zoom, fit_zoom)
	var value := clampf(requested_zoom, lower_bound, maxf(maximum_zoom, lower_bound))
	zoom = Vector2.ONE * value
