class_name InventoryUI
extends CanvasLayer

signal opened

@export var progression: PlaythroughState
# Node reference keeps storage/item definitions independent of the tool presenter.
@export var construction: Node
@export var transitions: SceneTransitionController

const MATERIAL_SLOTS := 24
const EQUIPMENT_SLOTS := 8
const SLOT_SIZE := Vector2(42, 42)
# Shared presentation lookup; storage remains independent of UI.
const ITEM_ICONS := ItemPresentation.ICONS

var _assignment_menu: PopupMenu
var _assignment_machine: MachineDefinition

@onready var _panel: PanelContainer = $HUD/Panel
@onready var _materials: GridContainer = $HUD/Panel/Content/Materials
@onready var _equipment: GridContainer = $HUD/Panel/Content/Equipment
@onready var _overflow: ScrollContainer = $HUD/Panel/Content/Overflow
@onready var _overflow_items: VBoxContainer = $HUD/Panel/Content/Overflow/Items


func _ready() -> void:
	var panel_style := _panel.get_theme_stylebox("panel").duplicate() as StyleBox
	panel_style.content_margin_left = 8
	panel_style.content_margin_right = 8
	panel_style.content_margin_top = 6
	panel_style.content_margin_bottom = 6
	_panel.add_theme_stylebox_override("panel", panel_style)
	_assignment_menu = PopupMenu.new()
	_assignment_menu.name = "AssignToHotbar"
	_assignment_menu.force_native = false
	$HUD.add_child(_assignment_menu)
	_assignment_menu.id_pressed.connect(_assign_to_hotbar)
	_assignment_menu.window_input.connect(_assignment_menu_input)
	transitions.transition_started.connect(_assignment_menu.hide)
	_create_slots(_materials, MATERIAL_SLOTS)
	_create_slots(_equipment, EQUIPMENT_SLOTS)
	progression.inventory.changed.connect(_refresh)
	_refresh()


func _input(event: InputEvent) -> void:
	# Popup owns Esc/navigation while open; closing it must not close inventory.
	if _assignment_menu.visible:
		return
	if event.is_action_pressed("inventory", true):
		# Consume repeats too, before GUI focus navigation can see Tab.
		get_viewport().set_input_as_handled()
		if not event.is_echo():
			_toggle()
		return
	if event.is_echo():
		return
	if _panel.visible and event.is_action_pressed("ui_cancel"):
		close()
		get_viewport().set_input_as_handled()


func _toggle() -> void:
	_assignment_menu.hide()
	_panel.visible = not _panel.visible
	if _panel.visible:
		opened.emit()


func is_open() -> bool:
	return _panel.visible


func close() -> void:
	_assignment_menu.hide()
	_panel.hide()


func _deploy_machine(definition: MachineDefinition) -> void:
	# The controller remains the authority for context, eligibility and cancellation.
	construction.begin_deployment(definition)


func _create_slots(grid: GridContainer, count: int) -> void:
	for index in count:
		var slot := Button.new()
		slot.custom_minimum_size = SLOT_SIZE
		slot.theme_type_variation = &"B1InventorySlot"
		slot.focus_mode = Control.FOCUS_NONE
		slot.mouse_filter = Control.MOUSE_FILTER_STOP
		grid.add_child(slot)
		var icon := TextureRect.new()
		icon.name = "Icon"
		icon.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)
		icon.position = Vector2(-11, 1)
		icon.size = Vector2(22, 22)
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		slot.add_child(icon)
		var symbol := Label.new()
		symbol.name = "Symbol"
		symbol.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
		symbol.offset_top = 1
		symbol.offset_bottom = 23
		symbol.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		symbol.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		symbol.add_theme_font_size_override("font_size", 14)
		symbol.add_theme_color_override("font_color", Color(0.84, 0.65, 0.45))
		symbol.mouse_filter = Control.MOUSE_FILTER_IGNORE
		slot.add_child(symbol)
		var quantity := Label.new()
		quantity.name = "Quantity"
		quantity.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
		quantity.offset_left = 2
		quantity.offset_right = -2
		quantity.offset_top = -19
		quantity.offset_bottom = -1
		quantity.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		quantity.add_theme_font_size_override("font_size", 12)
		quantity.mouse_filter = Control.MOUSE_FILTER_IGNORE
		slot.add_child(quantity)


