extends WorldInteractable

@export_file("*.tscn") var source_scene: String
@export_file("*.tscn") var destination_scene: String
@export var destination_spawn: StringName
@export var presentation: SceneTransitionController.Presentation = SceneTransitionController.Presentation.IMMEDIATE


func can_interact() -> bool:
	var controller := get_tree().get_first_node_in_group(&"scene_transitions") as SceneTransitionController
	return interaction_enabled and controller != null and not controller.is_transitioning()


func interact() -> String:
	if can_interact():
		var controller := get_tree().get_first_node_in_group(&"scene_transitions") as SceneTransitionController
		controller.request_transition(source_scene, destination_scene, destination_spawn, presentation)
	return ""
