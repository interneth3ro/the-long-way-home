class_name ObjectiveDefinition
extends Resource

@export var objective_id: StringName = &""
@export var title: String = ""
@export_multiline var description: String = ""


func is_valid() -> bool:
	return not String(objective_id).strip_edges().is_empty() \
		and not title.strip_edges().is_empty() \
		and not description.strip_edges().is_empty()
