extends SceneTree
## Authored behavioral assertions; NOT authorized or dispatched by a local runner.

const Presenter = preload("res://scenes/world/resource_presenter_v2.gd")
const Descriptors = preload("res://scenes/world/resource_generation_descriptors.gd")
const FERRITE = preload("res://scenes/world/resource_definitions/v2/ferrite.tres")
const CARBITE = preload("res://scenes/world/resource_definitions/v2/carbite.tres")
const CUPRITE = preload("res://scenes/world/resource_definitions/v2/cuprite.tres")
const EXTERIOR = preload("res://scenes/world/planet_exterior.tscn")
var _failures: int = 0


class FixtureWorld:
	extends "res://scenes/world/planet_world_state.gd"
	var fail_query: bool = false
	var queries: int = 0
	var members: Array = []

	func query_resource_descriptors_v2(_area: Rect2, token: RefCounted) -> Dictionary:
		var context := resource_generation_v2_context()
		if not context.ok or context.token != token:
			return {"ok": false}
		if fail_query:
			return {"ok": false, "error": "fixture presentation query failure"}
		queries += 1
		return {"ok": true, "deposits": members.duplicate(true)}


func _check(condition: bool, label: String) -> void:
	if not condition:
		_failures += 1
		printerr("FAIL: " + label)


func _initialize() -> void:
	call_deferred("_run")


func _drain(exterior: PlanetExterior) -> void:
	for index in range(1000):
		exterior._service_resources()
		if exterior._resources_done or not exterior._terrain_failure.is_empty():
			return
	_check(false, "finite fixture work budget")


