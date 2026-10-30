class_name ItemPresentation
extends RefCounted

# Shared canonical item artwork for inventory and hotbar.
const ICONS := {
	&"ferrite_ore": preload("res://assets/items/ferrite_ore.png"),
	&"ferrite_ingot": preload("res://assets/items/ferrite_ingot.png"),
	&"ferrite_plate": preload("res://assets/items/ferrite_plate.png"),
	&"ferrite_rod": preload("res://assets/items/ferrite_rod.png"),
	&"extractor": preload("res://assets/items/extractor.png"),
	&"smelter": preload("res://assets/items/smelter.png"),
	&"fabricator": preload("res://assets/items/fabricator.png"),
}


static func add_material_icon(label: Label) -> TextureRect:
	# Keep each existing name/quantity row; add an unframed identity group only.
	var parent := label.get_parent()
	var index := label.get_index()
	var identity := HBoxContainer.new()
	identity.size_flags_horizontal = label.size_flags_horizontal
	identity.mouse_filter = Control.MOUSE_FILTER_IGNORE
	identity.add_theme_constant_override("separation", 6)
	parent.add_child(identity)
	parent.move_child(identity, index)
	var icon := TextureRect.new()
	icon.custom_minimum_size = Vector2(24, 24)
	icon.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	icon.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	icon.hide()
	identity.add_child(icon)
	label.reparent(identity, false)
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	return icon


static func set_material_icon(icon: TextureRect, item: ItemDefinition, quantity: int) -> void:
	var artwork: Variant = ICONS.get(item.item_id) if item != null and quantity > 0 else null
	icon.texture = artwork if artwork is Texture2D else null
	icon.visible = icon.texture != null


static func quantity_text(quantity: int) -> String:
	# Keep exact int64 totals in tooltips; avoid float rounding on the slot.
	var digits := str(quantity)
	if digits.length() <= 3:
		return digits
	var group := int((digits.length() - 1) / 3.0)
	return digits.left(digits.length() - group * 3) + ["", "K", "M", "B", "T", "Qa", "Qi"][group]
