extends WorldInteractable

@onready var _progression := get_tree().get_first_node_in_group(&"playthrough") as PlaythroughState


func _ready() -> void:
	if _progression != null:
		_progression.smelter_recovery_completed.connect(_refresh_rack)
	_refresh_rack()


func can_interact() -> bool:
	return interaction_enabled and _progression != null \
		and _progression.ferrite_acquired and not _progression.smelter_recovered


func interact() -> String:
	if can_interact():
		_progression.recover_smelter()
	return ""


func _refresh_rack() -> void:
	var recovered := _progression != null and _progression.smelter_recovered
	$Module.visible = not recovered
	$Secured.visible = not recovered
	$Empty.visible = recovered
