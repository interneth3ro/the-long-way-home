extends WorldInteractable

@export var deposit_id: StringName = &"crash_site_ferrite"

@onready var _progression := get_tree().get_first_node_in_group(&"playthrough") as PlaythroughState


func can_interact() -> bool:
	return interaction_enabled and _progression != null and not _progression.ferrite_discovered


func interact() -> String:
	if can_interact():
		_progression.discover_ferrite(deposit_id)
	# The discovery signal routes to the musing presenter, never inspection/dialogue UI.
	return ""
