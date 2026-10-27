extends CanvasLayer

@export var progression: PlaythroughState

@onready var _panel: PanelContainer = $HUD/Panel
@onready var _materials: Label = $HUD/Panel/Content/Materials
@onready var _equipment: Label = $HUD/Panel/Content/Equipment


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


func _refresh() -> void:
	var materials := PackedStringArray()
	var equipment := PackedStringArray()
	for item in progression.inventory.get_items():
		var row := "%s ×%d" % [item.display_name, progression.inventory.get_quantity(item.item_id)]
		if item.section == ItemDefinition.Section.EQUIPMENT:
			equipment.append(row)
		else:
			materials.append(row)
	_materials.text = "Empty" if materials.is_empty() else "\n".join(materials)
	_equipment.text = "Empty" if equipment.is_empty() else "\n".join(equipment)
