extends WorldInteractable

@export var deposit_id: StringName = &"crash_site_ferrite"

@onready var _progression := get_tree().get_first_node_in_group(&"playthrough") as PlaythroughState


func _ready() -> void:
	if _progression != null:
		_progression.ferrite_discovery_completed.connect(_refresh_marker)
	_refresh_marker()


func can_interact() -> bool:
	return interaction_enabled and _progression != null and not _progression.ferrite_discovered


func interact() -> String:
	if can_interact():
		_progression.discover_ferrite(deposit_id)
	# The discovery signal routes to the musing presenter, never inspection/dialogue UI.
	return ""


func _refresh_marker() -> void:
	# Only this introductory marker disappears. Geology and future formations do not.
	var discovered := _progression != null and _progression.ferrite_discovered
	visible = not discovered
	interaction_enabled = not discovered
	# Discovery can be emitted during physics interaction. Availability/visuals
	# change immediately; defer the physics shape mutation without removing nodes.
	$CollisionShape2D.set_deferred("disabled", discovered)
