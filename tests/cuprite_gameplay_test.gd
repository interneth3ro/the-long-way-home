extends SceneTree
## Shared Ferrite/Cuprite/Carbite behavioral fixture. Authored only; not dispatched or executed.

const EXTRACTOR = preload("res://inventory/extractor.tres")
const Rules = preload("res://construction/extractor_anchor_rules.gd")
var _failures: int = 0
var _resource_label: String = ""

# Faults exist only at the fixture read boundary, never in production authority.
class DescriptorFailure:
	extends PlanetWorldState
	var descriptor_failure: String = ""
	func _init(world_seed: int = 26026) -> void:
		super(world_seed)
	func resource_descriptor_v2_by_id(identity: String, token: RefCounted) -> Dictionary:
		if descriptor_failure == "missing":
			return {"ok": false, "error": "fixture missing descriptor"}
		if descriptor_failure == "anchor":
			return {"ok": true, "descriptor": {}}
		var result := super.resource_descriptor_v2_by_id(identity, token)
		if result.ok and descriptor_failure == "geometry":
			result.descriptor.anchor_cells = Rect2i(0, 0, 3, 4)
		if result.ok and descriptor_failure == "unsupported":
			result.descriptor.resource_type = "unsupported"
		return result

class RejectRemoval:
	extends InventoryState
	func remove_item(_definition: ItemDefinition, _quantity: int = 1, _notify: bool = true) -> bool:
		return false

class RejectRecovery:
	extends InventoryState
	func add_items(_items: Array[Dictionary], _notify: bool = true) -> bool:
		return false

func _check(condition: bool, label: String) -> void:
	if not condition:
		_failures += 1
		push_error(_resource_label + ": " + label)

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	for resource_type in ["ferrite", "cuprite", "carbite"]:
		await _test_gameplay(resource_type)
	_test_discovery()
	await _test_exterior_revisit()
	_test_live_window_requests()
	for resource_type in ["ferrite", "cuprite", "carbite"]:
		_test_presentation(resource_type)
	print("Three-resource gameplay regression failures: %d" % _failures)
	quit(0 if _failures == 0 else 1)


