extends PanelContainer
## Presentation-only framing. Pair with assets/ui/b1_refined_panel.tres.
## Draws inside the panel's existing padding; adds no input surface or minimum size.

const OUTER_EDGE := Color(0.035, 0.055, 0.065, 0.95)
const METAL_EDGE := Color(0.38, 0.45, 0.46, 0.85)
const INNER_EDGE := Color(0.20, 0.34, 0.36, 0.65)
const TOP_HIGHLIGHT := Color(0.58, 0.64, 0.63, 0.45)
const CORNER_ACCENT := Color(0.72, 0.46, 0.23, 0.85)


func _ready() -> void:
	resized.connect(queue_redraw)


func _draw() -> void:
	if size.x < 24.0 or size.y < 24.0:
		return
	# Parallel chamfers: the frame never extends beyond the actual Control bounds.
	draw_polyline(_outline(0.5, 7.0), OUTER_EDGE, 1.0, true)
	draw_polyline(_outline(1.5, 6.0), METAL_EDGE, 1.0, true)
	draw_polyline(_outline(4.5, 3.0), INNER_EDGE, 1.0, true)
	draw_line(Vector2(8.0, 2.5), Vector2(size.x - 8.0, 2.5), TOP_HIGHLIGHT, 1.0, true)
	# Short copper inlays, without glow or additional corner hardware.
	for corner in [Vector2.ZERO, Vector2(size.x, 0), size, Vector2(0, size.y)]:
		var inward := Vector2(1.0 if corner.x == 0 else -1.0,
			1.0 if corner.y == 0 else -1.0)
		var points := PackedVector2Array([
			corner + Vector2(3.0, 9.0) * inward,
			corner + Vector2(3.0, 7.0) * inward,
			corner + Vector2(7.0, 3.0) * inward,
			corner + Vector2(9.0, 3.0) * inward,
		])
		draw_polyline(points, CORNER_ACCENT, 1.5, true)


func _outline(inset: float, chamfer: float) -> PackedVector2Array:
	var right := size.x - inset
	var bottom := size.y - inset
	return PackedVector2Array([
		Vector2(inset + chamfer, inset), Vector2(right - chamfer, inset),
		Vector2(right, inset + chamfer), Vector2(right, bottom - chamfer),
		Vector2(right - chamfer, bottom), Vector2(inset + chamfer, bottom),
		Vector2(inset, bottom - chamfer), Vector2(inset, inset + chamfer),
		Vector2(inset + chamfer, inset),
	])
