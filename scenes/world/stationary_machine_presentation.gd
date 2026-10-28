extends Node2D

# Presentation only; recovery transactions remain owned by PlaythroughState.
@export_enum("extractor", "smelter", "fabricator") var machine_id: String = "extractor"

var _progression: PlaythroughState
var _objectives: ObjectiveController


func _enter_tree() -> void:
	# _ready runs once; cached rooms enter again, including transition rollback.
	refresh_presentation.call_deferred()


func _ready() -> void:
	_progression = get_tree().get_first_node_in_group(&"playthrough") as PlaythroughState
	if _progression != null:
		_objectives = _progression.get_parent().get_node("ObjectiveController") as ObjectiveController
		for event in [&"ferrite_discovery_completed", &"extractor_recovery_completed",
				&"extractor_deployment_completed", &"ferrite_acquisition_completed",
				&"smelter_recovery_completed", &"smelter_deployment_completed",
				&"ferrite_ingot_acquisition_completed", &"fabricator_recovery_completed",
				&"ferrite_plate_acquisition_completed"]:
			_progression.connect(event, refresh_presentation)
	if _objectives != null:
		_objectives.objective_state_changed.connect(_on_objective_state_changed)
	refresh_presentation()


func _on_objective_state_changed(_id: StringName, _state: ObjectiveController.State) -> void:
	refresh_presentation()


func refresh_presentation() -> void:
	# Detached rooms retain signal connections, but have no active physics world.
	if not is_inside_tree():
		return
	var recovered := _is_recovered()
	$Visual.visible = not recovered
	var outline := $Visual/Machine.material as ShaderMaterial
	outline.set_shader_parameter("outline_enabled", not recovered and _is_highlighted())
	$Body/Shape.set_deferred("disabled", recovered)
	$Interaction/Shape.set_deferred("disabled", recovered)
	# The V2 Extractor adapter owns eligibility; later machines remain dormant.
	if machine_id != "extractor":
		$Interaction.interaction_enabled = false


func _is_recovered() -> bool:
	if _progression == null:
		return false
	match machine_id:
		"extractor": return _progression.extractor_recovered
		"smelter": return _progression.smelter_recovered
		"fabricator": return _progression.fabricator_recovered
	return false


func _is_highlighted() -> bool:
	if _progression == null or _objectives == null:
		return false
	var active := _objectives.get_active_objective()
	if active == null or active.objective_id != &"restore_computer":
		return false
	# Match Main's existing display-stage precedence without owning a new stage.
	if _progression.ferrite_plate_acquired or _progression.fabricator_recovered:
		return false
	if _progression.ferrite_ingot_acquired:
		return machine_id == "fabricator"
	if _progression.smelter_deployed or _progression.smelter_recovered:
		return false
	if _progression.ferrite_acquired:
		return machine_id == "smelter"
	if _progression.extractor_deployed or _progression.extractor_recovered:
		return false
	return machine_id == "extractor" and _progression.ferrite_discovered
