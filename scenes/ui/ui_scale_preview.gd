extends CanvasLayer

# Temporary comparison aid: editor executable only, absent in exported games.
# Deliberately outside the scaled roots and independent of B1/B2 resources.
const PREFERENCES := [0.75, 0.85, 1.0]


func _ready() -> void:
	if not OS.has_feature("editor"):
		queue_free()
		return
	var panel := PanelContainer.new()
	panel.anchor_left = 0.5
	panel.anchor_right = 0.5
	panel.offset_left = -180
	panel.offset_right = 180
	panel.offset_top = 8
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	panel.mouse_force_pass_scroll_events = false
	add_child(panel)
	var row := HBoxContainer.new()
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(row)
	var label := Label.new()
	label.text = "DEV UI scale"
	label.add_theme_font_size_override("font_size", 14)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(label)
	var buttons := ButtonGroup.new()
	for value: float in PREFERENCES:
		var button := Button.new()
		button.text = "%d%%" % roundi(value * 100)
		button.custom_minimum_size = Vector2(60, 30)
		button.add_theme_font_size_override("font_size", 14)
		button.toggle_mode = true
		button.button_group = buttons
		button.button_pressed = is_equal_approx(value, UIScaleRoot.get_preference())
		button.focus_mode = Control.FOCUS_NONE
		button.mouse_filter = Control.MOUSE_FILTER_STOP
		button.mouse_force_pass_scroll_events = false
		button.pressed.connect(_select_preference.bind(value))
		row.add_child(button)


func _select_preference(value: float) -> void:
	UIScaleRoot.set_preference(value, get_tree())