func _refresh() -> void:
	var materials: Array[ItemDefinition] = []
	var equipment: Array[ItemDefinition] = []
	var items := progression.inventory.get_items()
	# IDs, independent of acquisition order; quantity-only changes never reorder.
	items.sort_custom(func(a: ItemDefinition, b: ItemDefinition) -> bool:
		return String(a.item_id) < String(b.item_id))
	for item in items:
		if item.section == ItemDefinition.Section.EQUIPMENT:
			equipment.append(item)
		else:
			materials.append(item)
	_refresh_slots(_materials, materials)
	_refresh_slots(_equipment, equipment)
	# Storage is unbounded. Preserve access to future types without adding pages.
	for child in _overflow_items.get_children():
		_overflow_items.remove_child(child)
		child.queue_free()
	_add_overflow(materials, MATERIAL_SLOTS, "Materials")
	_add_overflow(equipment, EQUIPMENT_SLOTS, "Machines / Equipment")
	_overflow.visible = _overflow_items.get_child_count() > 0


func _refresh_slots(grid: GridContainer, items: Array[ItemDefinition]) -> void:
	for index in grid.get_child_count():
		var slot := grid.get_child(index) as Button
		for connection in slot.pressed.get_connections():
			slot.pressed.disconnect(connection.callable)
		for connection in slot.gui_input.get_connections():
			slot.gui_input.disconnect(connection.callable)
		var item: ItemDefinition = items[index] if index < items.size() else null
		var icon := slot.get_node("Icon") as TextureRect
		var symbol := slot.get_node("Symbol") as Label
		var quantity := slot.get_node("Quantity") as Label
		slot.disabled = item == null
		slot.tooltip_text = ""
		icon.texture = null
		symbol.text = ""
		quantity.text = ""
		slot.modulate = Color(1, 1, 1, 0.45) if item == null else Color.WHITE
		if item == null:
			continue
		var held := progression.inventory.get_quantity(item.item_id)
		var artwork: Variant = ITEM_ICONS.get(item.item_id, "?")
		if artwork is Texture2D:
			icon.texture = artwork
		else:
			symbol.text = str(artwork)
		quantity.text = _quantity_text(held)
		slot.tooltip_text = "%s ×%d" % [item.display_name, held]
		if item.section == ItemDefinition.Section.EQUIPMENT:
			if item is MachineDefinition and item.is_valid():
				slot.pressed.connect(_deploy_machine.bind(item))
				slot.gui_input.connect(_machine_context_input.bind(item, slot))
				slot.tooltip_text += "\nLeft-click to deploy · Right-click to assign hotbar"
			else:
				slot.disabled = true
				slot.tooltip_text += "\nNot deployable"


func _quantity_text(quantity: int) -> String:
	return ItemPresentation.quantity_text(quantity)


func _add_overflow(items: Array[ItemDefinition], capacity: int, section: String) -> void:
	for index in range(capacity, items.size()):
		var item := items[index]
		var row := Button.new()
		row.focus_mode = Control.FOCUS_NONE
		row.mouse_filter = Control.MOUSE_FILTER_STOP
		row.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		row.text = "%s · %s ×%d" % [section, item.display_name,
			progression.inventory.get_quantity(item.item_id)]
		row.tooltip_text = row.text
		if item.section == ItemDefinition.Section.EQUIPMENT:
			if item is MachineDefinition and item.is_valid():
				row.pressed.connect(_deploy_machine.bind(item))
				row.gui_input.connect(_machine_context_input.bind(item, row))
				row.tooltip_text += "\nLeft-click to deploy · Right-click to assign hotbar"
			else:
				row.disabled = true
				row.tooltip_text += "\nNot deployable"
		_overflow_items.add_child(row)


func _machine_context_input(event: InputEvent, definition: MachineDefinition, slot: Control) -> void:
	if not event is InputEventMouseButton or not event.pressed \
			or event.button_index != MOUSE_BUTTON_RIGHT:
		return
	slot.accept_event()
	_assignment_machine = definition
	_assignment_menu.clear()
	_assignment_menu.add_separator("Assign to Hotbar · " + definition.display_name)
	for index in PlaythroughState.HOTBAR_SIZE:
		var assigned := progression.get_hotbar_assignment(index)
		var key := str(index + 1) if index < 9 else "0"
		var label := "Slot %d [%s] · %s" % [index + 1, key,
			assigned.display_name if assigned != null else "Unassigned"]
		if assigned != null and assigned.item_id == definition.item_id:
			label += " (Current)"
		_assignment_menu.add_item(label, index)
	_assignment_menu.position = Vector2i(slot.get_screen_position() + Vector2(0, slot.size.y))
	_assignment_menu.reset_size()
	_assignment_menu.popup()


func _assign_to_hotbar(slot: int) -> void:
	# Revalidate quantity if inventory changed while the menu was open.
	progression.assign_hotbar(slot, _assignment_machine)


func _assignment_menu_input(event: InputEvent) -> void:
	# Keep Tab's close behavior even while the popup owns keyboard input.
	if event.is_action_pressed("inventory", true):
		_assignment_menu.set_input_as_handled()
		if not event.is_echo():
			close()
