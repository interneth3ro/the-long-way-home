extends WorldInteractable

@onready var _progression := get_tree().get_first_node_in_group(&"playthrough") as PlaythroughState


func _ready() -> void:
	if _progression != null:
		_progression.fabricator_recovery_completed.connect(_refresh_rack)
	_refresh_rack()


func can_interact() -> bool:
	return interaction_enabled and _progression != null \
		and _progression.ferrite_ingot_acquired and not _progression.fabricator_recovered


func interact() -> String:
	if can_interact():
		_progression.recover_fabricator()
	return ""


func _refresh_rack() -> void:
	var recovered := _progression != null and _progression.fabricator_recovered
	$Module.visible = not recovered
	$Secured.visible = not recovered
	$Empty.visible = recovered
