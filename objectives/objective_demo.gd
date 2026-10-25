extends Node

# Temporary manual-verification adapter. Remove this node/script and the demo
# resource assignment when narrative events take over. No dialogue dependency.
const DEMO_ID: StringName = &"demo_investigate_computer"

@export var controller: ObjectiveController


func _ready() -> void:
	set_process_unhandled_key_input(OS.is_debug_build() and controller != null)


func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey:
		return
	var key := event as InputEventKey
	if not key.pressed or key.echo or key.has_modifiers():
		return
	match key.physical_keycode:
		KEY_J:
			controller.activate_objective(DEMO_ID)
		KEY_K:
			controller.complete_objective(DEMO_ID)
		_:
			return
	get_viewport().set_input_as_handled()
