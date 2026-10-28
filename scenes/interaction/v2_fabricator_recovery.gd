extends WorldInteractable

# V2 action only; PlaythroughState owns the transaction and P3 owns presentation.
@onready var _progression := get_tree().get_first_node_in_group(&"playthrough") as PlaythroughState


func can_interact() -> bool:
	return is_inside_tree() and interaction_enabled and _progression != null \
		and _progression.ferrite_ingot_acquired and not _progression.fabricator_recovered


func interact() -> String:
	if not can_interact():
		return ""
	# The transaction also guards synchronous inventory callbacks and repeat input.
	if not _progression.recover_fabricator():
		return "Unable to recover the Fabricator."
	return ""
