extends Node2D

@onready var _objectives: ObjectiveController = $ObjectiveController
@onready var _tracker: ObjectiveTracker = $ObjectiveTracker
@onready var _dialogue: DialogueUI = $GroundObjects/Dave/DialogueUI


func _ready() -> void:
	_objectives.objective_state_changed.connect(_on_objective_state_changed)
	_dialogue.conversation_completed.connect(_on_conversation_completed)
	_refresh_objective_tracker()


func _on_conversation_completed(conversation_id: StringName) -> void:
	if conversation_id == &"computer_opening":
		_objectives.activate_objective(&"restore_computer")


func _on_objective_state_changed(_objective_id: StringName, _state: ObjectiveController.State) -> void:
	_refresh_objective_tracker()


func _refresh_objective_tracker() -> void:
	_tracker.show_objective(_objectives.get_active_objective())
