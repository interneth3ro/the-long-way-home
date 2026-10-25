class_name ObjectiveController
extends Node

signal objective_state_changed(objective_id: StringName, state: State)

enum State { INACTIVE, ACTIVE, COMPLETED }

@export var definitions: Array[ObjectiveDefinition] = []

# The only mutable progression state; definitions are read-only content.
var _states: Dictionary[StringName, State] = {}


func _ready() -> void:
	# Reject ambiguous IDs entirely rather than choosing a duplicate definition.
	var seen: Array[StringName] = []
	for definition in definitions:
		if definition == null or not definition.is_valid():
			push_warning("ObjectiveController: ignored invalid definition.")
			continue
		var objective_id := definition.objective_id
		if objective_id in seen:
			_states.erase(objective_id)
			push_warning("ObjectiveController: rejected duplicate ID: %s" % objective_id)
			continue
		seen.append(objective_id)
		_states[objective_id] = State.INACTIVE


func activate_objective(objective_id: StringName) -> bool:
	if not _states.has(objective_id) or _states[objective_id] != State.INACTIVE:
		return false
	_states[objective_id] = State.ACTIVE
	objective_state_changed.emit(objective_id, State.ACTIVE)
	return true


func complete_objective(objective_id: StringName) -> bool:
	if not _states.has(objective_id) or _states[objective_id] != State.ACTIVE:
		return false
	_states[objective_id] = State.COMPLETED
	objective_state_changed.emit(objective_id, State.COMPLETED)
	return true


# -1 distinguishes an unknown/rejected ID from a registered inactive objective.
func get_objective_state(objective_id: StringName) -> int:
	return _states.get(objective_id, -1)


# Stable definition order selects the displayed objective if several are active.
func get_active_objective() -> ObjectiveDefinition:
	for definition in definitions:
		if definition != null and definition.is_valid() \
				and get_objective_state(definition.objective_id) == State.ACTIVE:
			return definition
	return null