func _run() -> void:
	_test_highlight_budget()
	var world := FixtureWorld.new()
	var made := Descriptors.create_location("starting-v2-2", world.seed_value,
		Vector2i.ZERO, 0, &"cuprite", [Rect2i(-2, -2, 4, 4)])
	var carbite := Descriptors.create_location("starting-v2-2", world.seed_value,
		Vector2i.ZERO, 1, &"carbite", [Rect2i(8, 8, 4, 4)])
	var ferrite := Descriptors.create_location("starting-v2-2", world.seed_value,
		Vector2i.ZERO, 2, &"ferrite", [Rect2i(16, 16, 4, 4)])
	world.members = made.location.deposits + carbite.location.deposits + ferrite.location.deposits
	var exterior := EXTERIOR.instantiate() as PlanetExterior
	root.add_child(exterior)
	exterior.set_process(false)
	exterior._state = world
	exterior._initialize_world(world)
	var chunk := TerrainChunk.new()
	exterior.add_child(chunk)
	exterior._chunks[Vector2i.ZERO] = chunk
	# Exercise the actual initial presentation service, without generating terrain.
	_drain(exterior)
	var presenter: ResourcePresenterV2 = exterior._resource_presenter
	_check(exterior._resources_done and presenter.snapshot().sprites == 3,
		"initial presentation completes")
	_test_highlights(exterior, world)
	var registrations: Dictionary = presenter._registrations.duplicate(true)
	var sprites: Dictionary = presenter._sprites.duplicate()
	var textures: Dictionary = presenter._textures.duplicate()
	var query_count: int = world.queries
	_check_completed_steps(presenter, exterior._resource_token)
	_test_completed_invalidation(world.members)
	for visit in range(3):
		var old_token: int = exterior._resource_token
		root.remove_child(exterior)
		_check(not presenter.highlight_page(old_token, 0).ok, "detachment rejects highlight projection")
		_check(presenter.step(old_token).get("stale", false), "detachment retires old token")
		_check(presenter.step(presenter.snapshot().token).get("stale", false), "detached activity guard precedes terminal completion")
		root.add_child(exterior)
		exterior._initialize_world(world)
		_check(exterior._resources_done, "same-context completed visit reuses readiness work")
		for repeat in range(4):
			exterior._service_resources()
			_check(exterior._resources_done and presenter.is_complete(exterior._resource_token),
				"unchanged coverage service preserves completed readiness")
		_test_highlights(exterior, world)
		_check_completed_steps(presenter, exterior._resource_token)
		_check(world.queries == query_count, "reattachment performs no repeated queries")
		_check(presenter._registrations == registrations and presenter._sprites == sprites
			and presenter._textures == textures, "registrations sprite and texture retained")
		_check(not exterior.arrival_is_ready({"ok": true, "generation": -1}),
			"reused presentation cannot authorize an old arrival receipt")

	# Explicit cancellation invalidates completion, even if coverage is unchanged.
	var completed_token: int = exterior._resource_token
	exterior.cancel_arrival_preparation()
	_check(presenter.step(presenter.snapshot().token).get("stale", false), "cancelled activity cannot return completed work")
	_check(not presenter.is_complete(completed_token), "explicit cancellation rejects completion")
	exterior._initialize_world(world)
	_check(not exterior._resources_done, "cancelled visit requires presentation work")
	exterior._service_resources()
	var interrupted_token: int = exterior._resource_token
	root.remove_child(exterior)
	root.add_child(exterior)
	exterior._initialize_world(world)
	_check(not exterior._resources_done and presenter.step(interrupted_token).get("stale", false),
		"interrupted preparation cannot become ready on reattachment")
	_drain(exterior)
	_check(exterior._resources_done and world.queries > query_count, "cancelled work restarts safely")

	_check(not presenter.highlight_page(completed_token, 0).ok, "cancelled highlight token rejected")
	# Streaming still retires unloaded visuals and recreates them after reload.
	exterior._chunks.erase(Vector2i.ZERO)
	exterior._chunks[Vector2i(50, 50)] = chunk
	var prior_request: int = exterior._resource_token
	exterior._service_resources()
	_check(not exterior._resources_done and not presenter.is_complete(exterior._resource_token)
		and presenter.step(prior_request).get("stale", false), "changed coverage starts genuinely incomplete request")
	_drain(exterior)
	_drain_highlights(exterior)
	_check(exterior._highlight_nodes.is_empty(), "streaming retires highlight nodes")
	_check(presenter.snapshot().sprites == 0, "streaming after reattachment retires visuals")
	exterior._chunks.erase(Vector2i(50, 50))
	exterior._chunks[Vector2i.ZERO] = chunk
	_drain(exterior)
	_drain_highlights(exterior)
	_check(exterior._highlight_nodes.size() == 3, "streaming restores all resource highlights")
	_check(presenter.snapshot().sprites == 3, "streaming reload restores visible sprite")

	var replacement := FixtureWorld.new()
	var replacement_token: int = exterior._resource_token
	_check(presenter.configure_world(replacement, [CUPRITE, CARBITE]).ok,
		"new world instance reinitializes even at identical seed")
	_check(not presenter.is_complete(replacement_token) and presenter.snapshot().sprites == 0
		and presenter.snapshot().textures == 0, "world replacement clears unrelated caches")
	_check(not presenter.configure_world(replacement, []).ok, "invalid configuration fails closed")
	_check(presenter._world == null and presenter._registrations.is_empty(), "invalid context disposed")
	var incompatible := CUPRITE.duplicate() as WorldResourceDefinition
	incompatible.presentation_catalog = "res://missing.json"
	_check(not presenter.configure_world(replacement, [incompatible]).ok,
		"changed catalog is reinitialized and admitted fail closed")
	_check(presenter.configure_world(world, [CUPRITE, CARBITE]).ok, "valid context restored")
	world._resource_v2.invalidate("fixture retirement")
	_check(not presenter.configure_world(world, [CUPRITE, CARBITE]).ok and presenter._world == null,
		"retired generation context cannot be reused")
	_check(world.configure_resource_generation_v2().ok, "same world obtains a replacement context")
	_check(presenter.configure_world(world, [CUPRITE, CARBITE]).ok, "replacement context configured")
	world._resource_v2._token = RefCounted.new()
	var renewed := presenter.configure_world(world, [CUPRITE, CARBITE])
	_check(renewed.ok and not renewed.reused, "new context token reinitializes the same world")
	_check(presenter.configure_world(replacement, [CUPRITE, CARBITE]).ok, "retirement fixture configured")
	presenter.dispose()
	_check(presenter.step(presenter.snapshot().token).get("stale", false), "disposed presenter cannot return completed work")
	_check(presenter._world == null and presenter._catalogs.is_empty()
		and presenter._loaded_chunks.is_empty() and not presenter.is_complete(presenter.snapshot().token),
		"explicit disposal clears all reusable state")
	# Refill before freeing the cached exterior to verify automatic actual retirement.
	exterior._state = replacement
	exterior._initialize_world(replacement)
	replacement.members = world.members.duplicate(true)
	_drain(exterior)
	var retained_sprites: Array[WeakRef] = []
	for sprite: Sprite2D in presenter._sprites.values():
		retained_sprites.append(weakref(sprite))
	root.remove_child(exterior)
	exterior.free()
	for retained_sprite: WeakRef in retained_sprites:
		_check(retained_sprite.get_ref() == null, "actual retirement frees retained child sprites")
	print("Cuprite/Carbite presentation lifecycle failures: %d" % _failures)
	quit(0 if _failures == 0 else 1)


