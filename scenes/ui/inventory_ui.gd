class_name InventoryUI
extends CanvasLayer

signal opened

@export var progression: PlaythroughState
# Node reference keeps storage/item definitions independent of the tool presenter.
@export var construction: Node

@onready var _panel: PanelContainer = $HUD/Panel
@onready var _materials: Label = $HUD/Panel/Content/Materials
@onready var _equipment: Label = $HUD/Panel/Content/Equipment
@onready var _actions: VBoxContainer = $HUD/Panel/Content/EquipmentActions
var _selected: MachineDefinition


func _ready() -> void:
	progression.inventory.changed.connect(_refresh)
	_refresh()


func _input(event: InputEvent) -> void:
	if event.is_echo():
		return
	if event.is_action_pressed("inventory"):
		_toggle()
	elif _panel.visible and event.is_action_pressed("ui_cancel"):
		_panel.hide()
	else:
		return
	get_viewport().set_input_as_handled()


func _toggle() -> void:
	_panel.visible = not _panel.visible
	if _panel.visible:
		opened.emit()


func is_open() -> bool:
	return _panel.visible


func close() -> void:
	_panel.hide()


func _select_machine(definition: MachineDefinition) -> void:
	_selected = definition
	_refresh()


func _deploy_selected() -> void:
	if _selected != null:
		construction.begin_deployment(_selected)


func _refresh() -> void:
	for child in _actions.get_children():
		_actions.remove_child(child)
		child.queue_free()
	var materials := PackedStringArray()
	var equipment := PackedStringArray()
	for item in progression.inventory.get_items():
		var row := "%s ×%d" % [item.display_name, progression.inventory.get_quantity(item.item_id)]
		if item.section == ItemDefinition.Section.EQUIPMENT:
			if item is MachineDefinition:
				var select := Button.new()
				select.text = row
				select.focus_mode = Control.FOCUS_NONE
				select.pressed.connect(_select_machine.bind(item))
				_actions.add_child(select)
			else:
				equipment.append(row)
		else:
			materials.append(row)
	_materials.text = "Empty" if materials.is_empty() else "\n".join(materials)
	_equipment.text = "Empty" if equipment.is_empty() and _actions.get_child_count() == 0 else "\n".join(equipment)
	_equipment.visible = not _equipment.text.is_empty()
	if _selected != null and progression.inventory.get_quantity(_selected.item_id) > 0:
		var deploy := Button.new()
		deploy.text = "Deploy " + _selected.display_name
		deploy.focus_mode = Control.FOCUS_NONE
		deploy.pressed.connect(_deploy_selected)
		_actions.add_child(deploy)
	else:
		_selected = null
