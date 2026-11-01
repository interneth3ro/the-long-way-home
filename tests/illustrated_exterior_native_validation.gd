extends SceneTree

# Proposed PR #104 Phase 2 only; separate authorization after cold import PASS.
# One real 25-chunk preparation, bounded direct replacements, then a one-chunk
# legacy comparison. No Main, player controller, input automation or benchmark.
const EXTERIOR := "res://scenes/world/planet_exterior.tscn"
var failures: int = 0


class InvalidMaterialGenerator extends PlanetGenerator:
	func sample_ground_material(_tile: Vector2i) -> int:
		return 5


func _initialize() -> void:
	call_deferred("_validate")


func _check(condition: bool, message: String) -> bool:
	if not condition:
		failures += 1
		print("FAIL: " + message)
	return condition


func _finish() -> void:
	print("Illustrated exterior validation failures: %d" % failures)
	quit(0 if failures == 0 else 1)


func _attach(packed: PackedScene, renderer: int) -> PlanetExterior:
	var exterior := packed.instantiate() as PlanetExterior
	exterior.terrain_renderer = renderer
	root.add_child(exterior)
	exterior.set_process(false)
	var player := CharacterBody2D.new()
	exterior.get_node("GroundObjects").add_child(player)
	exterior._player = player
	return exterior


func _cell(layer: TileMapLayer, coordinate: Vector2i) -> Array:
	return [layer.get_cell_source_id(coordinate), layer.get_cell_atlas_coords(coordinate),
		layer.get_cell_alternative_tile(coordinate)]


func _region(layer: TileMapLayer, coordinate: Vector2i) -> Dictionary:
	var result: Dictionary = {}
	for y in range(32):
		for x in range(32):
			var cell := coordinate * 32 + Vector2i(x, y)
			result[cell] = _cell(layer, cell)
	return result


func _replace(exterior: PlanetExterior, coordinate: Vector2i) -> void:
	exterior._pending.clear()
	exterior._pending.append(coordinate)
	exterior._generate_budget()


