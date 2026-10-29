class_name HotbarUI
extends CanvasLayer

@export var progression: PlaythroughState
@export var construction: ConstructionController
@export var transitions: SceneTransitionController
@export var player: CharacterBody2D

const PHYSICAL_KEYS := [KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9, KEY_0]
const B1_THEME: Theme = preload("res://assets/ui/b1_theme.tres")

@onready var _root: Control = $HUD
@onready var _slots: HBoxContainer = $HUD/Backing/Slots
@onready var _feedback: Label = $HUD/Feedback
@onready var _dialogue: DialogueUI = player.get_node("DialogueUI")
@onready var _interaction: InteractionUI = player.get_node("InteractionUI")

var _clear_menu: PopupMenu
var _clear_slot: int = -1
var _active_item: StringName = &""
var _feedback_seconds: float = 0.0
var _active_hover: StyleBoxFlat


func _ready() -> void:
	# Keep active hover copper; make one private copy without changing pressed styling.
	_active_hover = B1_THEME.get_stylebox("pressed", "Button").duplicate() as StyleBoxFlat
	_active_hover.bg_color = Color(0.095, 0.15, 0.17, 1)
	_active_hover.border_color = Color(0.85, 0.62, 0.39, 1)
	# Customize a private copy so inventory and machine panels retain their style.
	var backing := B1_THEME.get_stylebox("panel", "PanelContainer").duplicate() as StyleBoxFlat
	backing.content_margin_left = 4.0
	backing.content_margin_top = 4.0
	backing.content_margin_right = 4.0
	backing.content_margin_bottom = 4.0
	backing.bg_color = Color(0.075, 0.105, 0.125, 0.90)
	$HUD/Backing.add_theme_stylebox_override("panel", backing)
	_clear_menu = PopupMenu.new()
	_clear_menu.force_native = false
	_root.add_child(_clear_menu)
	_clear_menu.add_item("Clear Assignment", 0)
	_clear_menu.id_pressed.connect(_clear_assignment)
	transitions.transition_started.connect(_clear_menu.hide)
	for index in PlaythroughState.HOTBAR_SIZE:
		var slot := Button.new()
		slot.custom_minimum_size = Vector2(52, 52)
		slot.theme_type_variation = &"B1InventorySlot"
		slot.focus_mode = Control.FOCUS_NONE
		slot.mouse_filter = Control.MOUSE_FILTER_STOP
		_slots.add_child(slot)
		slot.pressed.connect(_activate.bind(index))
		slot.gui_input.connect(_slot_input.bind(index, slot))
		var icon := TextureRect.new()
		icon.name = "Icon"
		icon.position = Vector2(14, 11)
		icon.size = Vector2(24, 24)
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		slot.add_child(icon)
		_add_label(slot, "Key", str(index + 1) if index < 9 else "0", Vector2(4, 0), 13)
		var symbol := _add_label(slot, "Symbol", "", Vector2(4, 11), 16)
		symbol.size.x = 44
		symbol.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		var quantity := _add_label(slot, "Quantity", "", Vector2(4, 32), 14)
		quantity.size.x = 44
		quantity.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	progression.hotbar_changed.connect(_refresh)
	progression.inventory.changed.connect(_refresh)
	_refresh()


func _add_label(slot: Control, label_name: String, text: String, point: Vector2, font_size: int) -> Label:
	var label := Label.new()
	label.name = label_name
	label.text = text
	label.position = point
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.add_theme_font_size_override("font_size", font_size)
	slot.add_child(label)
	return label


func _process(delta: float) -> void:
	# Narrative panels extend into the bottom band. Hide only for these modal
	# presentations/transitions; inventory, inspection and musings retain the bar.
	_root.visible = not transitions.is_transitioning() and not _dialogue.is_conversation_open() \
		and not _interaction.is_response_open()
	if not _root.visible:
		_clear_menu.hide()
	var active := construction.get_deployment_item_id()
	if active != _active_item:
		_active_item = active
		_refresh()
	_feedback_seconds = maxf(0.0, _feedback_seconds - delta)
	_feedback.visible = _feedback_seconds > 0.0 and _root.visible


func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.is_echo() \
			or event.alt_pressed or event.ctrl_pressed or event.meta_pressed or event.shift_pressed:
		return
	var slot := PHYSICAL_KEYS.find(event.physical_keycode)
	if slot < 0 or progression.get_hotbar_assignment(slot) == null:
		return
	get_viewport().set_input_as_handled()
	_activate(slot)


func _activate(slot: int) -> void:
	var definition := progression.get_hotbar_assignment(slot)
	if definition == null:
		return
	var reason := construction.activate_hotbar(definition)
	_feedback.text = reason
	_feedback_seconds = 3.0 if not reason.is_empty() else 0.0
	_active_item = construction.get_deployment_item_id()
	_refresh()


func _slot_input(event: InputEvent, index: int, slot: Control) -> void:
	if not event is InputEventMouseButton or not event.pressed \
			or event.button_index != MOUSE_BUTTON_RIGHT:
		return
	slot.accept_event()
	if progression.get_hotbar_assignment(index) == null:
		return
	_clear_slot = index
	_clear_menu.position = Vector2i(slot.get_screen_position() - Vector2(0, 44))
	_clear_menu.reset_size()
	_clear_menu.popup()


func _clear_assignment(_id: int) -> void:
	progression.clear_hotbar(_clear_slot)


func _refresh() -> void:
	for index in _slots.get_child_count():
		var slot := _slots.get_child(index) as Button
		var definition := progression.get_hotbar_assignment(index)
		var key := str(index + 1) if index < 9 else "0"
		var quantity := progression.inventory.get_quantity(definition.item_id) if definition != null else 0
		var active := definition != null and definition.item_id == _active_item
		# Keep zero-quantity buttons interactive so their assignments can be cleared.
		slot.modulate = Color.WHITE if quantity > 0 or active else Color(1, 1, 1, 0.5)
		var normal := B1_THEME.get_stylebox("normal", "B1InventorySlot")
		var hover := B1_THEME.get_stylebox("hover", "B1InventorySlot")
		var selected := B1_THEME.get_stylebox("pressed", "Button")
		slot.add_theme_stylebox_override("normal", selected if active else normal)
		slot.add_theme_stylebox_override("hover", _active_hover if active else hover)
		var icon := slot.get_node("Icon") as TextureRect
		var symbol := slot.get_node("Symbol") as Label
		var total := slot.get_node("Quantity") as Label
		icon.texture = null
		symbol.text = ""
		total.text = ""
		slot.tooltip_text = "Unassigned · Key %s" % key
		if definition == null:
			continue
		var artwork: Variant = ItemPresentation.ICONS.get(definition.item_id, "?")
		if artwork is Texture2D:
			icon.texture = artwork
		else:
			symbol.text = str(artwork)
		total.text = ItemPresentation.quantity_text(quantity)
		slot.tooltip_text = "%s ×%d · Key %s\nRight-click to clear assignment" % [definition.display_name, quantity, key]
		if quantity == 0:
			slot.tooltip_text += "\nUnavailable: none held"
