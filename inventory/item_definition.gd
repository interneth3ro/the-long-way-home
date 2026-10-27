class_name ItemDefinition
extends Resource

enum Section { MATERIALS, EQUIPMENT }

@export var item_id: StringName
@export var display_name: String
# Presentation metadata only; all items share the same quantity storage.
@export var section: Section = Section.MATERIALS


func is_valid() -> bool:
	return not String(item_id).strip_edges().is_empty() and not display_name.strip_edges().is_empty()
