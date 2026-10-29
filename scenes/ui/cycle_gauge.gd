extends Control

# Presentation only: the caller supplies simulation progress and status color.
var _fraction: float = 0.0
var _accent := Color(0.282, 0.663, 0.682)


func _ready() -> void:
	resized.connect(queue_redraw)


func set_progress(fraction: float, accent: Color) -> void:
	var bounded := clampf(fraction, 0.0, 1.0) if is_finite(fraction) else 0.0
	if is_equal_approx(bounded, _fraction) and _accent == accent:
		return
	_fraction = bounded
	_accent = accent
	queue_redraw()


func _draw() -> void:
	var center := size * 0.5
	var radius := minf(size.x, size.y) * 0.5 - 4.0
	if radius <= 24.0:
		return
	draw_circle(center, radius, Color(0.045, 0.065, 0.075))
	draw_arc(center, radius, 0.0, TAU, 128, Color(0.34, 0.40, 0.41), 1.5, true)
	draw_arc(center, radius - 4.0, 0.0, TAU, 128, Color(0.15, 0.21, 0.23), 1.0, true)
	for tick in range(48):
		var direction := Vector2.from_angle(-PI * 0.5 + TAU * tick / 48.0)
		var tick_length := 6.0 if tick % 4 == 0 else 3.0
		draw_line(center + direction * (radius - 9.0),
			center + direction * (radius - 9.0 - tick_length),
			Color(0.36, 0.43, 0.44), 1.0, true)
	var arc_radius := radius - 22.0
	draw_arc(center, arc_radius, -PI * 0.5, PI * 1.5, 128,
		Color(0.12, 0.20, 0.22), 5.0, true)
	if _fraction > 0.0:
		draw_arc(center, arc_radius, -PI * 0.5, -PI * 0.5 + TAU * _fraction,
			128, _accent, 5.0, true)
	var font := get_theme_font("font", "Label")
	var value := "%d%%" % roundi(_fraction * 100.0)
	var font_size := 30
	var width := font.get_string_size(value, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x
	draw_string(font, center + Vector2(-width * 0.5, font.get_ascent(font_size) * 0.3),
		value, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, Color(0.92, 0.94, 0.91))
