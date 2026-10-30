extends MarginContainer

# Presentation inside the existing Button; it never connects selection callbacks.
const CARD_THEME = preload("res://assets/ui/recipe_chooser.tres")
const AMBER := Color(0.773, 0.545, 0.322)
var _button: Button
var _flow: BoxContainer
var _arrow: Label


func configure(button: Button, recipe: RecipeDefinition, current: bool) -> void:
	_button = button
	button.text = ""
	button.icon = null
	button.theme = CARD_THEME
	button.theme_type_variation = &"B1RecipeCurrent" if current else &"B1RecipeCard"
	button.tooltip_text = "%s\nInput: %s\nOutput: %s" % [recipe.display_name,
		recipe.input_summary(), recipe.output_summary()]
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for edge in ["left", "right", "top", "bottom"]:
		add_theme_constant_override("margin_" + edge, 12)
	var rows := VBoxContainer.new()
	rows.mouse_filter = Control.MOUSE_FILTER_IGNORE
	rows.add_theme_constant_override("separation", 8)
	add_child(rows)
	var header := HBoxContainer.new()
	header.mouse_filter = Control.MOUSE_FILTER_IGNORE
	header.add_theme_constant_override("separation", 8)
	rows.add_child(header)
	if recipe.icon != null:
		var icon := TextureRect.new()
		icon.texture = recipe.icon
		icon.custom_minimum_size = Vector2(32, 32)
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		header.add_child(icon)
	var title := _label(recipe.display_name, 20)
	header.add_child(title)
	if current:
		var badge := _label("CURRENT", 13)
		badge.autowrap_mode = TextServer.AUTOWRAP_OFF
		badge.size_flags_horizontal = Control.SIZE_SHRINK_END
		badge.add_theme_color_override("font_color", AMBER)
		header.add_child(badge)
	_flow = BoxContainer.new()
	_flow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_flow.add_theme_constant_override("separation", 8)
	rows.add_child(_flow)
	var inputs := PackedStringArray()
	for ingredient in recipe.ingredients:
		inputs.append("%d %s" % [ingredient.quantity, ingredient.item.display_name])
	_flow.add_child(_material_area("INPUT", "\n".join(inputs)))
	_arrow = _label("→", 18)
	_arrow.autowrap_mode = TextServer.AUTOWRAP_OFF
	_arrow.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_arrow.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_arrow.add_theme_color_override("font_color", AMBER)
	_flow.add_child(_arrow)
	_flow.add_child(_material_area("OUTPUT", "%d %s" % [recipe.output_quantity,
		recipe.output_item.display_name]))
	resized.connect(_layout_flow)
	minimum_size_changed.connect(_fit_button)
	_layout_flow()


func _label(value: String, font_size: int) -> Label:
	var label := Label.new()
	label.text = value
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.add_theme_font_size_override("font_size", font_size)
	return label


func _material_area(heading: String, material: String) -> VBoxContainer:
	var area := VBoxContainer.new()
	area.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	area.mouse_filter = Control.MOUSE_FILTER_IGNORE
	area.add_theme_constant_override("separation", 2)
	var caption := _label(heading, 13)
	caption.theme_type_variation = &"B1MutedLabel"
	area.add_child(caption)
	area.add_child(_label(material, 16))
	return area


func _layout_flow() -> void:
	# Below two readable material columns, retain full names in a vertical flow.
	var stacked := size.x < 340.0
	_flow.vertical = stacked
	_arrow.text = "↓" if stacked else "→"
	_fit_button()


func _fit_button() -> void:
	# Wrapped content determines height; the ScrollContainer bounds the list.
	_button.custom_minimum_size = Vector2(0, maxf(100.0, get_combined_minimum_size().y))
