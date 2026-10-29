class_name UIScaleRoot
extends Control

# One session preference; CanvasLayers and presenter ownership stay unchanged.
signal scale_changed

const REFERENCE_SIZE := Vector2(1280, 720)
const ROOT_GROUP := &"ui_scale_roots"
static var _preference: float = 1.0


static func get_preference() -> float:
	return _preference


static func set_preference(value: float, tree: SceneTree) -> void:
	if not is_finite(value) or value <= 0.0 or is_equal_approx(value, _preference):
		return
	_preference = value
	tree.call_group(ROOT_GROUP, "_update_scale")


func _ready() -> void:
	add_to_group(ROOT_GROUP)
	# An explicit logical extent replaces viewport-sized root anchors. Child
	# anchors still span the complete screen after the root transform is applied.
	set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
	pivot_offset = Vector2.ZERO
	get_viewport().size_changed.connect(_update_scale)
	_update_scale()


func _update_scale() -> void:
	var ratios := Vector2(get_window().size) / REFERENCE_SIZE
	var stretch := minf(ratios.x, ratios.y)
	if stretch <= 0.0:
		return
	# The root Window already applies S. Multiplying by P / sqrt(S) gives
	# physical scale P * sqrt(S), rather than applying S a second time.
	var multiplier := _preference / sqrt(stretch)
	scale = Vector2.ONE * multiplier
	position = Vector2.ZERO
	size = get_viewport_rect().size / multiplier
	# Re-evaluate hover/tooltips against the new rectangles after container layout.
	get_viewport().update_mouse_cursor_state.call_deferred()
	scale_changed.emit()


static func popup_at_slot(menu: PopupMenu, slot: Control, above: bool = false) -> void:
	# Godot 4.7.2 PopupMenu._pre_popup explicitly derives Window content scale
	# from its parent CanvasItem's global transform. Keep the menu parented to
	# this scaled HUD; do not multiply its content_scale_factor again.
	var attachment_transform := slot.get_global_transform_with_canvas()
	if not menu.is_embedded():
		attachment_transform = slot.get_screen_transform()
	var local_point := Vector2.ZERO if above else Vector2(0, slot.size.y)
	var point := Vector2i((attachment_transform * local_point).round())
	var bounds := menu.get_usable_parent_rect()
	menu.max_size = bounds.size
	menu.reset_size()
	menu.popup(Rect2i(point, Vector2i.ZERO))
	# popup() has now applied the parent-derived scale and measured the window.
	# Above placement uses its actual height, replacing the old fixed 44 offset.
	if above:
		point.y -= menu.size.y
	menu.position = point.clamp(bounds.position, bounds.position.max(bounds.end - menu.size))