func _test_gameplay(resource_type: String) -> void:
	_resource_label = resource_type
	var members := [
		{"deposit_id": "a", "anchor_cells": Rect2i(-2, -2, 4, 4)},
		{"deposit_id": "b", "anchor_cells": Rect2i(4, -2, 4, 4)}]
	_check(Rules.select(Vector2(96, 0), members).deposit_id == "a", "stable tie")
	members.reverse()
	_check(Rules.select(Vector2(96, 0), members).deposit_id == "a", "stable tie independent of order")
	_check(Rules.select(Vector2(-96, 0), members).deposit_id == "a", "inclusive snapping")
	_check(Rules.select(Vector2(-96.01, 0), members).is_empty(), "outside snapping")
	var state := DescriptorFailure.new(42)
	var context := state.resource_generation_v2_context()
	_check(context.ok, "healthy authoritative context")
	if not context.ok:
		quit(1)
		return
	var layout := state.starting_resource_reservations_v2(context.token)
	var member: Dictionary = {}
	var carbite: Dictionary = {}
	for location: Dictionary in layout.locations:
		if location.resource_type == resource_type:
			member = location.deposits[0]
		if location.resource_type == "carbite":
			carbite = location.deposits[0]
	var ore := load("res://inventory/%s_ore.tres" % resource_type) as ItemDefinition
	_check(ore != null and ore.item_id == StringName(resource_type + "_ore")
		and ItemPresentation.ICONS.has(ore.item_id), "canonical ore and icon identity")
	var cell: Vector2i = member.anchor_cells.position
	var center := Rules.bounds(member.anchor_cells).get_center()
	# Use the authoritative descriptor ticket directly for transaction tests;
	# live routing always uses the same V2 authority.
	var ticket := {"token": context.token, "deposit_id": member.deposit_id,
		"resource_type": member.resource_type, "anchor_cells": member.anchor_cells}
	var foreign := ticket.duplicate()
	foreign.token = RefCounted.new()
	_check(state.extractor_anchor_rejection_v2(foreign, EXTRACTOR, cell, 0) == "Unavailable anchor",
		"foreign context rejected")
	var forged_id := ticket.duplicate()
	forged_id.deposit_id = member.deposit_id + ":forged"
	_check(state.extractor_anchor_rejection_v2(forged_id, EXTRACTOR, cell, 0) == "Unavailable anchor",
		"forged deposit identity rejected")
	for turn in range(4):
		_check(state.extractor_anchor_rejection_v2(ticket, EXTRACTOR, cell, turn).is_empty(), "exact rotated 4x4 alignment")
		var selected := state.extractor_target_v2(center, EXTRACTOR, turn)
		_check(selected.ticket == ticket and selected.cell == cell, "live authoritative snapping")
	var restricted := EXTRACTOR.duplicate() as MachineDefinition
	restricted.compatible_resources = [&"ferrite"]
	var incompatible := {"token": context.token, "deposit_id": carbite.deposit_id,
		"resource_type": carbite.resource_type, "anchor_cells": carbite.anchor_cells}
	_check(state.extractor_anchor_rejection_v2(incompatible, restricted,
		carbite.anchor_cells.position, 0) == "Incompatible resource", "incompatible feedback")
	var ground := Node2D.new()
	ground.add_to_group(&"construction_world")
	root.add_child(ground)
	var player := CharacterBody2D.new()
	player.position = center - Vector2(90, 0)
	var feet := CollisionShape2D.new()
	var feet_shape := CircleShape2D.new()
	feet_shape.radius = 10.0
	feet.shape = feet_shape
	player.add_child(feet)
	ground.add_child(player)
	await physics_frame
	var rejecting := RejectRemoval.new()
	rejecting.add_item(EXTRACTOR, 2)
	_check(state.deploy_extractor_v2(ticket, EXTRACTOR, cell, 0, rejecting, player, ground, 160) == 0
		and rejecting.get_quantity(&"extractor") == 2 and state.get_machines().is_empty()
		and state.extractor_occupant_v2(member.deposit_id) == 0, "failed removal leaves all state unchanged")
	var relabeled := ticket.duplicate()
	relabeled.resource_type = "carbite" if resource_type == "ferrite" else "ferrite"
	_check(state.extractor_anchor_rejection_v2(relabeled, EXTRACTOR, cell, 0) == "Unavailable anchor", "changed resource rejected")
	relabeled = ticket.duplicate()
	relabeled.anchor_cells = Rect2i(cell + Vector2i.ONE, Vector2i(4, 4))
	_check(state.extractor_anchor_rejection_v2(relabeled, EXTRACTOR, cell, 0) == "Unavailable anchor", "changed anchor rejected")
	var inventory := InventoryState.new()
	inventory.add_item(EXTRACTOR, 2)
	_check(state.deploy_machine_instance(EXTRACTOR, cell, 0, inventory, player, ground, 160) == 0
		and not state.deploy_machine(EXTRACTOR, cell, 0, inventory, player, ground, 160)
		and inventory.get_quantity(&"extractor") == 2 and state.get_machines().is_empty(),
		"unticketed generic Extractor bypass rejected atomically")
	for invalid_ticket: Dictionary in [foreign, forged_id, relabeled]:
		_check(state.deploy_extractor_v2(invalid_ticket, EXTRACTOR, cell, 0,
			inventory, player, ground, 160) == 0 and inventory.get_quantity(&"extractor") == 2
			and state.get_machines().is_empty() and state.extractor_occupant_v2(member.deposit_id) == 0,
			"spoofed confirmation consumes nothing")
	_check(state.deploy_extractor_v2(ticket, EXTRACTOR, cell + Vector2i.ONE, 0,
		inventory, player, ground, 160) == 0 and inventory.get_quantity(&"extractor") == 2,
		"failed placement alignment consumes nothing")
	_check(state.deploy_extractor_v2(ticket, EXTRACTOR, cell, 0,
		inventory, player, ground, 0) == 0, "failed placement distance")
	state._machines[99] = {"id": 99, "definition": EXTRACTOR, "cell": cell, "turns": 0}
	_check(state.deploy_extractor_v2(ticket, EXTRACTOR, cell, 0, inventory, player, ground, 160) == 0
		and state.extractor_occupant_v2(member.deposit_id) == 0, "failed placement machine overlap without claim")
	state._machines.erase(99)
	var blocker := StaticBody2D.new()
	blocker.collision_layer = PlacementRules.BLOCKING_LAYER
	blocker.position = center
	var solid := CollisionShape2D.new()
	var solid_shape := RectangleShape2D.new()
	solid_shape.size = Vector2(20, 20)
	solid.shape = solid_shape
	blocker.add_child(solid)
	ground.add_child(blocker)
	await physics_frame
	_check(PlacementRules.rejection(state, EXTRACTOR, cell, 0, player, ground, 160,
		inventory, ticket) == "Blocked by a solid obstacle", "failed placement physics obstacle")
	blocker.free()
	player.position = center
	await physics_frame
	_check(PlacementRules.rejection(state, EXTRACTOR, cell, 0, player, ground, 160,
		inventory, ticket) == "Dave is in the footprint", "failed placement player safety")
	player.position = center - Vector2(90, 0)
	await physics_frame
	var notifications: Array[int] = []
	inventory.changed.connect(func() -> void:
		notifications.append(state.extractor_occupant_v2(member.deposit_id))
		_check(state._machine_transaction, "notifications guarded")
		_check(state.deploy_extractor_v2(ticket, EXTRACTOR, cell, 0,
			inventory, player, ground, 160) == 0, "reentrant deployment rejected"))
	var machine_id := state.deploy_extractor_v2(ticket, EXTRACTOR, cell, 0, inventory, player, ground, 160)
	_check(machine_id == 1 and notifications == [1] and state.get_machine(1).v2_deposit_id == member.deposit_id,
		"successful deployment and consistent claim notification")
	_check(state.extractor_anchor_rejection_v2(ticket, EXTRACTOR, cell, 0) == "Occupied anchor", "occupied feedback")
	_check(state.deploy_extractor_v2(ticket, EXTRACTOR, cell, 0, inventory, player, ground, 160) == 0
		and inventory.get_quantity(&"extractor") == 1, "duplicate claim")
	_check(state.stored_output_item(state.get_machine(machine_id)).item_id == ore.item_id, "correct ore item identity")
	var forged := state.get_machine(machine_id)
	forged.v2_resource_type = "carbite" if resource_type == "ferrite" else "ferrite"
	_check(state.stored_output_item(forged) == null, "caller metadata cannot override authority")
	state._machines[machine_id].v2_resource_type = "carbite" if resource_type == "ferrite" else "ferrite"
	_check(state.stored_output_item(state.get_machine(machine_id)).item_id == ore.item_id, "authoritative descriptor outranks cached label")
	var view = preload("res://scenes/ui/extractor_inspection.tscn").instantiate()
	root.add_child(view)
	var current := state.get_machine(machine_id)
	view.refresh(current, state.machine_status(current), true, state.stored_output_item(current))
	_check(view._details.visible and view._yield.text == "1 " + ore.display_name, "inspection empty-buffer ore identity")
	view.free()
	state.advance_production(0.5)
	_check(state.get_machine(machine_id).output == 0, "partial cycle")
	state.advance_production(0.5)
	_check(state.get_machine(machine_id).output == 1, "successful ore production at one second")
	state.advance_production(100.0)
	var full := state.get_machine(machine_id)
	_check(full.output == 20 and full.cycle_progress == 0.0
		and state.machine_status(full) == PlanetWorldState.OperatingStatus.OUTPUT_FULL, "capacity and full-output status")
	state.advance_production(100.0)
	_check(state.get_machine(machine_id) == full, "full output pauses without backlog")
	var populated_view = preload("res://scenes/ui/extractor_inspection.tscn").instantiate()
	root.add_child(populated_view)
	populated_view.refresh(full, state.machine_status(full), true, state.stored_output_item(full))
	_check(populated_view._material.text == ore.display_name and not populated_view._collect.disabled
		and populated_view._material_icon.texture == ItemPresentation.ICONS[ore.item_id],
		"inspection populated-buffer identity")
	populated_view.free()
	var conflict := InventoryState.new()
	var counterfeit := ore.duplicate() as ItemDefinition
	conflict.add_item(counterfeit)
	_check(not state.collect_output(machine_id, conflict, center, 160)
		and state.get_machine(machine_id) == full, "inventory rejection without item loss")
	_check(not state.recover_machine(machine_id, conflict, center, 160)
		and state.get_machine(machine_id) == full
		and state.extractor_occupant_v2(member.deposit_id) == machine_id, "atomic recovery rejection retains output and claim")
	_check(state.collect_output(machine_id, inventory, center, 160)
		and inventory.get_quantity(ore.item_id) == 20
		and (resource_type == "ferrite" or inventory.get_quantity(&"ferrite_ore") == 0), "collection transfers resolved ore only")
	state.advance_production(1.0)
	_check(state.get_machine(machine_id).output == 1, "production resume after collection")
	_check(state.recover_machine(machine_id, inventory, center, 160)
		and inventory.get_quantity(ore.item_id) == 21
		and inventory.get_quantity(&"extractor") == 2
		and state.extractor_occupant_v2(member.deposit_id) == 0, "recovery returns stored ore and releases occupancy")
	var next := state.deploy_extractor_v2(ticket, EXTRACTOR, cell, 0, inventory, player, ground, 160)
	_check(next == 2, "construction and occupancy preserved on redeployment")
	state.advance_production(1.0)
	var stored := state.get_machine(next)
	for failure in ["missing", "anchor", "geometry", "unsupported"]:
		state.descriptor_failure = failure
		state.advance_production(1.0)
		_check(state.get_machine(next) == stored and state.stored_output_item(stored) == null,
			"missing descriptor pauses production" if failure == "missing" else "missing anchor pauses production")
		_check(not state.collect_output(next, inventory, center, 160)
			and not state.recover_machine(next, inventory, center, 160)
			and state.get_machine(next) == stored
			and state.extractor_occupant_v2(member.deposit_id) == next,
			"descriptor failure retains output and claim")
	state.descriptor_failure = ""
	state._extractor_claims_v2.erase(member.deposit_id)
	state.advance_production(1.0)
	_check(state.get_machine(next) == stored and state.stored_output_item(stored) == null,
		"missing claim pauses production")
	state._extractor_claims_v2[member.deposit_id] = 999
	_check(state.stored_output_item(state.get_machine(next)) == null, "foreign occupancy claim rejected")
	state._extractor_claims_v2[member.deposit_id] = next
	var committed_token: RefCounted = state._machines[next].v2_context_token
	state._machines[next].v2_context_token = RefCounted.new()
	_check(state.stored_output_item(state.get_machine(next)) == null, "foreign committed token rejected")
	state._machines[next].v2_context_token = committed_token
	state._machines[next].erase("v2_deposit_id")
	_check(state.stored_output_item(state.get_machine(next)) == null, "missing committed identity has no Ferrite fallback")
	state._machines[next].v2_deposit_id = member.deposit_id + ":forged"
	state._extractor_claims_v2[member.deposit_id + ":forged"] = next
	_check(state.stored_output_item(state.get_machine(next)) == null, "forged committed identity rejected")
	state._extractor_claims_v2.erase(member.deposit_id + ":forged")
	state._machines[next].v2_deposit_id = member.deposit_id
	state._extractor_claims_v2[member.deposit_id] = next
	state.invalidate_resource_generation_v2()
	state.advance_production(1.0)
	_check(state.get_machine(next) == stored and state.stored_output_item(stored) == null,
		"unavailable authority pauses production without Ferrite fallback")
	_check(not state.collect_output(next, inventory, center, 160)
		and not state.recover_machine(next, inventory, center, 160)
		and state.get_machine(next) == stored, "retired context preserves unresolved stored output")
	state.configure_resource_generation_v2()
	_check(state.extractor_anchor_rejection_v2(ticket, EXTRACTOR, cell, 0) == "Unavailable anchor",
		"stale context rejected")
	_check(not state.recover_machine(next, inventory, center, 160)
		and state.stored_output_item(state.get_machine(next)) == null,
		"replacement context cannot revive committed old-context output")
	# Fresh-session cutover: no conversion or refund of interrupted session records.
	state = DescriptorFailure.new(42)
	inventory = InventoryState.new()
	inventory.add_item(EXTRACTOR, 2)
	next = 0
	_check(state.deploy_extractor_v2(ticket, EXTRACTOR, cell, 0, inventory, player, ground, 160) == 0
		and inventory.get_quantity(&"extractor") == 2 and state.get_machines().is_empty(),
		"stale confirmation consumes nothing")
	context = state.resource_generation_v2_context()
	ticket.token = context.token
	for turn in range(4):
		var rotated := state.deploy_extractor_v2(ticket, EXTRACTOR, cell, turn, inventory, player, ground, 160)
		_check(rotated > next and state.get_machine(rotated).turns == turn, "rotated exact-anchor deployment")
		state.advance_production(1.0)
		_check(state.get_machine(rotated).output == 1, "rotated production")
		_check(state.recover_machine(rotated, inventory, center, 160), "rotated recovery")
	_test_ordinary_resource(state, resource_type)
	# A corrupt/unsupported record cannot gain production from the packaged default.
	state._machines[99] = {"id": 99, "definition": restricted, "cell": carbite.anchor_cells.position,
		"turns": 0, "cycle_progress": 0.0, "output": 0, "v2_deposit_id": carbite.deposit_id, "v2_context_token": context.token}
	state._extractor_claims_v2[carbite.deposit_id] = 99
	state.advance_production(5.0)
	_check(state.get_machine(99).output == 0 and state.stored_output_item(state.get_machine(99)) == null,
		"unsupported resource inactivity")
	# Empty-record recovery must not erase someone else's claim.
	state._extractor_claims_v2[carbite.deposit_id] = 100
	_check(state.recover_machine(99, InventoryState.new(), Rules.bounds(carbite.anchor_cells).get_center(), 160)
		and state.extractor_occupant_v2(carbite.deposit_id) == 100,
		"empty recovery preserves foreign claim ownership")
	state._extractor_claims_v2.erase(carbite.deposit_id)
	state.invalidate_resource_generation_v2()
	_check(not state.extractor_target_v2(center, EXTRACTOR, 0).reason.is_empty(),
		"unavailable authority has no legacy target fallback")
	ground.free()