func _check_completed_steps(presenter: ResourcePresenterV2, token: int) -> void:
	var before := presenter.snapshot()
	var registrations: Dictionary = presenter._registrations.duplicate(true)
	var sprites: Dictionary = presenter._sprites.duplicate()
	var textures: Dictionary = presenter._textures.duplicate()
	var cursor := [presenter._ordered, presenter._index, presenter._ids.duplicate()]
	for repeat in range(4):
		var result := presenter.step(token)
		_check(result.ok and result.get("done", false), "repeated completed step remains done")
		_check(presenter.snapshot() == before and presenter._registrations == registrations
			and presenter._sprites == sprites and presenter._textures == textures
			and [presenter._ordered, presenter._index, presenter._ids] == cursor,
			"terminal completion does not replay registrations or mutate published state")


func _test_completed_invalidation(members: Array) -> void:
	for failure in ["retired", "replaced", "failed"]:
		var world := FixtureWorld.new()
		world.members = members.duplicate(true)
		var presenter := Presenter.new()
		root.add_child(presenter)
		_check(presenter.configure_world(world, [FERRITE, CUPRITE, CARBITE]).ok, "three-resource completion fixture")
		presenter.set_loaded_chunks({Vector2i.ZERO: true})
		var requested := presenter.request(Rect2(-256, -256, 1536, 1536))
		var done := false
		for index in range(1000):
			var result := presenter.step(requested.token)
			if not result.ok or result.get("done", false):
				done = result.ok and result.get("done", false)
				break
		_check(done, "invalidation begins with genuinely completed presentation")
		if not done:
			presenter.free()
			continue
		_check_completed_steps(presenter, requested.token)
		if failure == "failed":
			world.fail_query = true
			var prior: int = requested.token
			requested = presenter.request(Rect2(-256, -256, 1536, 1536))
			_check(not presenter.is_complete(requested.token) and presenter.step(prior).get("stale", false),
				"same-area new request invalidates completed work")
		else:
			world.invalidate_resource_generation_v2()
			if failure == "replaced":
				_check(world.configure_resource_generation_v2().ok, "replacement generation context ready")
		_check(not presenter.highlight_page(requested.token, 0).ok, "retired context rejects highlight projection")
		var rejected := presenter.step(requested.token)
		_check(not rejected.ok and presenter.snapshot().sprites == 0
			and not presenter.is_complete(presenter.snapshot().token),
			"completed presentation still fails closed after " + failure)
		presenter.free()


func _drain_highlights(exterior: PlanetExterior) -> void:
	for index in range(1000):
		exterior._flush_highlights()
		if exterior._highlight_ready:
			return
	_check(false, "finite highlight fixture budget")


