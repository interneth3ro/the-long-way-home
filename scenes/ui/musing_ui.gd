class_name MusingUI
extends CanvasLayer

@onready var _panel: PanelContainer = $HUD/Panel
@onready var _text: Label = $HUD/Panel/Text

var _tween: Tween


func show_musing(definition: MusingDefinition) -> void:
	dismiss()
	if definition == null or definition.text.strip_edges().is_empty():
		return
	_text.text = definition.text
	_panel.modulate.a = 0.0
	_panel.show()
	_tween = create_tween()
	_tween.tween_property(_panel, "modulate:a", 1.0, 0.25)
	_tween.tween_interval(definition.duration_seconds)
	_tween.tween_property(_panel, "modulate:a", 0.0, 0.35)
	_tween.tween_callback(dismiss)


func dismiss() -> void:
	if _tween != null:
		_tween.kill()
		_tween = null
	_panel.hide()
	_text.text = ""