func _finish_presentation(presenter: ResourcePresenterV2, token: int) -> bool:
	for index in range(4096):
		var before: int = presenter.snapshot().sprites
		var result := presenter.step(token)
		_check(presenter.snapshot().sprites <= before + 1, "bounded sprite publication")
		if not result.ok:
			return false
		if result.get("done", false):
			return true
	return false


func _test_live_window_requests() -> void:
	var presenter := ResourcePresenterV2.new()
	var world := PlanetWorldState.new(42)
	_check(presenter.configure_world(world,
		[preload("res://scenes/world/resource_definitions/v2/ferrite.tres"),
		preload("res://scenes/world/resource_definitions/v2/cuprite.tres"),
		preload("res://scenes/world/resource_definitions/v2/carbite.tres")]).ok,
		"live window context")
	# Real 2048-unit chunks: initial 7x7, default retained 7x7 and maximum 13x13.
	for radius in [3, 6]:
		for center in [Vector2i(-4, -2), Vector2i.ZERO, Vector2i(4, 2)]:
			var area := Rect2(Vector2(center - Vector2i.ONE * radius) * WorldCoordinates.CHUNK_SIZE,
				Vector2.ONE * (2 * radius + 1) * WorldCoordinates.CHUNK_SIZE)
			var requested := presenter.request(area)
			_check(requested.ok, "real loaded terrain window admitted")
			_check(presenter._pages.size() <= ResourcePresenterV2.MAX_LIVE_PAGES,
				"live page plan remains bounded")
			for page: Rect2 in presenter._pages:
				_check(page.size == Vector2.ONE * ResourcePresenterV2.LIVE_PAGE_SIZE,
					"large window retains small descriptor queries")
	_check(not presenter.request(Rect2(Vector2.ZERO,
		Vector2.ONE * (ResourcePresenterV2.MAX_LIVE_AREA_AXIS + 1.0))).ok,
		"oversized live window still rejected")
	presenter.free()