func _test_highlights(exterior: PlanetExterior, world: FixtureWorld) -> void:
	var presenter: ResourcePresenterV2 = exterior._resource_presenter
	var token: int = exterior._resource_token
	var queries: int = world.queries
	_drain_highlights(exterior)
	_check(exterior._highlight_nodes.size() == 3 and exterior._highlight_groups.size() == 3,
		"three resource highlights and crossing anchor")
	var nodes: Dictionary = exterior._highlight_nodes.duplicate()
	var definition := preload("res://inventory/extractor.tres") as MachineDefinition
	for repeat in range(3):
		exterior.set_construction_definition(definition)
		exterior._flush_highlights()
		_check(exterior._highlights.visible, "selection reveals retained highlights")
		exterior.set_construction_definition(null)
		_check(not exterior._highlights.visible, "deselection hides without destruction")
		exterior.set_construction_definition(definition)
		exterior._flush_highlights()
		_check(exterior._highlight_nodes == nodes, "reselection retains highlight node identity")
	_check(world.queries == queries, "highlight selection performs no generation")
	var page := presenter.highlight_page(token, 0)
	_check(page.ok and page.entries.size() == 3, "published projection complete")
	page.entries[0].anchor_cells = Rect2i()
	page.entries[0].deposit_id = "forged"
	var fresh := presenter.highlight_page(token, 0)
	_check(fresh.entries[0].deposit_id != "forged" and fresh.entries[0].anchor_cells.size == Vector2i(4, 4),
		"highlight projection returns independent data")
	for entry: Dictionary in fresh.entries:
		_check(entry.keys().size() == 4 and not entry.has("token") and not entry.has("ticket"),
			"visual projection grants no placement ticket")
	# Art can still overlap the loaded chunk while the logical anchor is outside it.
	var identity: String = fresh.entries[0].deposit_id
	var original: Dictionary = presenter._registrations[identity].duplicate(true)
	presenter._registrations[identity].logical_bounds = Rect2(-4096, -4096, 128, 128)
	_check(presenter.highlight_page(token, 0).entries.size() == 2, "painted overhang alone is not an anchor")
	presenter._registrations[identity] = original
	var incompatible := definition.duplicate() as MachineDefinition
	incompatible.compatible_resources = [&"cuprite"]
	exterior.set_construction_definition(incompatible)
	_check(exterior._highlight_groups["cuprite"].visible and not exterior._highlight_groups["ferrite"].visible
		and not exterior._highlight_groups["carbite"].visible, "compatibility changes group visibility")
	exterior.set_construction_definition(null)


func _test_highlight_budget() -> void:
	var world := FixtureWorld.new()
	for index in range(40):
		var made := Descriptors.create_location("starting-v2-2", world.seed_value,
			Vector2i.ZERO, index, &"ferrite", [Rect2i((index % 8) * 6, (index / 8) * 6, 4, 4)])
		world.members.append_array(made.location.deposits)
	var exterior := EXTERIOR.instantiate() as PlanetExterior
	root.add_child(exterior)
	exterior.set_process(false)
	exterior._state = world
	exterior._initialize_world(world)
	var chunk := TerrainChunk.new()
	exterior.add_child(chunk)
	exterior._chunks[Vector2i.ZERO] = chunk
	_drain(exterior)
	var queries: int = world.queries
	var previous := 0
	for index in range(20):
		exterior._flush_highlights()
		var count: int = exterior._highlight_nodes.size()
		_check(count - previous <= exterior.HIGHLIGHT_BUDGET, "highlight reconciliation budget")
		previous = count
		if exterior._highlight_ready:
			break
	_check(exterior._highlight_ready and previous == 40 and world.queries == queries,
		"bounded reconciliation includes every published anchor")
	# A disjoint published set retires old nodes before allocating replacements.
	var replacements: Array = []
	for index in range(40):
		var made := Descriptors.create_location("starting-v2-2", world.seed_value,
			Vector2i.ZERO, index + 40, &"cuprite", [Rect2i((index % 8) * 6, (index / 8) * 6, 4, 4)])
		replacements.append_array(made.location.deposits)
	world.members = replacements
	exterior._resource_chunks.clear()
	_drain(exterior)
	previous = exterior._highlight_nodes.size()
	for index in range(30):
		exterior._flush_highlights()
		var count: int = exterior._highlight_nodes.size()
		_check(absi(count - previous) <= exterior.HIGHLIGHT_BUDGET and count <= 40,
			"streaming additions and retirement remain bounded without accumulation")
		previous = count
		if exterior._highlight_ready:
			break
	_check(exterior._highlight_ready and previous == 40, "replacement set eventually complete")
	exterior._resource_presenter.cancel(true)
	exterior._flush_highlights()
	_check(not exterior._highlights.visible and not exterior._highlight_ready,
		"retained visuals after cancellation cannot highlight")
	exterior.free()
