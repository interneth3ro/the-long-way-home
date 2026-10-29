class_name ItemPresentation
extends RefCounted

# Shared provisional artwork for inventory and hotbar; no gameplay state.
const ICONS := {
	&"ferrite_ore": "ORE",
	&"ferrite_ingot": "BAR",
	&"ferrite_plate": preload("res://assets/items/ferrite_plate.svg"),
	&"ferrite_rod": preload("res://assets/items/ferrite_rod.svg"),
	&"extractor": "EX",
	&"smelter": "SM",
	&"fabricator": "FB",
}


static func quantity_text(quantity: int) -> String:
	# Keep exact int64 totals in tooltips; avoid float rounding on the slot.
	var digits := str(quantity)
	if digits.length() <= 3:
		return digits
	var group := int((digits.length() - 1) / 3.0)
	return digits.left(digits.length() - group * 3) + ["", "K", "M", "B", "T", "Qa", "Qi"][group]
