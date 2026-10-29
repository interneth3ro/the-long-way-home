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
var _expanded: bool = false
var _machine_inspection_open: bool = false


func set_machine_inspection_open(open: bool) -> void:
	# A temporary visibility override, never a change to the player's preference.
	_machine_inspection_open = open
	_refresh_visibility()


func show_objective(definition: ObjectiveDefinition) -> void:
	_has_objective = definition != null
	if not _has_objective:
		_expanded = false
	_title.text = definition.title if _has_objective else ""
	_description.text = definition.description if _has_objective else ""
	_refresh_visibility()


func _toggle_pin() -> void:
	_presentation = Presentation.CONTEXTUAL if _presentation == Presentation.PINNED else Presentation.PINNED
	_expanded = _presentation == Presentation.PINNED
	_refresh_visibility()


func _hide_tracker() -> void:
	_presentation = Presentation.HIDDEN
	_expanded = false
	_refresh_visibility()


func _restore_tracker() -> void:
	_presentation = Presentation.CONTEXTUAL
	_expanded = true
	_refresh_visibility()


func _refresh_visibility() -> void:
	if _machine_inspection_open:
		_panel.hide()
		_restore.hide()
		return
	_panel.visible = _has_objective and (_presentation == Presentation.PINNED \
		or (_presentation == Presentation.CONTEXTUAL and _expanded))
	_restore.visible = _has_objective and not _panel.visible
	_pin.text = "Unpin" if _presentation == Presentation.PINNED else "Pin"
