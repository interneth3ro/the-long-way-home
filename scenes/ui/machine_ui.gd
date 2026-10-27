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
@onready var _explanation: Label = $HUD/Panel/Content/Explanation
@onready var _progress: ProgressBar = $HUD/Panel/Content/Progress
@onready var _input_section: VBoxContainer = $HUD/Panel/Content/InputSection
@onready var _input_storage: Label = $HUD/Panel/Content/InputSection/Storage
@onready var _transfer_button: Button = $HUD/Panel/Content/InputSection/Transfer
@onready var _output_section: VBoxContainer = $HUD/Panel/Content/OutputSection
@onready var _output: Label = $HUD/Panel/Content/OutputSection/Storage
@onready var _collect_button: Button = $HUD/Panel/Content/OutputSection/Collect

@onready var _recipe_cards: VBoxContainer = $HUD/Panel/Content/RecipeCards
@onready var _recipe_summary: Label = $HUD/Panel/Content/RecipeSummary
@onready var _change_button: Button = $HUD/Panel/Content/ChangeRecipe
@onready var _back_button: Button = $HUD/Panel/Content/RecipeBack
@onready var _pause_label: Label = $HUD/Panel/Content/RecipePause
@onready var _recipe_error: Label = $HUD/Panel/Content/RecipeError

var _machine_id: int = 0
# Only the post-placement panel session bypasses inspection range. Transfer
# always checks real range; closing discards this exception.
var _placement_session: bool = false
var _changing_recipe: bool = false
var _pause_world: PlanetWorldState
var _pause_lease: RefCounted


func _ready() -> void:
	_detector.machine_panel = self
	inventory_ui.opened.connect(close)
	construction.mode_started.connect(close)
	construction.deployment_completed.connect(_open_placed_machine)
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


func _open_placed_machine(machine_id: int) -> void:
	var machine := progression.planet.get_machine(machine_id)
	if machine.is_empty():
		return
	var definition: MachineDefinition = machine.definition
	if not definition.has_recipes() or not transitions.get_current_world() is PlanetExterior \
			or transitions.is_transitioning() or inventory_ui.is_open() \
			or _dialogue.is_conversation_open() or _interaction.is_response_open():
		return
	_show_machine(machine_id, machine, true)


func open_machine(machine_id: int) -> void:
	var machine := progression.planet.get_machine(machine_id)
	if inventory_ui.is_open() or _dialogue.is_conversation_open() \
			or _interaction.is_response_open() or not _in_range(machine):
		return
	_show_machine(machine_id, machine, false)


func _show_machine(machine_id: int, machine: Dictionary, placement_session: bool) -> void:
	close()
	_machine_id = machine_id
	_placement_session = placement_session
	_build_recipe_cards(machine)
	_panel.show()
	_interaction.set_prompt("")
	_refresh(machine)


func close() -> void:
	_release_recipe_pause()
	_machine_id = 0
	_placement_session = false
	_panel.hide()


func _exit_tree() -> void:
	_release_recipe_pause()


func _release_recipe_pause() -> void:
	if _pause_world != null:
		_pause_world.end_recipe_change(_machine_id, _pause_lease)
	_pause_world = null
	_pause_lease = null
	_changing_recipe = false
	if is_instance_valid(_recipe_error):
		_recipe_error.text = ""
		_recipe_error.hide()


func _change_recipe() -> void:
	var machine := progression.planet.get_machine(_machine_id)
	if not _panel.visible or _changing_recipe or not _in_range(machine) \
			or inventory_ui.is_open() or _dialogue.is_conversation_open() \
			or _interaction.is_response_open():
		return
	var lease := progression.planet.begin_recipe_change(_machine_id)
	if lease == null:
		return
	_pause_world = progression.planet
	_pause_lease = lease
	_changing_recipe = true
	# Switching always obeys normal inspection range, including this session.
	_placement_session = false
	_build_recipe_cards(machine)
	_refresh(machine)


func _back_to_inspection() -> void:
	if not _changing_recipe:
		return
	_release_recipe_pause()
	var machine := progression.planet.get_machine(_machine_id)
	if machine.is_empty() or not _in_range(machine):
		close()
	else:
		_refresh(machine)


