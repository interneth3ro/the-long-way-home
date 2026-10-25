class_name InteractionUI
extends CanvasLayer

@onready var _prompt: Label = $HUD/Prompt
@onready var _response: PanelContainer = $HUD/Response
@onready var _response_text: Label = $HUD/Response/Content/Text


func set_prompt(text: String) -> void:
	_prompt.text = text
	_prompt.visible = not text.is_empty() and not is_response_open()


func is_response_open() -> bool:
	return _response.visible


func show_response(text: String) -> void:
	if text.is_empty():
		return
	_response_text.text = text
	_response.show()
	_prompt.hide()


func dismiss_response() -> void:
	_response.hide()
