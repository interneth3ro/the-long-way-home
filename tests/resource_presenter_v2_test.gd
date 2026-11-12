extends SceneTree
## Authored behavior assertions ONLY; not added to any runner or executed.

const Presenter = preload("res://scenes/world/resource_presenter_v2.gd")
const Catalog = preload("res://scenes/world/resource_presentation_catalog.gd")
const Descriptors = preload("res://scenes/world/resource_generation_descriptors.gd")
const Context = preload("res://scenes/world/resource_generation_crash_site.gd")
const CUPRITE = preload("res://scenes/world/resource_definitions/v2/cuprite.tres")
const FERRITE = preload("res://scenes/world/resource_definitions/v2/ferrite.tres")
const CARBITE = preload("res://scenes/world/resource_definitions/v2/carbite.tres")
var _failures: int = 0


class Fixture:
	extends "res://scenes/world/ordinary_resource_generator.gd"
	var locations: Array = []
	var reverse: bool = false
	var context_policy: String = "ordinary-v2-1"
	var owner_count: int = 2

	func identity_policy() -> String:
		return context_policy

	func query_owners(_area: Rect2) -> Dictionary:
		var owners: Array[Vector2i] = []
		for x in range(owner_count):
			owners.append(Vector2i(x, 0))
		if reverse:
			owners.reverse()
		return {"ok": true, "owners": owners}

	func region(_owner: Vector2i) -> Dictionary:
		return {"ok": true, "locations": locations.duplicate(true)}


func _check(condition: bool, label: String) -> void:
	if not condition:
		_failures += 1
		printerr("FAIL: " + label)


func _initialize() -> void:
	call_deferred("_run")


func _finish(presenter: ResourcePresenterV2, token: int) -> Dictionary:
	for index in range(1000):
		var before: int = presenter.snapshot().sprites
		var result := presenter.step(token)
		_check(presenter.snapshot().sprites <= before + 1, "one sprite maximum per step")
		if not result.ok or result.get("done", false):
			return result
	return {"ok": false, "error": "finite assertion work budget exhausted"}