func _input(event: InputEvent) -> void:
	if _panel.visible and not event.is_echo() and event.is_action_pressed("ui_cancel"):
		close()
		get_viewport().set_input_as_handled()


func _process(_delta: float) -> void:
	if not _panel.visible:
		return
	var machine := progression.planet.get_machine(_machine_id)
	if machine.is_empty() or (not _placement_session and not _in_range(machine)) \
			or not transitions.get_current_world() is PlanetExterior \
			or transitions.is_transitioning() or inventory_ui.is_open() \
			or _dialogue.is_conversation_open() or _interaction.is_response_open():
		close()
		return
	_refresh(machine)


func _refresh(machine: Dictionary) -> void:
	var definition: MachineDefinition = machine.definition
	_title.text = definition.display_name
	_recipe_cards.visible = definition.has_recipes() \
		and (_changing_recipe or machine.get("recipe_id", &"") == &"")
	_recipe_summary.visible = definition.has_recipes() and not _recipe_cards.visible \
		and definition.get_recipe(machine.get("recipe_id", &"")) != null
	_change_button.visible = _recipe_summary.visible
	_back_button.visible = _changing_recipe and definition.has_recipes()
	_pause_label.visible = _back_button.visible
	_recipe_error.visible = _back_button.visible and not _recipe_error.text.is_empty()
	_status.visible = not _recipe_cards.visible
	if definition.has_recipes():
		_refresh_fabricator(machine, definition)
		return
	_status.remove_theme_color_override("font_color")
	_explanation.text = "No production configured."
	match progression.planet.machine_status(machine):
		PlanetWorldState.OperatingStatus.PRODUCING:
			_status.text = "Producing"
		PlanetWorldState.OperatingStatus.OUTPUT_FULL:
			_status.text = "Output Full"
		PlanetWorldState.OperatingStatus.INPUT_EMPTY:
			_status.text = "Input Empty"
		_:
			_status.text = "Inactive"
	var has_production := definition.has_production()
	_explanation.visible = not has_production
	_progress.visible = has_production
	_output_section.visible = has_production
	_input_section.visible = has_production and definition.has_input()
	if not has_production:
		return
	_progress.value = 100.0 * machine.cycle_progress / definition.cycle_seconds
	if definition.has_input():
		var input_heading := "Input"
		if machine.input > 0:
			input_heading += " — %s" % definition.input_item.display_name
		_input_storage.text = "%s\n%d / %d" % [input_heading,
			machine.input, definition.input_capacity]
		_transfer_button.disabled = machine.input >= definition.input_capacity \
			or progression.inventory.get_quantity(definition.input_item.item_id) == 0
	var output_heading := "Output"
	if machine.output > 0 and definition.output_item != null:
		output_heading += " — %s" % definition.output_item.display_name
	_output.text = "%s\n%d / %d" % [output_heading, machine.output, definition.output_capacity]
	_collect_button.disabled = machine.output == 0


func _build_recipe_cards(machine: Dictionary) -> void:
	for child in _recipe_cards.get_children():
		_recipe_cards.remove_child(child)
		child.queue_free()
	var definition: MachineDefinition = machine.definition
	for recipe in definition.recipes:
		if recipe == null or not recipe.is_valid():
			continue
		var card := Button.new()
		var marker := " — Current" if _changing_recipe \
			and recipe.recipe_id == machine.get("recipe_id", &"") else ""
		card.text = "%s%s\nInput: %s\nOutput: %s" % [recipe.display_name, marker,
			recipe.input_summary(), recipe.output_summary()]
		card.icon = recipe.icon
		card.expand_icon = true
		card.add_theme_constant_override("icon_max_width", 40)
		card.custom_minimum_size = Vector2(0, 100)
		card.alignment = HORIZONTAL_ALIGNMENT_LEFT
		card.focus_mode = Control.FOCUS_NONE
		card.mouse_filter = Control.MOUSE_FILTER_STOP
		card.pressed.connect(_select_recipe.bind(machine.id, recipe.recipe_id))
		_recipe_cards.add_child(card)


