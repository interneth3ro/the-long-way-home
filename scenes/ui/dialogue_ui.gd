class_name DialogueUI
extends CanvasLayer

signal conversation_completed(conversation_id: StringName)
signal conversation_dismissed(conversation_id: StringName)

@onready var _panel: PanelContainer = $HUD/Conversation
@onready var _speaker: Label = $HUD/Conversation/Content/Speaker
@onready var _text: Label = $HUD/Conversation/Content/Text
@onready var _next: Button = $HUD/Conversation/Content/Actions/Next

var _conversation: DialogueConversation
var _entry_index: int = 0


func is_conversation_open() -> bool:
	return _conversation != null


func show_conversation(conversation: DialogueConversation) -> bool:
	if is_conversation_open() or conversation == null or not conversation.is_valid():
		return false
	_conversation = conversation
	_entry_index = 0
	_show_entry()
	_panel.show()
	return true


func advance() -> void:
	if not is_conversation_open():
		return
	if _entry_index == _conversation.entries.size() - 1:
		var completed_id := _conversation.conversation_id
		_close()
		conversation_completed.emit(completed_id)
	else:
		_entry_index += 1
		_show_entry()


func dismiss() -> void:
	if not is_conversation_open():
		return
	var dismissed_id := _conversation.conversation_id
	_close()
	conversation_dismissed.emit(dismissed_id)


func _show_entry() -> void:
	var entry := _conversation.entries[_entry_index]
	_speaker.text = entry.speaker_display_name
	_text.text = entry.text
	_next.text = "Finish (E)" if _entry_index == _conversation.entries.size() - 1 else "Next (E)"


func _close() -> void:
	_panel.hide()
	_conversation = null
	_entry_index = 0
