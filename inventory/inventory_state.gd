class_name InventoryState
extends RefCounted

signal changed

var _definitions: Dictionary[StringName, ItemDefinition] = {}
var _quantities: Dictionary[StringName, int] = {}


func add_item(definition: ItemDefinition, quantity: int = 1) -> bool:
	if definition == null or not definition.is_valid() or quantity <= 0:
		return false
	var item_id := definition.item_id
	if _definitions.has(item_id) and _definitions[item_id] != definition:
		return false
	var current := get_quantity(item_id)
	if current > 9223372036854775807 - quantity:
		return false
	_definitions[item_id] = definition
	_quantities[item_id] = current + quantity
	changed.emit()
	return true


func get_quantity(item_id: StringName) -> int:
	return _quantities.get(item_id, 0)


func get_items() -> Array[ItemDefinition]:
	# Return a fresh list; callers cannot change the storage dictionaries.
	var items: Array[ItemDefinition] = []
	for definition in _definitions.values():
		items.append(definition)
	return items
