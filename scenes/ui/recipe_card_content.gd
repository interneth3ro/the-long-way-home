extends MarginContainer

# Presentation inside the existing Button; it never connects selection callbacks.
const CARD_THEME = preload("res://assets/ui/recipe_chooser.tres")
const AMBER := Color(0.773, 0.545, 0.322)
var _button: Button


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
		icon.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
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
	var inputs := _material_area("INPUT")
	for ingredient in recipe.ingredients:
		inputs.add_child(_label("%d %s" % [ingredient.quantity,
			ingredient.item.display_name], 16))
	rows.add_child(inputs)
	var divider := HSeparator.new()
	divider.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var line := StyleBoxLine.new()
	line.color = Color(0.52, 0.40, 0.27, 0.5)
	line.thickness = 1
	divider.add_theme_stylebox_override("separator", line)
	divider.add_theme_constant_override("separation", 2)
	rows.add_child(divider)
	var output := _material_area("OUTPUT")
	output.add_child(_label("%d %s" % [recipe.output_quantity,
		recipe.output_item.display_name], 16))
	rows.add_child(output)
	resized.connect(_fit_button)
	minimum_size_changed.connect(_fit_button)
	_fit_button()


func _label(value: String, font_size: int) -> Label:
	var label := Label.new()
	label.text = value
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.add_theme_font_size_override("font_size", font_size)
	return label


func _material_area(heading: String) -> VBoxContainer:
	var area := VBoxContainer.new()
	area.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	area.mouse_filter = Control.MOUSE_FILTER_IGNORE
	area.add_theme_constant_override("separation", 2)
	var caption := _label(heading, 13)
	caption.theme_type_variation = &"B1MutedLabel"
	area.add_child(caption)
	return area


func _fit_button() -> void:
	# Wrapped content determines height; the ScrollContainer bounds the list.
	_button.custom_minimum_size = Vector2(0, maxf(100.0, get_combined_minimum_size().y))
