extends SceneTree
## Authored behavioral assertions; NOT authorized or dispatched by a local runner.

const Presenter = preload("res://scenes/world/resource_presenter_v2.gd")
const Descriptors = preload("res://scenes/world/resource_generation_descriptors.gd")
const CUPRITE = preload("res://scenes/world/resource_definitions/v2/cuprite.tres")
const EXTERIOR = preload("res://scenes/world/planet_exterior.tscn")
var _failures: int = 0


class FixtureWorld:
	extends "res://scenes/world/planet_world_state.gd"
	var queries: int = 0
	var members: Array = []

	func query_resource_descriptors_v2(_area: Rect2, token: RefCounted) -> Dictionary:
		var context := resource_generation_v2_context()
		if not context.ok or context.token != token:
			return {"ok": false}
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
	var world := FixtureWorld.new()
	var made := Descriptors.create_location("starting-v2-2", world.seed_value,
		Vector2i.ZERO, 0, &"cuprite", [Rect2i(-2, -2, 4, 4)])
	world.members = made.location.deposits
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
	_check(exterior._resources_done and presenter.snapshot().sprites == 1,
		"initial presentation completes")
	var registrations: Dictionary = presenter._registrations.duplicate(true)
	var sprite: Sprite2D = presenter._sprites.values()[0]
	var texture: Texture2D = presenter._textures.values()[0]
	var query_count: int = world.queries
	for visit in range(3):
		var old_token: int = exterior._resource_token
		root.remove_child(exterior)
		_check(presenter.step(old_token).get("stale", false), "detachment retires old token")
		root.add_child(exterior)
		exterior._initialize_world(world)
		_check(exterior._resources_done, "same-context completed visit reuses readiness work")
		exterior._service_resources()
		_check(world.queries == query_count, "reattachment performs no repeated queries")
		_check(presenter._registrations == registrations and presenter._sprites.values()[0] == sprite
			and presenter._textures.values()[0] == texture, "registrations sprite and texture retained")
		_check(not exterior.arrival_is_ready({"ok": true, "generation": -1}),
			"reused presentation cannot authorize an old arrival receipt")

	# Explicit cancellation invalidates completion, even if coverage is unchanged.
	var completed_token: int = exterior._resource_token
	exterior.cancel_arrival_preparation()
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

	# Streaming still retires unloaded visuals and recreates them after reload.
	exterior._chunks.erase(Vector2i.ZERO)
	exterior._chunks[Vector2i(50, 50)] = chunk
	_drain(exterior)
	_check(presenter.snapshot().sprites == 0, "streaming after reattachment retires visuals")
	exterior._chunks.erase(Vector2i(50, 50))
	exterior._chunks[Vector2i.ZERO] = chunk
	_drain(exterior)
	_check(presenter.snapshot().sprites == 1, "streaming reload restores visible sprite")

	var replacement := FixtureWorld.new()
	var replacement_token: int = exterior._resource_token
	_check(presenter.configure_world(replacement, [CUPRITE]).ok,
		"new world instance reinitializes even at identical seed")
	_check(not presenter.is_complete(replacement_token) and presenter.snapshot().sprites == 0
		and presenter.snapshot().textures == 0, "world replacement clears unrelated caches")
	_check(not presenter.configure_world(replacement, []).ok, "invalid configuration fails closed")
	_check(presenter._world == null and presenter._registrations.is_empty(), "invalid context disposed")
	var incompatible := CUPRITE.duplicate() as WorldResourceDefinition
	incompatible.presentation_catalog = "res://missing.json"
	_check(not presenter.configure_world(replacement, [incompatible]).ok,
		"changed catalog is reinitialized and admitted fail closed")
	_check(presenter.configure_world(world, [CUPRITE]).ok, "valid context restored")
	world._resource_v2.invalidate("fixture retirement")
	_check(not presenter.configure_world(world, [CUPRITE]).ok and presenter._world == null,
		"retired generation context cannot be reused")
	_check(world.configure_resource_generation_v2().ok, "same world obtains a replacement context")
	_check(presenter.configure_world(world, [CUPRITE]).ok, "replacement context configured")
	world._resource_v2._token = RefCounted.new()
	var renewed := presenter.configure_world(world, [CUPRITE])
	_check(renewed.ok and not renewed.reused, "new context token reinitializes the same world")
	_check(presenter.configure_world(replacement, [CUPRITE]).ok, "retirement fixture configured")
	presenter.dispose()
	_check(presenter._world == null and presenter._catalogs.is_empty()
		and presenter._loaded_chunks.is_empty() and not presenter.is_complete(presenter.snapshot().token),
		"explicit disposal clears all reusable state")
	# Refill before freeing the cached exterior to verify automatic actual retirement.
	exterior._state = replacement
	exterior._initialize_world(replacement)
	replacement.members = made.location.deposits
	_drain(exterior)
	var retained_sprite: WeakRef = weakref(presenter._sprites.values()[0])
	root.remove_child(exterior)
	exterior.free()
	_check(retained_sprite.get_ref() == null, "actual retirement frees retained child sprites")
	print("Cuprite presentation lifecycle failures: %d" % _failures)
	quit(0 if _failures == 0 else 1)
