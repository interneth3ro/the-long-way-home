"""Source-bound contracts and independent finite models; never executes GDScript.

Python arithmetic/sequence proofs do not establish native TileMapLayer behavior.
"""
import itertools
from pathlib import Path
import re
import unittest
ROOT = Path(__file__).resolve().parents[1]
PRESENTER = 'scenes/world/illustrated_terrain_presenter.gd'
SOURCE = (ROOT/PRESENTER).read_text()


def body(source, name):
    return re.search(r'^(?:static )?func ' + name + r'\(.*?(?=^func |\Z)', source, re.M | re.S)[0]


def region(coordinate):
    return {(coordinate[0]*32+x, coordinate[1]*32+y) for x in range(32) for y in range(32)}


class PresenterStaticTest(unittest.TestCase):
    def test_region_geometry_negative_ownership_and_halo(self):
        self.assertIn('WIDTH: int = WorldCoordinates.CHUNK_TILES', SOURCE)
        self.assertEqual(region((-1, -1)), set(itertools.product(range(-32, 0), repeat=2)))
        for a, b in itertools.combinations(itertools.product(range(-2, 3), repeat=2), 2):
            self.assertTrue(region(a).isdisjoint(region(b)))
        for name, operation in [('present_chunk', '_terrain.set_cell'), ('retire_chunk', '_terrain.erase_cell')]:
            method = body(SOURCE, name)
            for required in ('var origin := coordinate * WIDTH', 'for y in range(WIDTH):',
                             'for x in range(WIDTH):', 'origin + Vector2i(x, y)', operation):
                self.assertIn(required, method)
        prepare = body(SOURCE, '_prepare')
        self.assertEqual(prepare.count('range(-1, WIDTH + 1)'), 2)
        self.assertIn('sampler.call(cell)', prepare)
        self.assertIn('not sample is int or sample < 0 or sample > 4', prepare)
        self.assertIn('samples.append(halo[cell + offset])', prepare)
        self.assertNotIn('get_cell_', prepare)
        self.assertEqual(34*34, 1156)

    def test_registration_authority_and_retirement_sequence_model(self):
        # Bind ordering predicates to source; independent state/visible-region oracle.
        begin = body(SOURCE, 'begin_generation')
        self.assertIn('generation_token <= _high_water', begin)
        self.assertLess(begin.index('if generation_token <= _high_water'), begin.index('_high_water ='))
        self.assertIn('_active[coordinate] = {"token": generation_token, "presented": false}', begin)
        self.assertNotIn('_terrain.', begin)
        self.assertIn('_active.has(coordinate) and _active[coordinate].token == token', body(SOURCE, '_matches'))
        self.assertIn('if presentation and _active[coordinate].presented:', body(SOURCE, '_current'))
        self.assertIn('_active.erase(coordinate)', body(SOURCE, 'retire_chunk'))
        high, active, pixels = 0, {}, {}
        def register(c, token):
            nonlocal high
            # Evaluate the actual restricted source predicate.
            predicate = re.search(r'if (generation_token <= _high_water):', begin)[1]
            if token <= 0 or eval(predicate, {'__builtins__': {}}, {'generation_token': token, '_high_water': high}):
                return False
            high, active[c] = token, (token, False)
            return True
        def present(c, token, valid=True):
            if active.get(c) != (token, False) or not valid:
                return False
            pixels.update(dict.fromkeys(region(c), token))
            active[c] = token, True
            return True
        def retire(c, token):
            if c not in active or active[c][0] != token:
                return False
            for cell in region(c):
                pixels.pop(cell, None)
            del active[c]
            return True
        a, b = (-1, -1), (0, -1)
        self.assertTrue(register(a, 1) and present(a, 1))
        self.assertTrue(register(b, 2) and present(b, 2))
        snapshot = pixels.copy()
        self.assertTrue(register(a, 3))
        self.assertFalse(present(a, 1))  # delayed old result, newer still pending
        self.assertFalse(retire(a, 1))
        self.assertFalse(present(a, 3, False))
        self.assertEqual(pixels, snapshot)
        self.assertTrue(register(a, 4) and present(a, 4))
        self.assertFalse(present(a, 3))
        self.assertFalse(present(a, 4))  # duplicate
        self.assertTrue(retire(a, 4))
        self.assertFalse(register(a, 4))
        self.assertFalse(present(a, 4))
        self.assertTrue(register(a, 5) and present(a, 5))
        self.assertFalse(retire(a, 4))
        self.assertEqual({p:v for p,v in pixels.items() if p in region(b)},
                         {p:v for p,v in snapshot.items() if p in region(b)})

    def test_complete_validation_before_mutation_and_failure_preservation(self):
        present = body(SOURCE, 'present_chunk')
        order = ['_current(', '_busy = true', '_prepare(', 'if not prepared.ok:',
                 '_validate_assignments(', 'if not validated.ok:', 'if not _matches(', '_terrain.set_cell(',
                 '_active[coordinate].presented = true']
        self.assertEqual([present.index(x) for x in order], sorted(present.index(x) for x in order))
        for forbidden in ('clear(', 'erase_cell(', 'await ', 'call_deferred'):
            self.assertNotIn(forbidden, present)
        validate = body(SOURCE, '_validate_assignments')
        for guard in ('assignments.size() != WIDTH * WIDTH', 'assignments.get(cell)',
                      'not value is Dictionary', 'is Vector2i', 'is PackedInt32Array',
                      'record.signature.size() != 9', 'tiles.has_source', 'source.has_tile',
                      'source.has_alternative_tile', 'signature != record.signature',
                      '_lookup.assignment(signature, record.variant)', 'expected != record'):
            self.assertIn(guard, validate)
        self.assertNotIn('set_cell(', validate)
        self.assertNotIn('erase_cell(', validate)
        self.assertIn('if _busy:', body(SOURCE, '_guard'))
        self.assertNotIn('_high_water =', body(SOURCE, 'initialize'))
        self.assertNotIn('_active.clear', SOURCE)

    def test_determinism_actual_resolver_oracle_and_reverse_order(self):
        from static_production_terrain_test import chunk, CHUNKS
        expected = {c: chunk(c) for c in CHUNKS}
        self.assertEqual(expected, {c: chunk(c) for c in reversed(CHUNKS)})
        self.assertEqual(expected[(-1, -1)], chunk((-1, -1)))
        self.assertIn('TerrainResolver.resolve(cell, samples, _lookup, seed_value, rule_version)', SOURCE)
        self.assertIn('rule_version != TerrainResolver.RULE_VERSION', body(SOURCE, 'present_chunk'))
        for forbidden in ('set_cells_terrain', 'randf(', 'randi(', 'func _process', 'func _physics_process',
                          'PlanetWorldState', 'PlanetGenerator.new', 'push_error(', 'push_warning('):
            self.assertNotIn(forbidden, SOURCE)

    def test_diagnostics(self):
        for key in ('"ok"', '"code"', '"chunk"', '"token"', '"message"'):
            self.assertIn(key, body(SOURCE, '_result'))
        self.assertIn('result["cell"] = cell', body(SOURCE, '_cell_failure'))

    def test_scene_layers_and_no_autonomous_initialization(self):
        for path in ('scenes/world/planet_exterior.tscn', 'scenes/experiments/production_terrain/fixture.tscn'):
            scene = (ROOT/path).read_text()
            layer = scene.split('[node name="Terrain" type="TileMapLayer" parent="IllustratedTerrainPresenter"]', 1)[1].split('[node ', 1)[0]
            for prop in ('scale = Vector2(0.5, 0.5)', 'collision_enabled = false',
                         'navigation_enabled = false', 'occlusion_enabled = false'):
                self.assertIn(prop, layer)
            self.assertNotIn('position =', layer)
            for ref in re.findall(r'path="res://([^"]+)"', scene):
                self.assertTrue((ROOT/ref).is_file(), ref)
        self.assertNotIn('func _ready', SOURCE)
        self.assertNotIn('func _enter_tree', SOURCE)
        self.assertIn('load(TerrainAssignmentLookup.TILESET_PATH)', body(SOURCE, 'initialize'))

    def test_reference_methods_shading_and_masks_remain_exact(self):
        path = 'scenes/experiments/production_terrain/fixture.gd'
        fixture = (ROOT/path).read_text()
        self.assertIn('_presenter_mode: bool = false', fixture)
        self.assertIn('backend.add_item("PR #102 reference")', fixture)
        switch = body(fixture, 'select_presenter_mode')
        self.assertLess(switch.index('presenter.initialize()'), switch.index('_unload_chunk(coordinate)'))
        self.assertIn('terrain.visible = not enabled', switch)
        self.assertIn('presenter.visible = enabled', switch)
        self.assertNotIn('func _process', fixture)
        native = (ROOT/'scenes/experiments/production_terrain/engine_validation.gd').read_text()
        for marker in ('Stale retirement rejected', 'Stale presentation rejected', 'Negative owned cell erased',
                       'Invalid assignment preserves terrain', 'Reference restored unchanged',
                       'Reentrant mutation rejected', 'Adjacent 2048 cells', 'Invalid version'):
            self.assertIn(marker, native)

    def test_fixture_startup_is_reference_only(self):
        directory = ROOT/'scenes/experiments/production_terrain'
        scene = (directory/'fixture.tscn').read_text()
        fixture = (directory/'fixture.gd').read_text()
        def node(header):
            return scene.split(header, 1)[1].split('[node ', 1)[0]
        root = node('[node name="ProductionTerrainFixture" type="Node2D"]')
        reference = node('[node name="Terrain" type="TileMapLayer" parent="."]')
        presenter = node('[node name="IllustratedTerrainPresenter" type="Node2D" parent="."]')
        child = node('[node name="Terrain" type="TileMapLayer" parent="IllustratedTerrainPresenter"]')
        # CanvasItem visibility defaults true; the explicit hidden parent hides
        # its Terrain child. The presenter also starts empty and uninitialized.
        self.assertNotIn('visible = false', root + reference)
        self.assertIn('visible = false', presenter)
        self.assertIn('tile_set = ExtResource("2")', reference)
        self.assertNotIn('tile_set =', child)
        self.assertNotIn('tile_map_data', scene)
        self.assertIn('var _presenter_mode: bool = false', fixture)
        self.assertIn('var _presenter_tokens: Dictionary[Vector2i, int] = {}', fixture)
        ready = body(fixture, '_ready')
        self.assertIn('_set_shading(0)', ready)
        self.assertIn('_reload(false)', ready)
        for forbidden in ('presenter.', 'select_presenter_mode(', '_reload_active(', 'visible =', 'await '):
            self.assertNotIn(forbidden, ready)
        controls = body(fixture, '_build_controls')
        self.assertLess(controls.index('backend.add_item("PR #102 reference")'),
                        controls.index('backend.add_item("PR #103 presenter")'))
        self.assertNotIn('backend.select(1)', controls)
        self.assertNotIn('item_selected.emit', controls)

    def test_fixture_switch_retires_before_exclusive_visibility_and_population(self):
        fixture = (ROOT/'scenes/experiments/production_terrain/fixture.gd').read_text()
        switch = body(fixture, 'select_presenter_mode')
        self.assertIn('if enabled == _presenter_mode:\n\t\treturn true', switch)
        visibility = '_presenter_mode = enabled\n\tterrain.visible = not enabled\n\tpresenter.visible = enabled'
        self.assertIn(visibility, switch)
        self.assertLess(switch.index('_unload_chunk(coordinate)'), switch.index(visibility))
        self.assertLess(switch.index('_unload_active(coordinate)'), switch.index(visibility))
        self.assertLess(switch.index(visibility), switch.index('return _reload_active(false)'))
        self.assertIn('if not result.ok:\n\t\t\t_status.text = "STOP: " + str(result)\n\t\t\treturn false', switch)
        self.assertIn('if not _unload_active(coordinate):\n\t\t\t\treturn false', switch)
        for forbidden in ('await ', 'call_deferred', 'create_timer'):
            self.assertNotIn(forbidden, switch)
        for selected in (False, True, False, True, False):
            # Truth table of the exact source assignments, not engine execution.
            self.assertEqual(sum((not selected, selected)), 1)


if __name__ == '__main__':
    unittest.main()
