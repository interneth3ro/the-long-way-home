extends SceneTree
## Authored assertions only. No approved runner dispatches this script.

const Rules = preload("res://construction/extractor_anchor_rules.gd")
const Inspection = preload("res://scenes/experiments/resource_generation_v2/extractor_anchor_inspection.gd")
const Descriptors = preload("res://scenes/world/resource_generation_descriptors.gd")
const Generator = preload("res://scenes/world/starting_resource_generator.gd")
const Context = preload("res://scenes/world/resource_generation_crash_site.gd")
const EXTRACTOR = preload("res://inventory/extractor.tres")
const FERRITE = preload("res://scenes/world/resource_definitions/v2/ferrite.tres")
const CARBITE = preload("res://scenes/world/resource_definitions/v2/carbite.tres")
const CUPRITE = preload("res://scenes/world/resource_definitions/v2/cuprite.tres")
var _failures: int = 0
var _checks: int = 0


class Fixture:
	extends "res://scenes/world/ordinary_resource_generator.gd"
	var members: Array = []
	func query(_area: Rect2) -> Dictionary:
		return {"ok": true, "deposits": members.duplicate(true)}
	func descriptor_by_id(identity: String) -> Dictionary:
		for member: Dictionary in members:
			if member.deposit_id == identity:
				return {"ok": true, "descriptor": member.duplicate(true)}
		return {"ok": false}


class RejectRemoval:
	extends InventoryState
	func remove_item(_definition: ItemDefinition, _quantity: int = 1, _notify: bool = true) -> bool:
		return false


class RejectRecovery:
	extends InventoryState
	func add_items(_items: Array[Dictionary], _notify: bool = true) -> bool:
		return false


