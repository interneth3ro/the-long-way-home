extends Node2D

const FERRITE_MUSING: MusingDefinition = preload("res://dialogue/ferrite_discovery.tres")
# Display stage only: the controller keeps the original single objective ID/state.
const FERRITE_GUIDANCE: ObjectiveDefinition = preload("res://objectives/restore_computer_ferrite.tres")
const EXTRACTOR_MUSING: MusingDefinition = preload("res://dialogue/extractor_recovery.tres")
const EXTRACTOR_GUIDANCE: ObjectiveDefinition = preload("res://objectives/restore_computer_extractor.tres")
const PRODUCTION_GUIDANCE: ObjectiveDefinition = preload("res://objectives/restore_computer_production.tres")
const SMELTER_GUIDANCE: ObjectiveDefinition = preload("res://objectives/restore_computer_smelter.tres")

@onready var _objectives: ObjectiveController = $ObjectiveController
@onready var _tracker: ObjectiveTracker = $ObjectiveTracker
@onready var _dialogue: DialogueUI = $Dave/DialogueUI


func _ready() -> void:
	$PlaythroughState.ferrite_discovery_completed.connect(_on_ferrite_discovered)
	$PlaythroughState.extractor_recovery_completed.connect(_on_extractor_recovered)
	$PlaythroughState.extractor_deployment_completed.connect(_refresh_objective_tracker)
	$PlaythroughState.ferrite_acquisition_completed.connect(_refresh_objective_tracker)
	$SceneTransitions.transition_started.connect($MusingUI.dismiss)
	$SceneTransitions.initialize()
	_objectives.objective_state_changed.connect(_on_objective_state_changed)
	_dialogue.conversation_completed.connect(_on_conversation_completed)
	_refresh_objective_tracker()


func _on_conversation_completed(conversation_id: StringName) -> void:
	if conversation_id == &"computer_opening":
		_objectives.activate_objective(&"restore_computer")


func _on_objective_state_changed(_objective_id: StringName, _state: ObjectiveController.State) -> void:
	_refresh_objective_tracker()


func _refresh_objective_tracker() -> void:
	var definition := _objectives.get_active_objective()
	if definition != null and definition.objective_id == &"restore_computer":
		if $PlaythroughState.ferrite_acquired:
			definition = SMELTER_GUIDANCE
		elif $PlaythroughState.extractor_deployed:
			definition = PRODUCTION_GUIDANCE
		elif $PlaythroughState.extractor_recovered:
			definition = EXTRACTOR_GUIDANCE
		elif $PlaythroughState.ferrite_discovered:
			definition = FERRITE_GUIDANCE
	_tracker.show_objective(definition)


func _on_ferrite_discovered() -> void:
	$MusingUI.show_musing(FERRITE_MUSING)
	# Exploration is possible before finishing Computer's optional conversation.
	# Reuse its objective so that discovery always leaves recoverable guidance.
	_objectives.activate_objective(&"restore_computer")
	_refresh_objective_tracker()


func _on_extractor_recovered() -> void:
	$MusingUI.show_musing(EXTRACTOR_MUSING)
	_refresh_objective_tracker()
