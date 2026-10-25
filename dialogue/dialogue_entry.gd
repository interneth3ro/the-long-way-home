class_name DialogueEntry
extends Resource

@export var entry_id: StringName = &""
@export var speaker_id: StringName = &""
@export var speaker_display_name: String = ""
@export_multiline var text: String = ""


func is_valid() -> bool:
	return not String(entry_id).strip_edges().is_empty() \
		and not String(speaker_id).strip_edges().is_empty() \
		and not speaker_display_name.strip_edges().is_empty() \
		and not text.strip_edges().is_empty()