func _run() -> void:
	var catalog := Catalog.read_catalog(CUPRITE.presentation_catalog, "cuprite")
	_check(catalog.ok, "Cuprite resource-type catalog selection")
	if not catalog.ok:
		quit(1)
		return
	var made := Descriptors.create_location("ordinary-v2-1", 42, Vector2i.ZERO, 0,
		&"cuprite", [Rect2i(-2, -2, 4, 4), Rect2i(10, -2, 4, 4)])
	var registration := Catalog.registration(made.location.deposits[0], CUPRITE.presentation_catalog, catalog)
	_check(registration.position == Vector2(0, 16), "anchor center plus approved offset")
	_check(registration.logical_bounds == Rect2(-64, -64, 128, 128), "4x4 independent logical anchor")
	_check(registration.illustrated_envelope.size.is_equal_approx(Vector2(345.6, 230.4)), "full canvas envelope")
	_check(registration.illustrated_envelope != registration.logical_bounds, "logical and visual geometry separate")
	_check(registration == Catalog.registration(made.location.deposits[0], CUPRITE.presentation_catalog, catalog), "stable descriptor registration")
	var invalid := made.location.deposits[0].duplicate(true)
	invalid.presentation = {"variant_id": "unapproved"}
	_check(not Catalog.registration(invalid, CUPRITE.presentation_catalog, catalog).ok, "missing variant fails admission")
	invalid.presentation = {"catalog_ref": "res://wrong.json"}
	_check(not Catalog.registration(invalid, CUPRITE.presentation_catalog, catalog).ok, "catalog mismatch fails admission")
	_check(not Catalog.read_catalog(FERRITE.presentation_catalog, "ferrite").ok, "no Ferrite artwork fallback")
	_check(not Catalog.read_catalog(CARBITE.presentation_catalog, "carbite").ok, "no Carbite artwork fallback")
	_check(not Catalog.read_catalog("res://missing.json", "cuprite").ok, "missing artwork catalog fails admission")
	var bad_entry := {"id": "bad", "artwork": registration.artwork,
		"sha256": registration.sha256, "size": [1536, 1024], "scale": -1, "offset": [0, 16]}
	_check(not Catalog.admit_entry(bad_entry).ok, "invalid scale rejected")
	bad_entry.scale = 0.225
	bad_entry.size = [4096, 1024]
	_check(not Catalog.admit_entry(bad_entry).ok, "oversized pixel dimensions rejected")
	var fixture := Fixture.new(42, [FERRITE, CARBITE, CUPRITE], [])
	fixture.locations = [made.location]
	var presenter := Presenter.new()
	root.add_child(presenter)
	_check(presenter.configure(fixture, 42, [CUPRITE]).ok, "explicit presentation subset")
	var requested := presenter.request(Rect2(-1000, -1000, 2000, 2000))
	var old_token: int = requested.token
	_check(_finish(presenter, old_token).ok, "texture admission and incremental commit")
	_check(presenter.snapshot().sprites == 2, "overlapping owner queries deduplicate stable IDs")
	var texture: Texture2D = presenter._textures.values()[0]
	presenter._textures.clear()
	for index in range(Presenter.TEXTURE_LIMIT):
		presenter._textures["fixture_%d" % index] = texture
	_check(presenter._texture(registration).ok and presenter.snapshot().textures == Presenter.TEXTURE_LIMIT,
		"texture cache eviction retains fixed cap")
	_check(not presenter._textures.has("fixture_0"), "oldest texture insertion evicted")
	var first := presenter._registrations.duplicate(true)
	fixture.reverse = true
	requested = presenter.request(Rect2(-1000, -1000, 2000, 2000))
	_check(presenter.step(old_token).get("stale", false), "old token cannot publish")
	_check(_finish(presenter, requested.token).ok and first == presenter._registrations, "reverse query order independence")
	presenter.cancel()
	_check(presenter.snapshot().sprites == 0 and presenter.snapshot().descriptors == 0, "cancel removes visuals and descriptors")
	_check(presenter.step(requested.token).get("stale", false), "cancelled request stays stale")
	requested = presenter.request(Rect2(10000, 10000, 128, 128))
	_check(_finish(presenter, requested.token).ok and presenter.snapshot().sprites == 0, "movement retires off-area visuals")
	_check(not presenter.request(Rect2(0, 0, 1000000, 1000000)).ok, "unbounded area rejected")
	fixture.owner_count = 65
	_check(not presenter.request(Rect2(0, 0, 128, 128)).ok, "owner budget rejected before generation")
	fixture.owner_count = 2
	requested = presenter.request(Rect2(-1000, -1000, 2000, 2000))
	fixture.context_policy = "changed-policy"
	_check(not presenter.step(requested.token).ok and presenter.snapshot().sprites == 0, "policy replacement clears old visuals")
	fixture.context_policy = "ordinary-v2-1"
	_check(presenter.configure(fixture, 79, [CUPRITE]).ok, "seed context replacement")
	requested = presenter.request(Rect2(-1000, -1000, 2000, 2000))
	_check(not _finish(presenter, requested.token).ok, "wrong seed descriptors fail closed")
	_check(presenter.snapshot().textures == 0, "failed context clears texture cache")
	_check(presenter.configure(fixture, 42, [CUPRITE]).ok, "restore context for rejection cases")
	fixture.locations = []
	for index in range(12):
		fixture.locations.append(made.location)
	requested = presenter.request(Rect2(-1000, -1000, 2000, 2000))
	_check(not presenter.step(requested.token).ok, "oversized region rejected before admission")
	fixture.locations = [made.location.duplicate(true)]
	fixture.locations[0].deposits[0].anchor_cells = Rect2i(0, 0, 3, 4)
	_check(presenter.configure(fixture, 42, [CUPRITE]).ok, "restore malformed location fixture")
	requested = presenter.request(Rect2(-1000, -1000, 2000, 2000))
	_check(not _finish(presenter, requested.token).ok, "malformed complete location rejected")
	_check(presenter.snapshot().sprites == 0, "admission failure publishes no visuals")
	_check(presenter.configure(fixture, 42, [CUPRITE]).ok, "restore context for texture rejection")
	var bad_texture := registration.duplicate(true)
	bad_texture.sha256 = "0".repeat(64)
	_check(not presenter._texture(bad_texture).ok, "wrong artwork hash rejected before sprite creation")
	_check(not presenter.configure(fixture, 42, [FERRITE]).ok, "unapproved resource cannot activate visually")
	var starting := StartingResourceGenerator.new(26026, [FERRITE, CARBITE, CUPRITE],
		Context.protected_bounds(), Context.SHIP_REFERENCE)
	_check(starting.is_ready(), "inspection seed prepares complete reservations")
	if starting.is_ready():
		var before := starting.reservations()
		_check(presenter.configure(starting, 26026, [CUPRITE]).ok, "Cuprite-only presentation retains generator context")
		requested = presenter.request(Rect2(-3000, -3000, 6000, 6000))
		_check(_finish(presenter, requested.token).ok, "starting generator presentation")
		_check(starting.reservations() == before, "all seven inactive and active reservations preserved")
		for visual: Dictionary in presenter._registrations.values():
			_check(visual.resource_id == "cuprite", "Ferrite and Carbite remain visually inactive")
	_check(presenter.snapshot().descriptors <= Presenter.MAX_DESCRIPTORS, "bounded descriptor cache")
	_check(presenter.snapshot().textures <= Presenter.TEXTURE_LIMIT, "bounded texture cache")
	presenter.dispose()
	_check(presenter.get_child_count() == 0 and presenter.snapshot().textures == 0, "complete disposal")
	presenter.free()
	print("Resource presenter v2 assertions: failures=%d" % _failures)
	quit(0 if _failures == 0 else 1)
