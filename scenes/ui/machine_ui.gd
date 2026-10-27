class_name MachineUI
extends CanvasLayer

@export var player: CharacterBody2D
@export var progression: PlaythroughState
@export var transitions: SceneTransitionController
@export var inventory_ui: InventoryUI
@export var construction: ConstructionController

@onready var _detector: InteractionDetector = player.get_node("InteractionDetector")
@onready var _dialogue: DialogueUI = player.get_node("DialogueUI")
@onready var _interaction: InteractionUI = player.get_node("InteractionUI")
@onready var _panel: PanelContainer = $HUD/Panel
@onready var _title: Label = $HUD/Panel/Content/Title
@onready var _status: Label = $HUD/Panel/Content/Status
@onready var _progress: ProgressBar = $HUD/Panel/Content/Progress
@onready var _output: Label = $HUD/Panel/Content/Output
@onready var _collect_button: Button = $HUD/Panel/Content/Collect

var _machine_id: int = 0


func _ready() -> void:
	_detector.machine_panel = self
	inventory_ui.opened.connect(close)
	construction.mode_started.connect(close)
	transitions.transition_started.connect(close)


func is_open() -> bool:
	return _panel.visible


func interaction_blocked() -> bool:
	return _panel.visible or inventory_ui.is_open() or transitions.is_transitioning()


func _in_range(machine: Dictionary) -> bool:
	var world := transitions.get_current_world()
	if machine.is_empty() or not world is PlanetExterior or transitions.is_transitioning():
		return false
	var definition: MachineDefinition = machine.definition
	var point := world.to_local(_detector.global_position)
	return point.distance_to(definition.footprint(machine.cell, machine.turns).get_center()) \
		<= _detector.machine_interaction_range


func open_machine(machine_id: int) -> void:
	var machine := progression.planet.get_machine(machine_id)
	if inventory_ui.is_open() or _dialogue.is_conversation_open() \
			or _interaction.is_response_open() or not _in_range(machine):
		return
	_machine_id = machine_id
	_panel.show()
	_interaction.set_prompt("")
	_refresh(machine)


func close() -> void:
	_machine_id = 0
	_panel.hide()


func _input(event: InputEvent) -> void:
	if _panel.visible and not event.is_echo() and event.is_action_pressed("ui_cancel"):
		close()
		get_viewport().set_input_as_handled()


func _process(_delta: float) -> void:
	if not _panel.visible:
		return
	var machine := progression.planet.get_machine(_machine_id)
	if not _in_range(machine) or inventory_ui.is_open() \
			or _dialogue.is_conversation_open() or _interaction.is_response_open():
		close()
		return
	_refresh(machine)


func _refresh(machine: Dictionary) -> void:
	var definition: MachineDefinition = machine.definition
	_title.text = definition.display_name
	match progression.planet.machine_status(machine):
		PlanetWorldState.OperatingStatus.PRODUCING:
			_status.text = "Producing"
		PlanetWorldState.OperatingStatus.OUTPUT_FULL:
			_status.text = "Output Full"
		_:
			_status.text = "Inactive"
	_progress.value = 100.0 * machine.cycle_progress / definition.cycle_seconds \
		if definition.has_production() else 0.0
	var name_text := definition.output_item.display_name if definition.output_item != null else "Output"
	_output.text = "%s: %d / %d" % [name_text, machine.output, definition.output_capacity]
	_collect_button.disabled = machine.output == 0


func _collect() -> void:
	var machine := progression.planet.get_machine(_machine_id)
	if not _panel.visible or not _in_range(machine) or inventory_ui.is_open() \
			or _dialogue.is_conversation_open() or _interaction.is_response_open():
		return
	var world := transitions.get_current_world()
	progression.planet.collect_output(_machine_id, progression.inventory,
		world.to_local(_detector.global_position), _detector.machine_interaction_range)
	var updated := progression.planet.get_machine(_machine_id)
	if updated.is_empty():
		close()
	else:
		_refresh(updated)