func _test_presentation(resource_type: String) -> void:
	_resource_label = resource_type
	var world := PlanetWorldState.new(42)
	var context := world.resource_generation_v2_context()
	var layout := world.starting_resource_reservations_v2(context.token)
	var member: Dictionary = {}
	for location: Dictionary in layout.locations:
		if location.resource_type == resource_type:
			member = location.deposits[0]
	var before := layout.duplicate(true)
	var area := Rules.bounds(member.anchor_cells).grow(200.0)
	var chunk := WorldCoordinates.world_to_chunk(area.get_center())
	var loaded := {chunk: true}
	var presenter := ResourcePresenterV2.new()
	root.add_child(presenter)
	_check(presenter.configure_world(world, [preload("res://scenes/world/resource_definitions/v2/ferrite.tres"),
		preload("res://scenes/world/resource_definitions/v2/cuprite.tres"),
		preload("res://scenes/world/resource_definitions/v2/carbite.tres")]).ok,
		"world descriptor presentation adapter")
	presenter.set_loaded_chunks(loaded)
	var requested := presenter.request(area)
	_check(_finish_presentation(presenter, requested.token), "presentation completes")
	_check(presenter._sprites.has(member.deposit_id), "loaded resource visible")
	if presenter._sprites.has(member.deposit_id):
		var sprite: Sprite2D = presenter._sprites[member.deposit_id]
		_check(sprite.position == Rules.bounds(member.anchor_cells).get_center() + Vector2(0, 16)
			and sprite.scale == Vector2.ONE * 0.225, "approved presentation positioning and scale")
	var count: int = presenter.snapshot().sprites
	for index in range(3):
		_check(presenter.step(requested.token).done and presenter.snapshot().sprites == count, "no duplicate sprites")
	var old_token: int = requested.token
	var retained: Sprite2D = presenter._sprites.get(member.deposit_id)
	requested = presenter.request(area)
	_check(presenter._sprites.get(member.deposit_id) == retained, "streaming retains valid sprites")
	_check(presenter.step(old_token).get("stale", false), "stale request cannot publish")
	_check(_finish_presentation(presenter, requested.token) and presenter.snapshot().sprites == count,
		"revisit retains stable deposit identities")
	presenter.set_loaded_chunks({})
	_check(presenter.snapshot().sprites == 0, "streaming unload retires sprites")
	requested = presenter.request(area)
	_check(_finish_presentation(presenter, requested.token) and presenter.snapshot().sprites == 0,
		"unloaded terrain publishes no sprites")
	presenter.set_loaded_chunks(loaded)
	requested = presenter.request(area)
	_check(_finish_presentation(presenter, requested.token) and presenter.snapshot().sprites == count,
		"terrain reload restores presentation")
	_check(world.starting_resource_reservations_v2(context.token) == before, "presentation preserves generation")
	world.invalidate_resource_generation_v2()
	_check(not presenter.step(requested.token).ok and presenter.snapshot().sprites == 0,
		"retired authority clears presentation")
	presenter.free()


