"""Source-bound contracts and independent finite models; never executes GDScript.

Python arithmetic/sequence proofs do not establish native TileMapLayer behavior.
"""
import hashlib
import itertools
from pathlib import Path
import re
import subprocess
import unittest

from production_terrain_preservation import (
    PRESENTER_BASE, PRESENTER_INPUT_SHA256, PRESENTER_TEST_SHA256,
    historical_presenter_bytes, verify_presenter_input, without_presenter_paths,
)

ROOT = Path(__file__).resolve().parents[1]
PRESENTER = 'scenes/world/illustrated_terrain_presenter.gd'
SOURCE = (ROOT/PRESENTER).read_text()
HELPER_SHA256 = '09ea841ca268e25cecdd4029be268f173ced31c656ad32f72904d56728402e86'
NATIVE_HELPER_SHA256 = 'dedccbe4f87a3493147d624b749d9084cff15479e7af319dce4897d58bacd245'


def body(source, name):
    return re.search(r'^(?:static )?func ' + name + r'\(.*?(?=^func |\Z)', source, re.M | re.S)[0]


def old(path):
    return subprocess.check_output(['git', 'show', f'{PRESENTER_BASE}:{path}'], cwd=ROOT).decode().replace('\r\n', '\n')


def region(coordinate):
    return {(coordinate[0]*32+x, coordinate[1]*32+y) for x in range(32) for y in range(32)}


class PresenterStaticTest(unittest.TestCase):
    def test_exact_inputs_and_test_amendments_reject_tampering(self):
        self.assertEqual(set(PRESENTER_INPUT_SHA256), {PRESENTER,
            'scenes/world/planet_exterior.gd', 'scenes/world/planet_exterior.tscn',
            'scenes/experiments/production_terrain/fixture.gd',
            'scenes/experiments/production_terrain/fixture.tscn',
            'scenes/experiments/production_terrain/engine_validation.gd'})
        for path in PRESENTER_INPUT_SHA256:
            raw = (ROOT/path).read_bytes()
            verify_presenter_input(path, raw)
            for bad in (raw + b'CHANGED', raw[1:], raw + raw):
                with self.subTest(path=path), self.assertRaises(AssertionError):
                    verify_presenter_input(path, bad)
            with self.assertRaises(AssertionError):
                verify_presenter_input(path + '.other', raw)
        for path in PRESENTER_TEST_SHA256:
            raw = (ROOT/path).read_bytes()
            self.assertEqual(historical_presenter_bytes(path, raw).decode().replace('\r\n', '\n'), old(path))
            for bad in (raw + b'CHANGED', raw[1:], raw + raw):
                with self.subTest(path=path), self.assertRaises(AssertionError):
                    historical_presenter_bytes(path, bad)

    def test_preservation_helpers_and_unrelated_inputs(self):
        for path, digest in [('tests/production_terrain_preservation.py', HELPER_SHA256),
                             ('tests/native_terrain_preservation.py', NATIVE_HELPER_SHA256)]:
            raw = (ROOT/path).read_bytes().replace(b'\r\n', b'\n')
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest, path)
            for bad in (raw + b'CHANGED', raw[1:], raw + raw):
                self.assertNotEqual(hashlib.sha256(bad).hexdigest(), digest, path)
        for path in ('scenes/world/terrain_chunk.gd', 'scenes/world/planet_generator.gd',
                     'assets/ui/b1_theme.tres', 'tools/run-local-tests.ps1', 'AGENTS.md'):
            raw = (ROOT/path).read_bytes() + b'OWNER CHANGE'
            self.assertEqual(historical_presenter_bytes(path, raw), raw)
            with self.assertRaises(AssertionError):
                verify_presenter_input(path, raw)
            self.assertEqual(without_presenter_paths([path]), [path])

    def test_historical_stage_reconciliation_rejects_changed_bytes(self):
        import json
        from static_production_terrain_test import historical_stage_input
        manifest_path = 'docs/experiments/production_terrain_stage.json'
        self.assertEqual((ROOT/manifest_path).read_text(), old(manifest_path))
        manifest = json.loads(old(manifest_path))
        for path in ('scenes/experiments/production_terrain/tint.gdshader',
                     'scenes/experiments/production_terrain/fixture.gd',
                     'assets/experiments/native_terrain_47_96/baked_v2/baseline_94.png'):
            raw = (ROOT/path).read_bytes()
            historical_stage_input(path, raw, manifest[path])
            for bad in (raw + b'CHANGED', raw[1:], raw + raw):
                with self.subTest(path=path), self.assertRaises(AssertionError):
                    historical_stage_input(path, bad, manifest[path])
            with self.assertRaises(AssertionError):
                historical_stage_input(path, raw, '0'*64)

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

    def test_diagnostics_and_dormant_production_gate(self):
        for key in ('"ok"', '"code"', '"chunk"', '"token"', '"message"'):
            self.assertIn(key, body(SOURCE, '_result'))
        self.assertIn('result["cell"] = cell', body(SOURCE, '_cell_failure'))
        exterior = (ROOT/'scenes/world/planet_exterior.gd').read_text()
        self.assertIn('terrain_renderer: TerrainRenderer = TerrainRenderer.LEGACY', exterior)
        assignments = re.findall(r'_effective_renderer\s*(?::[^=\n]+)?=\s*([^\n]+)', exterior)
        self.assertTrue(assignments)
        self.assertTrue(all(value == 'TerrainRenderer.LEGACY' for value in assignments))
        for name, call in [('_present_illustrated_chunk', '_terrain_presenter.initialize()'),
                           ('_retire_illustrated_chunk', '_terrain_presenter.retire_chunk')]:
            method = body(exterior, name)
            self.assertLess(method.index('if _effective_renderer != TerrainRenderer.ILLUSTRATED:\n\t\treturn true'), method.index(call))
        self.assertIn('Callable(_generator, "sample_ground_material")', exterior)
        self.assertIn('_present_illustrated_chunk(coordinate)', body(exterior, '_generate_budget'))
        self.assertIn('_retire_illustrated_chunk(coordinate)', body(exterior, '_update_neighborhood'))
        for unchanged in ('loading_radius: int = 2', 'retention_margin: int = 1', 'chunks_per_frame: int = 2'):
            self.assertIn(unchanged, exterior)

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
        baseline = old(path)
        for name in ('_ready', 'sample_material', '_generate', '_load_chunk', '_unload_chunk',
                     '_reload', '_set_shading', '_view', '_draw', '_button'):
            self.assertEqual(body(fixture, name).rstrip(), body(baseline, name).rstrip(), name)
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

    def test_unchanged_production_assets_controls_and_historical_inventory(self):
        changed = subprocess.check_output(['git', 'diff', '--name-only', PRESENTER_BASE, '--',
            'assets', 'scenes', 'shaders', 'construction', 'inventory', 'dialogue', 'objectives',
            'tools', 'AGENTS.md', 'project.godot', 'docs/LOCAL_TESTING.md',
            'docs/experiments/production_terrain_stage.json'], cwd=ROOT, text=True).splitlines()
        self.assertEqual(without_presenter_paths(changed), [])
        for path in ('scenes/world/planet_generator.gd', 'scenes/world/planet_world_state.gd',
                     'scenes/world/world_coordinates.gd', 'scenes/world/terrain_chunk.gd',
                     'scenes/world/terrain_resolver.gd', 'scenes/world/terrain_assignment_lookup.gd',
                     'scenes/experiments/production_terrain/tint.gdshader'):
            self.assertEqual((ROOT/path).read_text(), old(path), path)


if __name__ == '__main__':
    unittest.main()