func _validate() -> void:
	var packed := load(EXTERIOR) as PackedScene
	if not _check(packed != null, "Production scene loads"):
		_finish()
		return
	var exterior := _attach(packed, PlanetExterior.TerrainRenderer.ILLUSTRATED)
	var state := PlanetWorldState.new(26026)
	await exterior.prepare_for_arrival(exterior._player, state)
	var presenter: IllustratedTerrainPresenter = exterior.get_node("IllustratedTerrainPresenter")
	var layer: TileMapLayer = presenter.get_node("Terrain")
	if not _check(exterior.terrain_failure().is_empty() and presenter._lookup != null
			and exterior._chunks.size() == 25, "Illustrated initialization and initial 25 chunks"):
		exterior.free()
		_finish()
		return
	_check(exterior._pending.is_empty() and not exterior._preparing, "Arrival queue drains")
	_check(exterior.loading_radius == 2 and exterior.retention_margin == 1
		and exterior.chunks_per_frame == 2, "Production budgets unchanged")
	_check(layer.get_used_cells().size() == 25600, "25 complete owned regions")
	var details: int = 0
	for coordinate in exterior._chunks:
		var chunk: TerrainChunk = exterior._chunks[coordinate]
		_check(not chunk._draw_legacy_ground and chunk._ground_materials.is_empty(), "Ground-only suppression")
		details += chunk._details.size()
		_check(chunk.is_inside_tree() and chunk.state_revision == state.revision, "Details node retained")
	_check(details > 0, "Decorative details generated")
	if not _check(exterior._tint_image != null and exterior._tint_texture != null
			and exterior._tint_material != null, "Shared tint resources exist"):
		exterior.free()
		_finish()
		return
	_check(exterior._tint_image.get_size() == Vector2i(231, 231)
		and exterior._tint_texture.get_size() == Vector2(231, 231), "Shared tint dimensions")
	_check(layer.material == exterior._tint_material and exterior._tint_material.shader != null,
		"Production shader bound; GPU compilation still needs graphical validation")
	_check(exterior._tint_material.get_shader_parameter("tint_field") == exterior._tint_texture,
		"Shader uses shared tint texture")
	_check(presenter.z_index == -11 and exterior._chunks[Vector2i.ZERO].z_index == -10,
		"Ground below detail nodes")
	var negative := Vector2i(-2, -2)
	var diagonal := negative + Vector2i.ONE
	var cell := negative * 32
	var samples := PackedInt32Array()
	for offset in IllustratedTerrainPresenter.OFFSETS:
		samples.append(exterior._generator.sample_ground_material(cell + offset))
	var expected := TerrainResolver.resolve(cell, samples, presenter._lookup, state.seed_value, TerrainResolver.RULE_VERSION)
	_check(not expected.is_empty() and _cell(layer, cell) == [expected.source_id,
		expected.atlas_coords, expected.alternative_id], "Absolute negative-coordinate assignment")
	_check(layer.to_global(layer.map_to_local(cell)).is_equal_approx((Vector2(cell) + Vector2.ONE * 0.5) * 64.0),
		"Half-scale negative cell center")
	var region := _region(layer, negative)
	var old_token: int = exterior._terrain_tokens[negative]
	_replace(exterior, negative)
	var new_token: int = exterior._terrain_tokens[negative]
	_check(new_token > old_token and _region(layer, negative) == region, "Deterministic token replacement")
	_check(not presenter.retire_chunk(negative, old_token).ok, "Stale retirement rejected")
	_check(not presenter.present_chunk(negative, old_token, Callable(exterior._generator,
		"sample_ground_material"), state.seed_value, TerrainResolver.RULE_VERSION).ok, "Stale presentation rejected")
	var neighbor := _region(layer, Vector2i.ZERO)
	_check(exterior._retire_illustrated_chunk(negative), "Direct production retirement")
	_check(layer.get_used_cells().size() == 24576, "Only 1024 cells retired")
	for owned in region:
		_check(layer.get_cell_source_id(owned) == -1, "Retired negative region empty")
	_check(_region(layer, Vector2i.ZERO) == neighbor, "Neighbor cells preserved")
	_check(exterior._tint_image.get_pixelv(exterior._tint_slot(negative)) == Color.WHITE, "Retired tint cleared")
	_replace(exterior, negative)
	_check(layer.get_used_cells().size() == 25600 and _region(layer, negative) == region,
		"Reload restores deterministic region")
	var previous_tint := exterior._tint_image.get_pixelv(exterior._tint_slot(diagonal))
	state.set_terrain_color(negative * 32 + Vector2i(31, 31), Color(0.8, 0.2, 0.1))
	exterior._update_neighborhood()
	_check(exterior._pending.size() == 25, "Revision schedules retained chunks")
	var stale_revision: int = exterior._chunks[diagonal].state_revision
	_replace(exterior, negative)
	_check(exterior._chunks[negative].state_revision == state.revision
		and exterior._chunks[diagonal].state_revision == stale_revision, "Bounded revision replacement")
	var corner := exterior._tint_image.get_pixelv(exterior._tint_slot(diagonal))
	_check(not corner.is_equal_approx(previous_tint), "Stored override changes shared corner tint")
	for offset in [Vector2i.RIGHT, Vector2i.DOWN, Vector2i.ONE]:
		var adjacent: Vector2i = negative + offset
		var shared_start := negative * 32 + Vector2i(32 if offset.x == 1 else 0, 32 if offset.y == 1 else 0)
		var shared_size := Vector2i(1 if offset.x == 1 else 33, 1 if offset.y == 1 else 33)
		for y in range(shared_size.y):
			for x in range(shared_size.x):
				var vertex := shared_start + Vector2i(x, y)
				var a := exterior._tint_slot(negative) + vertex - negative * 32
				var b := exterior._tint_slot(adjacent) + vertex - adjacent * 32
				_check(exterior._tint_image.get_pixelv(a).is_equal_approx(exterior._tint_image.get_pixelv(b)),
					"Revision borders agree while neighbor replacement is pending")
	# Cached detach/reattach must neither rebuild the 25 regions nor change tokens.
	var tokens := exterior._terrain_tokens.duplicate()
	var texture := exterior._tint_texture
	root.remove_child(exterior)
	root.add_child(exterior)
	await exterior.prepare_for_arrival(exterior._player, state)
	_check(exterior._terrain_tokens == tokens and exterior._tint_texture == texture, "Cached reattachment retains identity")
	# Inject one invalid sample via a test-only subclass, using the real queue path.
	var snapshot := _region(layer, negative)
	var old_chunk: TerrainChunk = exterior._chunks[negative]
	var tint_bytes := exterior._tint_image.get_data()
	exterior._generator = InvalidMaterialGenerator.new(state.seed_value, [], PackedVector2Array(), PackedVector2Array())
	_replace(exterior, negative)
	_check(not exterior.terrain_failure().is_empty() and exterior._pending == [negative], "Failure reported and request retained")
	_check(exterior._chunks[negative] == old_chunk and _region(layer, negative) == snapshot
		and exterior._tint_image.get_data() == tint_bytes, "Failed preparation preserves displayed data")
	var generation: int = exterior._terrain_generation
	exterior._generate_budget()
	exterior._process(0.0)
	_check(exterior._terrain_generation == generation and exterior._pending == [negative], "Failure stops further processing")
	exterior.free()
	# Legacy is deliberately only one direct budget call; no second 25-chunk drain.
	var legacy := _attach(packed, PlanetExterior.TerrainRenderer.LEGACY)
	legacy._configure_terrain_renderer()
	legacy._state = PlanetWorldState.new(26026)
	legacy._generator = PlanetGenerator.new(26026, [], PackedVector2Array(), PackedVector2Array())
	_replace(legacy, negative)
	var legacy_presenter: IllustratedTerrainPresenter = legacy.get_node("IllustratedTerrainPresenter")
	var legacy_layer: TileMapLayer = legacy_presenter.get_node("Terrain")
	_check(legacy_presenter._lookup == null and legacy_layer.tile_set == null
		and legacy_layer.get_used_cells().is_empty() and legacy._terrain_tokens.is_empty()
		and legacy._terrain_generation == 0, "Legacy avoids illustrated initialization and writes")
	_check(legacy._tint_image == null and legacy._tint_texture == null and legacy._tint_material == null,
		"Legacy avoids tint processing")
	_check(legacy._chunks[negative]._draw_legacy_ground
		and legacy._chunks[negative]._ground_materials.size() == 1024
		and not legacy._chunks[negative]._details.is_empty(), "Legacy ground and details remain")
	legacy.free()
	await process_frame
	_finish()