func _test_ordinary_resource(state: PlanetWorldState, resource_type: String) -> void:
	var context := state.resource_generation_v2_context()
	var found := false
	# Finite corpus away from starting reservations; no density/performance probe.
	for y in range(8, 16):
		for x in range(8, 16):
			if found:
				break
			var queried := state.query_resource_descriptors_v2(
				Rect2(Vector2(x, y) * 1536.0, Vector2.ONE * 1536.0), context.token)
			_check(queried.ok, "ordinary query available")
			if not queried.ok:
				return
			for member: Dictionary in queried.deposits:
				if member.resource_type != resource_type or not member.deposit_id.begins_with("resource:ordinary-v2-1:"):
					continue
				var resolved := state.resource_descriptor_v2_by_id(member.deposit_id, context.token)
				_check(resolved.ok and resolved.descriptor == member,
					"ordinary resource resolves through world authority")
				var ticket := {"token": context.token, "deposit_id": member.deposit_id,
					"resource_type": member.resource_type, "anchor_cells": member.anchor_cells}
				for turn in range(4):
					_check(state.extractor_anchor_rejection_v2(ticket, EXTRACTOR,
						member.anchor_cells.position, turn).is_empty(), "ordinary exact rotated anchor")
				# A committed-record fixture exercises the same resolver for ordinary IDs.
				var identity: int = state._next_machine_id
				state._machines[identity] = {"id": identity, "definition": EXTRACTOR,
					"cell": member.anchor_cells.position, "turns": 0, "cycle_progress": 0.0,
					"output": 0, "v2_deposit_id": member.deposit_id, "v2_context_token": context.token}
				state._extractor_claims_v2[member.deposit_id] = identity
				_check(state.stored_output_item(state.get_machine(identity)) == load("res://inventory/%s_ore.tres" % resource_type),
					"ordinary canonical resource output")
				state.advance_production(1.0)
				var inventory := InventoryState.new()
				_check(state.recover_machine(identity, inventory,
					Rules.bounds(member.anchor_cells).get_center(), 160)
					and inventory.get_quantity(StringName(resource_type + "_ore")) == 1, "ordinary resource production and recovery")
				found = true
				break
	_check(found, "ordinary resource fixture found")


