class_name DialogueUI
extends CanvasLayer

signal conversation_completed(conversation_id: StringName)
signal conversation_dismissed(conversation_id: StringName)

const PORTRAITS := {
	&"dave": preload("res://assets/dialogue/portraits/dave_dialogue_portrait.png"),
	&"computer": preload("res://assets/dialogue/portraits/computer_dialogue_portrait.png"),
	&"marvin": preload("res://assets/dialogue/portraits/marvin_dialogue_portrait.png"),
}
const PANEL_WIDTH := 640.0
# Reserve the normal hotbar band even while the bar is hidden.
const BOTTOM_CLEARANCE := 104.0
const EDGE_CLEARANCE := 24.0

@onready var _panel: PanelContainer = $HUD/Conversation
@onready var _speaker: Label = $HUD/Conversation/Content/Entry/Body/Speaker
@onready var _text: Label = $HUD/Conversation/Content/Entry/Body/Scroll/Text
@onready var _scroll: ScrollContainer = $HUD/Conversation/Content/Entry/Body/Scroll
@onready var _portrait: TextureRect = $HUD/Conversation/Content/Entry/Portrait
@onready var _hints: Label = $HUD/Conversation/Content/Actions/Hints
@onready var _next: Button = $HUD/Conversation/Content/Actions/Next

var _conversation: DialogueConversation
var _entry_index: int = 0
var _speaker_id: StringName = &""
var _opening_tween: Tween
var _portrait_tween: Tween
var _layout_queued: bool = false


func _ready() -> void:
	$HUD.scale_changed.connect(_queue_layout)
	_text.minimum_size_changed.connect(_queue_layout)
	_speaker.minimum_size_changed.connect(_queue_layout)
	_panel.minimum_size_changed.connect(_queue_layout)
	_queue_layout()


func is_conversation_open() -> bool:
	return _conversation != null


func show_conversation(conversation: DialogueConversation) -> bool:
	if is_conversation_open() or conversation == null or not conversation.is_valid():
		return false
	_conversation = conversation
	_entry_index = 0
	_show_entry()
	_panel.show()
	# Start readable; no text reveal timer or input lock accompanies this fade.
	_panel.modulate.a = 0.82
	_opening_tween = create_tween()
	_opening_tween.tween_property(_panel, "modulate:a", 1.0, 0.12)
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
	_scroll.scroll_vertical = 0
	_next.text = "Finish" if _entry_index == _conversation.entries.size() - 1 else "Next"
	if _portrait_tween != null:
		_portrait_tween.kill()
	_portrait.modulate.a = 1.0
	_portrait.texture = PORTRAITS.get(entry.speaker_id)
	_portrait.visible = _portrait.texture != null
	if _speaker_id != entry.speaker_id and _portrait.visible:
		_portrait.modulate.a = 0.8
		_portrait_tween = create_tween()
		_portrait_tween.tween_property(_portrait, "modulate:a", 1.0, 0.10)
	_speaker_id = entry.speaker_id
	_queue_layout()


func _close() -> void:
	# State cleanup is immediate, including during opening/speaker transitions.
	if _opening_tween != null:
		_opening_tween.kill()
	if _portrait_tween != null:
		_portrait_tween.kill()
	_panel.hide()
	_panel.modulate.a = 1.0
	_conversation = null
	_entry_index = 0
	_speaker_id = &""


func _queue_layout() -> void:
	if not _layout_queued:
		_layout_queued = true
		_layout_panel.call_deferred()


func _layout_panel() -> void:
	_layout_queued = false
	var extent: Vector2 = $HUD.size
	var width := minf(PANEL_WIDTH, extent.x - EDGE_CLEARANCE * 2.0)
	# Width changes settle through containers; Label minimum-size notifications
	# schedule another measurement after wrapping, including scrollbar clearance.
	_panel.size.x = width
	_hints.text = "E · Advance   Esc · Dismiss" if width >= 560.0 else "E / Esc"
	var content := $HUD/Conversation/Content as VBoxContainer
	var body := $HUD/Conversation/Content/Entry/Body as VBoxContainer
	var actions := $HUD/Conversation/Content/Actions as HBoxContainer
	var style := _panel.get_theme_stylebox("panel")
	var chrome: float = style.get_minimum_size().y + content.get_theme_constant("separation") \
		+ actions.get_combined_minimum_size().y \
		+ _speaker.get_combined_minimum_size().y \
		+ $HUD/Conversation/Content/Entry/Body/Divider.get_combined_minimum_size().y \
		+ body.get_theme_constant("separation") * 2.0
	var maximum_height := minf(360.0, extent.y - BOTTOM_CLEARANCE - EDGE_CLEARANCE)
	var text_height := minf(_text.get_minimum_size().y, maxf(24.0, maximum_height - chrome))
	_scroll.custom_minimum_size.y = text_height
	_panel.size.y = _panel.get_combined_minimum_size().y
	_panel.position = Vector2((extent.x - _panel.size.x) * 0.5,
		extent.y - BOTTOM_CLEARANCE - _panel.size.y)