func _check(condition: bool, label: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		printerr("FAIL: " + label)


func _fixture() -> Fixture:
	var definitions: Array[WorldResourceDefinition] = [FERRITE]
	var source := Fixture.new(42, definitions, [])
	var anchors: Array[Rect2i] = [Rect2i(-2, -2, 4, 4), Rect2i(4, -2, 4, 4)]
	var made := Descriptors.create_location("ordinary-v2-1", 42, Vector2i(-1, -1), 0, &"ferrite", anchors)
	source.members = made.location.deposits
	return source


func _environment(point: Vector2 = Vector2.ZERO) -> Dictionary:
	var inventory := InventoryState.new()
	inventory.add_item(EXTRACTOR, 2)
	return {"player_point": point, "range": 160.0, "obstacle_clear": true, "player_clear": true,
		"inventory": inventory}


func _geometry() -> void:
	var source := _fixture()
	var first: Dictionary = source.members[0]
	_check(Rules.bounds(first.anchor_cells) == Rect2(-64, -64, 128, 128), "exact 4x4 geometry and world conversion")
	_check(WorldCoordinates.world_to_construction(Vector2(-0.01, -32.01)) == Vector2i(-1, -2), "negative coordinates floor")
	_check(Rules.select(Vector2(96, 0), source.members).deposit_id == first.deposit_id, "stable tie breaking")
	source.members.reverse()
	_check(Rules.select(Vector2(96, 0), source.members).deposit_id == first.deposit_id, "query-order independence")
	_check(not Rules.select(Vector2(-96, 0), source.members).is_empty(), "snap tolerance inclusive edge")
	_check(Rules.select(Vector2(-96.01, 0), source.members).is_empty(), "snap tolerance outside")
	_check(Rules.select(Vector2(-96, -96), source.members).is_empty(), "Euclidean corner tolerance")
	_check(Rules.select(Vector2(INF, 0), source.members).is_empty(), "nonfinite cursor rejected")
	_check(Rules.target(source, Vector2(10000, 0)).is_empty(), "no distant snapping")
	var state := Inspection.new()
	_check(state.configure(source), "inspection context configured")
	var preview: Dictionary = state.preview(Vector2.ZERO, EXTRACTOR, 0, _environment())
	var ticket: Dictionary = preview.ticket
	_check(preview.reason.is_empty(), "valid unoccupied anchor")
	var malformed := ticket.duplicate()
	malformed.deposit_id = 42
	_check(state.inspect_rejection(malformed, EXTRACTOR, Vector2i(-2, -2), 0, _environment()) == "Unavailable anchor", "malformed ticket fails closed")
	for turn in range(4):
		var rotated: Dictionary = state.preview(Vector2.ZERO, EXTRACTOR, turn, _environment())
		_check(rotated.ticket == ticket and rotated.bounds == preview.bounds, "rotation without anchor displacement")
		_check(state.inspect_rejection(ticket, EXTRACTOR, Vector2i(-2, -2), turn, _environment()).is_empty(), "exact footprint alignment")
	for cell in [Vector2i(-1, -2), Vector2i(2, -2), Vector2i(4, -2)]:
		_check(not state.inspect_rejection(ticket, EXTRACTOR, cell, 0, _environment()).is_empty(), "partial adjacent and wrong deposit rejected")
	var wrong: MachineDefinition = EXTRACTOR.duplicate(true)
	wrong.footprint_cells = Vector2i(4, 3)
	_check(not state.inspect_rejection(ticket, wrong, Vector2i(-2, -2), 0, _environment()).is_empty(), "wrong footprint rejected")
	wrong = EXTRACTOR.duplicate(true)
	wrong.compatible_resources = [&"cuprite"]
	_check(state.preview(Vector2.ZERO, wrong, 0, _environment()).reason == "Incompatible resource", "incompatible resource")
	wrong = EXTRACTOR.duplicate(true)
	wrong.input_item = EXTRACTOR.output_item
	_check(state.preview(Vector2.ZERO, wrong, 0, _environment()).reason == "Unsupported inspection machine", "preview rejects unsupported input machine")
	_check(Rules.rejection(source, ticket, EXTRACTOR, Vector2i(-2, -2), 0, 0) == "Inactive resource", "no inactive gameplay activation")
	var blocked := _environment()
	blocked.obstacle_clear = false
	_check(state.preview(Vector2.ZERO, EXTRACTOR, 0, blocked).reason == "Blocked by a solid obstacle", "environmental obstacle")
	blocked = _environment()
	blocked.player_clear = false
	_check(state.preview(Vector2.ZERO, EXTRACTOR, 0, blocked).reason == "Dave is in the footprint", "player safety")
	_check(state.preview(Vector2.ZERO, EXTRACTOR, 0, {}).reason == "Unavailable environment", "missing context fails closed")
	blocked = _environment()
	blocked.inventory = InventoryState.new()
	_check(state.preview(Vector2.ZERO, EXTRACTOR, 0, blocked).reason == "No packaged machine in inventory", "preview inventory identity and quantity")
	_check(state.preview(Vector2.ZERO, EXTRACTOR, 0, _environment(Vector2(1000, 0))).reason == "Out of construction range", "construction range")
	state.seed_value += 1
	_check(state.inspect_rejection(ticket, EXTRACTOR, Vector2i(-2, -2), 0, _environment()) == "Unavailable anchor", "world seed invalidation")
	state.seed_value -= 1
	var stale_policy := ticket.duplicate()
	stale_policy.policy = "retired-policy"
	_check(state.inspect_rejection(stale_policy, EXTRACTOR, Vector2i(-2, -2), 0, _environment()) == "Unavailable anchor", "changed policy ticket rejected")
	_check(state.configure(_fixture()), "replace same policy source")
	_check(state.inspect_rejection(ticket, EXTRACTOR, Vector2i(-2, -2), 0, _environment()) == "Unavailable anchor", "source and policy invalidation")
	state = Inspection.new()
	state.configure(source)
	preview = state.preview(Vector2.ZERO, EXTRACTOR, 0, _environment())
	source.members.clear()
	_check(state.inspect_rejection(preview.ticket, EXTRACTOR, Vector2i(-2, -2), 0, _environment()) == "Unavailable anchor", "removed authoritative deposit")


func _transactions() -> void:
	var source := _fixture()
	var state := Inspection.new()
	state.configure(source)
	var ticket: Dictionary = state.preview(Vector2.ZERO, EXTRACTOR, 0, _environment()).ticket
	var cell: Vector2i = ticket.anchor_cells.position
	var inventory := InventoryState.new()
	_check(state.confirm(ticket, EXTRACTOR, cell, 0, _environment(), inventory) == 0, "empty inventory rejects placement")
	var rejecting := RejectRemoval.new()
	rejecting.add_item(EXTRACTOR, 2)
	_check(state.confirm(ticket, EXTRACTOR, cell, 0, _environment(), rejecting) == 0 \
		and rejecting.get_quantity(&"extractor") == 2 and state.occupant(ticket.deposit_id) == 0, "failed placement without inventory consumption or claim")
	inventory.add_item(EXTRACTOR, 2)
	var observed: Array[int] = []
	inventory.changed.connect(func() -> void:
		observed.append(state.confirm(ticket, EXTRACTOR, cell, 0, _environment(), inventory)))
	var machine_id: int = state.confirm(ticket, EXTRACTOR, cell, 0, _environment(), inventory)
	_check(machine_id > 0 and state.occupant(ticket.deposit_id) == machine_id, "successful claim has committed machine ID")
	_check(observed == [0] and state.get_machines().size() == 1, "reentrant confirmation rejected")
	_check(state.preview(Vector2.ZERO, EXTRACTOR, 1, _environment()).reason == "Occupied anchor", "occupied-anchor rejection")
	_check(state.confirm(ticket, EXTRACTOR, cell, 0, _environment(), inventory) == 0 \
		and inventory.get_quantity(&"extractor") == 1, "duplicate claim and repeated confirmation rejected")
	var before: Dictionary = state.get_machine(machine_id)
	state.advance_production(100.0)
	_check(state.get_machine(machine_id) == before, "inspection never produces Ferrite or Cuprite")
	_check(not state.configure(_fixture()), "cannot replace world while occupied")
	_check(not state.recover_machine(machine_id, RejectRecovery.new(), Vector2.ZERO, 160.0) \
		and state.occupant(ticket.deposit_id) == machine_id, "failed recovery preserves claim")
	_check(not state.recover_machine(machine_id, inventory, Vector2(1000, 0), 1.0), "recovery range preserved")
	var released: Array[int] = []
	state.machines_changed.connect(func() -> void: released.append(state.occupant(ticket.deposit_id)))
	_check(state.recover_machine(machine_id, inventory, Vector2.ZERO, 160.0), "existing recovery transaction succeeds")
	_check(state.occupant(ticket.deposit_id) == 0 and released == [0], "recovery releases occupancy before callbacks")
	_check(inventory.get_quantity(&"extractor") == 2, "recovery returns same packaged identity")
	_check(not state.recover_machine(machine_id, inventory, Vector2.ZERO, 160.0), "repeated recovery rejected")
	_check(state.confirm(ticket, EXTRACTOR, cell, 3, _environment(), inventory) > machine_id, "recovered anchor available with monotonic machine IDs")
	# Synthetic independent record in the SAME registry demonstrates overlap checks.
	var other := Inspection.new()
	other.configure(source)
	other._machines[99] = {"id": 99, "definition": EXTRACTOR, "cell": cell, "turns": 0}
	var overlap: Dictionary = other.preview(Vector2.ZERO, EXTRACTOR, 0, _environment())
	_check(overlap.reason == "Overlaps a deployed machine", "machine obstruction without proximity occupancy")
	_check(other.confirm(overlap.ticket, EXTRACTOR, cell, 0, _environment(), inventory) == 0, "blocked placement consumes nothing")
	_check(other.deploy_machine_instance(EXTRACTOR, cell, 0, inventory, null, null, 160) == 0, "normal deployment entry stays disabled")


func _real_sources() -> void:
	var crossed := false
	for world_seed in [0, 42, -79]:
		var definitions: Array[WorldResourceDefinition] = [FERRITE, CARBITE, CUPRITE]
		var source := Generator.new(world_seed, definitions, Context.protected_bounds(), Context.SHIP_REFERENCE)
		_check(source.is_ready(), "representative seed preparation")
		if not source.is_ready():
			continue
		var reservations := source.reservations()
		var count := 0
		for location: Dictionary in reservations.locations:
			for member: Dictionary in location.deposits:
				count += 1
				var cursor := Rules.bounds(member.anchor_cells).get_center()
				var forward := Rules.target(source, cursor)
				_check(forward.get("deposit_id") == member.deposit_id, "real source anchor targeting across regions")
				crossed = crossed or source.owner_at(cursor) != location.owner_region
				# Unrelated query and reversed reservation visitation cannot alter target.
				source.query(Rect2(Vector2(10000, -10000), Vector2(128, 128)))
				_check(Rules.target(source, cursor) == forward, "real query-order independence")
		_check(count == 7 and reservations == source.reservations(), "all seven reservations unchanged")
	_check(crossed, "cross-region deposit coverage")


func _initialize() -> void:
	_geometry()
	_transactions()
	_real_sources()
	print("Extractor anchor assertions: %d checks, %d failures" % [_checks, _failures])
	quit(0 if _failures == 0 else 1)