func _test_discovery() -> void:
	var seed_world := PlanetWorldState.new(42)
	var context := seed_world.resource_generation_v2_context()
	var layout := seed_world.starting_resource_reservations_v2(context.token)
	var ferrite_count := 0
	for location: Dictionary in layout.locations:
		if location.resource_type != "ferrite":
			continue
		for member: Dictionary in location.deposits:
			ferrite_count += 1
			var progression := PlaythroughState.new()
			progression.world_seed = 42
			root.add_child(progression)
			var own := progression.planet.resource_generation_v2_context()
			_check(not progression.discover_ferrite(member.deposit_id, context.token), "foreign discovery context rejected")
			_check(not progression.discover_ferrite("crash_site_ferrite", own.token), "retired authored discovery identity rejected")
			_check(not progression.discover_ferrite(member.deposit_id + ":forged", own.token), "forged discovery identity rejected")
			_check(progression.discover_ferrite(member.deposit_id, own.token)
				and progression.ferrite_discovered, "genuine starting V2 Ferrite discovery")
			_check(not progression.discover_ferrite(member.deposit_id, own.token), "discovery is one shot")
			progression.free()
	_check(ferrite_count == 3, "three starting Ferrite discovery members")


func _test_exterior_revisit() -> void:
	var progression := PlaythroughState.new()
	progression.world_seed = 42
	root.add_child(progression)
	var exterior = preload("res://scenes/world/planet_exterior.tscn").instantiate()
	exterior.process_mode = Node.PROCESS_MODE_DISABLED
	root.add_child(exterior)
	var prepared: Dictionary = await exterior.prepare_initial_neighborhood(progression.planet)
	_check(exterior.preparation_is_ready(prepared), "three-resource exterior startup readiness")
	var presenter: ResourcePresenterV2 = exterior._resource_presenter
	var sprites: Dictionary = presenter._sprites.duplicate()
	var interactions := 0
	for child in exterior.get_node("GroundObjects").get_children():
		if child.get_script() == preload("res://scenes/interaction/ferrite_inspection.gd"):
			interactions += 1
	_check(interactions == 3, "three genuine Ferrite interactions without authored duplicate")
	root.remove_child(exterior)
	_check(not exterior.preparation_is_ready(prepared), "detached startup receipt rejected")
	root.add_child(exterior)
	var player := CharacterBody2D.new()
	player.position = exterior.get_node("Spawns/FromShip").position
	exterior.add_child(player)
	var arrived: Dictionary = await exterior.prepare_for_arrival(player, progression.planet)
	_check(exterior.arrival_is_ready(arrived) and exterior._resource_presenter == presenter,
		"cached exterior arrival retains shared presenter")
	for identity in sprites:
		if presenter._sprites.has(identity):
			_check(presenter._sprites[identity] == sprites[identity], "revisit reuses resource sprites")
	exterior.cancel_arrival_preparation()
	_check(not exterior.arrival_is_ready(arrived), "cancelled resource receipt rejected")
	exterior.free()
	progression.free()