func _select_recipe(machine_id: int, recipe_id: StringName) -> void:
	var machine := progression.planet.get_machine(machine_id)
	if not _panel.visible or machine_id != _machine_id or machine.is_empty() \
			or (not _placement_session and not _in_range(machine)) \
			or not transitions.get_current_world() is PlanetExterior \
			or transitions.is_transitioning() or inventory_ui.is_open() \
			or _dialogue.is_conversation_open() or _interaction.is_response_open():
		if _panel.visible and machine_id == _machine_id:
			close()
		return
	var success := false
	if _changing_recipe:
		var result := progression.planet.change_recipe(machine_id, recipe_id, progression.inventory)
		success = result == PlanetWorldState.RecipeChangeResult.OK
		if not success:
			_recipe_error.text = _recipe_change_error(result)
			_recipe_error.show()
	else:
		success = progression.planet.select_initial_recipe(machine_id, recipe_id)
	if success and _panel.visible and _machine_id == machine_id:
		_release_recipe_pause()
		var updated := progression.planet.get_machine(machine_id)
		if updated.is_empty():
			close()
		else:
			_refresh(updated)


func _recipe_change_error(result: PlanetWorldState.RecipeChangeResult) -> String:
	match result:
		PlanetWorldState.RecipeChangeResult.BUSY:
			return "Machine is busy. Try again."
		PlanetWorldState.RecipeChangeResult.INVALID_RECIPE:
			return "That recipe is unavailable. Choose another recipe."
		PlanetWorldState.RecipeChangeResult.INVALID_CURRENT:
			return "The machine's current recipe is invalid. Cannot change recipe."
		PlanetWorldState.RecipeChangeResult.INVALID_INPUTS:
			return "Stored materials are inconsistent. Cannot change recipe."
		PlanetWorldState.RecipeChangeResult.INVENTORY_REJECTED:
			return "Inventory could not accept returned materials. Recipe unchanged."
	return "Machine is no longer available."


func _refresh_fabricator(machine: Dictionary, definition: MachineDefinition) -> void:
	_progress.hide()
	_output_section.hide()
	var recipe := definition.get_recipe(machine.get("recipe_id", &""))
	# Assign the desired state once: hiding a visible ancestor cancels button presses.
	_input_section.visible = not _recipe_cards.visible and recipe != null
	_explanation.visible = not _recipe_cards.visible
	_explanation.text = "Production not yet available"
	_status.text = "Inactive"
	_status.add_theme_color_override("font_color", Color(0.55, 0.58, 0.59))
	if _recipe_cards.visible:
		_title.text = "%s — %s" % [definition.display_name,
			"Change Recipe" if _changing_recipe else "Select Recipe"]
		return
	if recipe == null:
		return
	_recipe_summary.text = "Selected Recipe: %s\nRecipe: %s → %s" % [
		recipe.display_name, recipe.input_summary(), recipe.output_summary()]
	var rows := PackedStringArray()
	var can_transfer := false
	var inputs: Dictionary = machine.inputs
	for ingredient in recipe.ingredients:
		var stored: int = inputs.get(ingredient.item.item_id, 0)
		rows.append("Input — %s: %d / %d" % [ingredient.item.display_name,
			stored, definition.input_capacity])
		if stored < definition.input_capacity \
				and progression.inventory.get_quantity(ingredient.item.item_id) > 0:
			can_transfer = true
	_input_storage.text = "\n".join(rows)
	_transfer_button.disabled = not can_transfer or not _in_range(machine)


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


func _transfer() -> void:
	var machine := progression.planet.get_machine(_machine_id)
	if not _panel.visible or _changing_recipe or not _in_range(machine) or inventory_ui.is_open() \
			or _dialogue.is_conversation_open() or _interaction.is_response_open():
		return
	var world := transitions.get_current_world()
	progression.planet.transfer_input(_machine_id, progression.inventory,
		world.to_local(_detector.global_position), _detector.machine_interaction_range)
	var updated := progression.planet.get_machine(_machine_id)
	if updated.is_empty():
		close()
	else:
		_refresh(updated)
