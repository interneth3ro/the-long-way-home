class_name InventoryState
extends RefCounted

signal changed

var _definitions: Dictionary[StringName, ItemDefinition] = {}
var _quantities: Dictionary[StringName, int] = {}


# Planet transactions defer notification until both inventory and world agree.
func add_item(definition: ItemDefinition, quantity: int = 1, notify: bool = true) -> bool:
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
	if notify:
		changed.emit()
	return true


func remove_item(definition: ItemDefinition, quantity: int = 1, notify: bool = true) -> bool:
	if definition == null or quantity <= 0 or _definitions.get(definition.item_id) != definition:
		return false
	var current := get_quantity(definition.item_id)
	if current < quantity:
		return false
	if current == quantity:
		_quantities.erase(definition.item_id)
		_definitions.erase(definition.item_id)
	else:
		_quantities[definition.item_id] = current - quantity
	if notify:
		changed.emit()
	return true


func get_quantity(item_id: StringName) -> int:
	return _quantities.get(item_id, 0)


# Validate the entire recovery payload against private copies before committing.
# No callbacks or published partial additions; the planet notifies after removal.
func add_items(items: Array[Dictionary], notify: bool = true) -> bool:
	var definitions := _definitions.duplicate()
	var quantities := _quantities.duplicate()
	for item in items:
		var definition: ItemDefinition = item.get("definition")
		var quantity: int = item.get("quantity", 0)
		if definition == null or not definition.is_valid() or quantity <= 0:
			return false
		var item_id := definition.item_id
		if definitions.has(item_id) and definitions[item_id] != definition:
			return false
		var current: int = quantities.get(item_id, 0)
		if current > 9223372036854775807 - quantity:
			return false
		definitions[item_id] = definition
		quantities[item_id] = current + quantity
	_definitions = definitions
	_quantities = quantities
	if notify:
		changed.emit()
	return true


func get_items() -> Array[ItemDefinition]:
	# Return a fresh list; callers cannot change the storage dictionaries.
	var items: Array[ItemDefinition] = []
	for definition in _definitions.values():
		items.append(definition)
	return items
