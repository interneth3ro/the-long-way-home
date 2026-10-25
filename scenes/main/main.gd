extends Node2D

@onready var _objectives: ObjectiveController = $ObjectiveController
@onready var _tracker: ObjectiveTracker = $ObjectiveTracker


func _ready() -> void:
	_objectives.objective_state_changed.connect(_on_objective_state_changed)
	_refresh_objective_tracker()


func _on_objective_state_changed(_objective_id: StringName, _state: ObjectiveController.State) -> void:
	_refresh_objective_tracker()


func _refresh_objective_tracker() -> void:
	_tracker.show_objective(_objectives.get_active_objective())
