class_name WorldInteractable
extends CollisionObject2D

# Shared interaction interface for solid bodies and nonblocking areas.

@export var interaction_prompt: String = ""
@export_multiline var inspection_response: String = ""
@export var conversation: DialogueConversation
@export var interaction_enabled: bool = true
@export var interaction_point: Vector2 = Vector2.ZERO


func can_interact() -> bool:
	return interaction_enabled and (has_valid_conversation() or not inspection_response.is_empty())


func has_valid_conversation() -> bool:
	return conversation != null and conversation.is_valid()


func interact() -> String:
	if not can_interact():
		return ""
	return inspection_response
