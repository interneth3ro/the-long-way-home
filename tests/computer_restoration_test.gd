extends SceneTree

# Unexecuted. This script is NOT part of the authorized Native runner inventory.
# Separate owner execution approval is required; static checks do not run it.
const PLATE: ItemDefinition = preload("res://inventory/ferrite_plate.tres")
const ROD: ItemDefinition = preload("res://inventory/ferrite_rod.tres")
var _failures := 0
var _notifications := 0
var _restorations := 0
var _cinematics := 0


class RejectingInventory extends InventoryState:
	func remove_items(_items: Array[Dictionary], _notify: bool = true) -> bool:
		return false


func _check(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		push_error(message)


func _session(plates: int, rods: int) -> PlaythroughState:
	# Deliberately off-tree: no planet generation, world processing or presentation.
	var state := PlaythroughState.new()
	state.ferrite_plate_acquired = true
	state.computer_opening_completed = true
	state.computer_inspection_completed = true
	if plates > 0:
		state.inventory.add_item(PLATE, plates)
	if rods > 0:
		state.inventory.add_item(ROD, rods)
	return state


func _initialize() -> void:
	_check(PLATE.is_valid() and ROD.is_valid() and PLATE != ROD, "Two valid distinct item resources")
	for amounts in [Vector2i(0, 0), Vector2i(4, 3), Vector2i(3, 4), Vector2i(8, 0)]:
		var state := _session(amounts.x, amounts.y)
		_check(not state.restore_computer(), "Insufficient inventory rejects repair")
		_check(not state.computer_restored, "Rejected repair preserves damaged state")
		_check(state.inventory.get_quantity(PLATE.item_id) == amounts.x
			and state.inventory.get_quantity(ROD.item_id) == amounts.y, "No partial consumption")
		state.free()
	var state := _session(4, 4)
	_check(state.has_computer_materials(), "Exact Materials readiness")
	state.inventory.remove_item(ROD)
	_check(not state.has_computer_materials(), "Readiness reverses after spending")
	state.inventory.add_item(ROD)
	state.computer_opening_completed = false
	_check(not state.restore_computer(), "Cannot bypass opening completion")
	state.computer_opening_completed = true
	state.computer_inspection_completed = false
	_check(not state.restore_computer(), "Dismissed inspection cannot authorize repair")
	state.computer_inspection_completed = true
	state.ferrite_plate_acquired = false
	_check(not state.restore_computer(), "First Plate milestone required")
	state.ferrite_plate_acquired = true
	state.computer_restoration_completed.connect(func():
		_restorations += 1
		_check(state.computer_restored, "Milestone callback sees committed state")
		_check(not state.restore_computer(), "Milestone callback cannot reenter"))
	state.inventory.changed.connect(func():
		_notifications += 1
		_check(state.computer_restored, "Inventory callback sees committed repair")
		_check(state.inventory.get_quantity(PLATE.item_id) == 0
			and state.inventory.get_quantity(ROD.item_id) == 0, "Single atomic inventory notification")
		_check(not state.restore_computer(), "Inventory callback cannot reenter"))
	state.computer_cinematic_completed.connect(func(): _cinematics += 1)
	_check(state.restore_computer(), "Exact 4+4 repairs successfully")
	_check(not state.restore_computer(), "Repeated confirmation rejected")
	_check(_notifications == 1 and _restorations == 1, "Exactly one publication of repair")
	_check(not state.computer_cinematic_finished, "Transaction does not finish cinematic")
	state.finish_computer_cinematic()
	state.finish_computer_cinematic()
	_check(_cinematics == 1, "Cinematic completion is idempotent")
	state.free()
	state = _session(7, 9)
	_check(state.restore_computer(), "Surplus inventory can repair")
	_check(state.inventory.get_quantity(PLATE.item_id) == 3
		and state.inventory.get_quantity(ROD.item_id) == 5, "Consumes exactly 4+4")
	state.free()
	state = _session(4, 4)
	var rejected := RejectingInventory.new()
	rejected.add_item(PLATE, 4)
	rejected.add_item(ROD, 4)
	state.inventory = rejected
	_check(not state.restore_computer() and not state.computer_restored, "Batch failure preserves milestone")
	_check(rejected.get_quantity(PLATE.item_id) == 4 and rejected.get_quantity(ROD.item_id) == 4,
		"Batch failure preserves both materials")
	_check(state.can_restore_computer(), "Failure releases transaction guard")
	state.free()
	var inventory := InventoryState.new()
	inventory.add_item(PLATE, 4)
	inventory.add_item(ROD, 3)
	_check(not inventory.remove_items([
		{"definition": PLATE, "quantity": 4}, {"definition": ROD, "quantity": 4}]),
		"Second ingredient rejects entire batch")
	_check(inventory.get_quantity(PLATE.item_id) == 4 and inventory.get_quantity(ROD.item_id) == 3,
		"Failed later ingredient leaves earlier ingredient intact")
	var impostor := ROD.duplicate() as ItemDefinition
	_check(not inventory.remove_items([{"definition": PLATE, "quantity": 4},
		{"definition": impostor, "quantity": 1}]), "Definition identity required")
	_check(inventory.get_quantity(PLATE.item_id) == 4, "Identity failure is also atomic")
	print("Computer restoration regression failures: %d" % _failures)
	quit(0 if _failures == 0 else 1)
