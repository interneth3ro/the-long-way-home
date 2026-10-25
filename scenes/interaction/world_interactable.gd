class_name WorldInteractable
extends StaticBody2D

@export var interaction_prompt: String = ""
@export_multiline var inspection_response: String = ""
@export var interaction_enabled: bool = true
@export var interaction_point: Vector2 = Vector2.ZERO


func can_interact() -> bool:
	return interaction_enabled and not inspection_response.is_empty()


func interact() -> String:
	if not can_interact():
		return ""
	return inspection_response
