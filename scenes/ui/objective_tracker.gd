class_name ObjectiveTracker
extends CanvasLayer

enum Presentation { CONTEXTUAL, PINNED, HIDDEN }

@onready var _panel: PanelContainer = $HUD/Panel
@onready var _title: Label = $HUD/Panel/Content/Title
@onready var _description: Label = $HUD/Panel/Content/Description
@onready var _pin: Button = $HUD/Panel/Content/Actions/Pin
@onready var _restore: Button = $HUD/Restore

var _presentation: Presentation = Presentation.CONTEXTUAL
var _has_objective: bool = false


func show_objective(definition: ObjectiveDefinition) -> void:
	_has_objective = definition != null
	_title.text = definition.title if _has_objective else ""
	_description.text = definition.description if _has_objective else ""
	_refresh_visibility()


func _toggle_pin() -> void:
	_presentation = Presentation.CONTEXTUAL if _presentation == Presentation.PINNED else Presentation.PINNED
	_refresh_visibility()


func _hide_tracker() -> void:
	_presentation = Presentation.HIDDEN
	_refresh_visibility()


func _restore_tracker() -> void:
	_presentation = Presentation.CONTEXTUAL
	_refresh_visibility()


func _refresh_visibility() -> void:
	_panel.visible = _has_objective and _presentation != Presentation.HIDDEN
	_restore.visible = _has_objective and _presentation == Presentation.HIDDEN
	_pin.text = "Unpin" if _presentation == Presentation.PINNED else "Pin"
