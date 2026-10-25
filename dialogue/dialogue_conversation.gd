class_name DialogueConversation
extends Resource

@export var conversation_id: StringName = &""
@export var entries: Array[DialogueEntry] = []


func is_valid() -> bool:
	if String(conversation_id).strip_edges().is_empty() or entries.is_empty():
		return false
	var entry_ids: Array[StringName] = []
	for entry in entries:
		if entry == null or not entry.is_valid() or entry.entry_id in entry_ids:
			return false
		entry_ids.append(entry.entry_id)
	return true
