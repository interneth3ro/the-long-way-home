"""Nonexecuting presentation contracts, independent geometry and preservation.

No GDScript, Godot, import, rendering or runtime determinism is exercised.
"""
from pathlib import Path
import hashlib
import json
import re
import struct
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = 'f82298e1874ace843455f453aba2de583d2b8f5d'
PRESENTER = (ROOT / 'scenes/world/resource_presenter_v2.gd').read_text()
CATALOG = (ROOT / 'scenes/world/resource_presentation_catalog.gd').read_text()
HARNESS = (ROOT / 'scenes/experiments/resource_generation_v2/cuprite_inspection.gd').read_text()
SCENE = (ROOT / 'scenes/experiments/resource_generation_v2/cuprite_inspection.tscn').read_text()
ASSERTIONS = (ROOT / 'tests/resource_presenter_v2_test.gd').read_text()
CONFIG_PATH = 'scenes/world/resource_presentations/v2/cuprite.json'
CONFIG = json.loads((ROOT / CONFIG_PATH).read_text())


def body(source, name):
    return re.search(r'^(?:static )?func ' + name + r'\(.*?(?=^(?:static )?func |\Z)',
                     source, re.M | re.S)[0]


def baseline(path):
    return subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)


class ResourcePresenterV2StaticTests(unittest.TestCase):
    def test_frozen_artwork_identity_and_native_catalog_reference(self):
        self.assertEqual(CONFIG['version'], 1)
        self.assertEqual(CONFIG['resource_id'], 'cuprite')
        self.assertEqual(len(CONFIG['variants']), 1)
        entry = CONFIG['variants'][0]
        self.assertEqual(entry['id'], 'prototype_v1')
        self.assertEqual(entry['artwork'], 'res://assets/environment/exterior/cuprite/cuprite_prototype_v1.png')
        artwork = (ROOT / entry['artwork'][6:]).read_bytes()
        self.assertEqual(hashlib.sha256(artwork).hexdigest(), entry['sha256'])
        self.assertEqual(entry['sha256'], '6a3ed462b0da325b0dc334b0fb0f5d467242d7758dbd71bfe2aa46dff8b531fe')
        self.assertEqual(list(struct.unpack('>II', artwork[16:24])), entry['size'])
        self.assertEqual(entry['size'], [1536, 1024])
        self.assertEqual(entry['scale'], 0.225)
        self.assertEqual(entry['offset'], [0, 16])
        path = 'scenes/world/resource_definitions/v2/cuprite.tres'
        # Exactly one additive field. All generation/identity bytes preserved.
        current = (ROOT / path).read_bytes().replace(b'\r\n', b'\n')
        original = baseline(path).replace(b'\r\n', b'\n')
        self.assertEqual(current, original + f'presentation_catalog = "res://{CONFIG_PATH}"\n'.encode())

    def test_independent_anchor_artwork_registration_math(self):
        entry = CONFIG['variants'][0]
        width, height = [value * entry['scale'] for value in entry['size']]
        self.assertAlmostEqual(width, 345.6)
        self.assertAlmostEqual(height, 230.4)
        for cell in [(0, 0), (-2, -2), (-48, 47), (8192, -8192)]:
            center = (cell[0] * 32 + 64, cell[1] * 32 + 64)
            sprite = (center[0], center[1] + 16)
            envelope = (sprite[0] - width/2, sprite[1] - height/2,
                        sprite[0] + width/2, sprite[1] + height/2)
            self.assertAlmostEqual((envelope[0] + envelope[2])/2, center[0])
            self.assertAlmostEqual((envelope[1] + envelope[3])/2 - center[1], 16)
            self.assertGreater(width, 128 + 2*64)  # existing policy envelope is smaller
        for fragment in ('member.anchor_cells.position) * 32.0', 'Vector2(128, 128)',
                         'logical.get_center()', 'center + entry.offset',
                         '"logical_bounds": logical', '"illustrated_envelope": Rect2'):
            self.assertIn(fragment, body(CATALOG, 'registration'))

    def test_spatial_query_covers_painted_edges_without_policy_mutation(self):
        request = body(PRESENTER, 'request')
        self.assertIn('_source.query_owners(area.grow(_reach))', request)
        self.assertIn('_area.intersects(registration.illustrated_envelope, true)', PRESENTER)
        # Maximum parent-to-painted-point reach is offset + half-anchor + canvas.
        painted = max(CONFIG['variants'][0]['size']) * 0.225 / 2
        self.assertLessEqual(448 + 64 + painted, 640 + painted)
        self.assertIn('reach > MAX_REACH', CATALOG)
        self.assertIn('area.size.x > MAX_AREA_AXIS', request)
        self.assertIn('area.end.is_finite()', request)
        self.assertLess(request.index('area.size.x > MAX_AREA_AXIS'), request.index('_source.query_owners'))
        self.assertLess(request.index('plan.owners.size() > MAX_OWNERS'), request.index('_active = true'))

    def test_registration_determinism_and_duplicate_admission(self):
        registration = body(CATALOG, 'registration')
        for field in ('resource_id', 'deposit_id', 'anchor_cells', 'artwork', 'sha256',
                      'scale', 'offset', 'variant_id', 'illustrated_envelope'):
            self.assertIn(f'"{field}"', registration)
        self.assertIn('ids.sort()', registration)
        self.assertIn('metadata.get("variant_id", ids[0])', registration)
        self.assertIn('_ids.sort()', PRESENTER)
        self.assertIn('_registrations.has(identity) and _registrations[identity] != registration', PRESENTER)
        self.assertIn('if not _sprites.has(identity):', PRESENTER)
        self.assertEqual(PRESENTER.count('Sprite2D.new()'), 1)
        for forbidden in ('randf(', 'randi(', 'hash(', 'Time.', 'await '):
            self.assertNotIn(forbidden, registration)

    def test_incremental_work_and_cardinality_bounds(self):
        step = body(PRESENTER, 'step')
        self.assertIn('_owners.pop_front()', step)
        self.assertIn('_locations.pop_front()', step)
        self.assertNotIn('while ', step)
        self.assertNotIn('for owner', step)
        self.assertNotIn('for identity', step)
        for fragment in ('MAX_DESCRIPTORS: int = 775', 'MAX_OWNERS: int = 64',
                         'MAX_LOCATIONS_PER_OWNER: int = 11', 'TEXTURE_LIMIT: int = 8',
                         'MAX_CATALOGS: int = 8', '_registrations.size() > MAX_DESCRIPTORS',
                         'result.locations.size() > MAX_LOCATIONS_PER_OWNER',
                         '_textures.size() >= TEXTURE_LIMIT', '_textures.erase(_textures.keys()[0])'):
            self.assertIn(fragment, PRESENTER)
        self.assertEqual(64*4*3 + 7, 775)
        self.assertIn('_presenter.step(_token)', body(HARNESS, '_process'))
        self.assertNotRegex(body(HARNESS, '_process'), re.compile(r'^\s*while ', re.M))

    def test_cancellation_context_and_failure_clear_every_visual(self):
        step = body(PRESENTER, 'step')
        self.assertLess(step.index('token != _token or not _active'), step.index('_source.region(owner)'))
        self.assertIn('_source.identity_policy() != _policy', step)
        self.assertIn('location.world_seed != _seed or location.generation_policy != _policy', step)
        for fragment in ('_token += 1', '_active = false', '_registrations.clear()',
                         '_owners.clear()', '_locations.clear()', '_ids.clear()',
                         'remove_child(sprite)', 'sprite.free()', '_sprites.clear()'):
            self.assertIn(fragment, body(PRESENTER, 'cancel'))
        for fragment in ('cancel()', '_source = null', '_catalogs.clear()', '_references.clear()', '_textures.clear()'):
            self.assertIn(fragment, body(PRESENTER, 'dispose'))
        self.assertIn('dispose()', body(PRESENTER, '_failure'))
        self.assertIn('dispose()', body(PRESENTER, '_exit_tree'))
        self.assertIn('_exiting = true', body(PRESENTER, '_exit_tree'))
        self.assertIn('sprite.hide()\n\t\t\tsprite.queue_free()\n\t\telse:', body(PRESENTER, 'cancel'))
        self.assertLess(body(PRESENTER, 'configure').index('dispose()'), body(PRESENTER, 'configure').index('_source = source'))

    def test_fail_closed_catalog_and_texture_admission(self):
        for fragment in ('file.get_length() > MAX_BYTES', 'data.get("resource_id") != resource_id',
                         'data.variants.size() > MAX_VARIANTS', 'variants.has(entry.id)',
                         'size != size.floor()', 'not is_finite(float(value.scale))',
                         'value.scale <= 0.0', 'reach > MAX_REACH', 'value.sha256.length() != 64',
                         'not catalog.variants.has(variant)', 'metadata.get("catalog_ref", catalog_ref) != catalog_ref'):
            self.assertIn(fragment, CATALOG)
        for fragment in ('file.get_length() > Catalog.MAX_IMAGE_BYTES',
                         'FileAccess.get_sha256(registration.artwork) != registration.sha256',
                         'ResourceLoader.exists(registration.artwork, "Texture2D")',
                         'texture.get_size() != registration.size'):
            self.assertIn(fragment, body(PRESENTER, '_texture'))
        for resource in ('ferrite', 'carbite'):
            self.assertNotIn('presentation_catalog =', (ROOT / f'scenes/world/resource_definitions/v2/{resource}.tres').read_text())

    def test_isolated_opt_in_seven_reservations_and_final_context(self):
        for guard in ('development_inspection_enabled: bool = false',
                      'not OS.has_feature("editor")', 'get_tree().current_scene != self',
                      'world_seed: int = 26026'):
            self.assertIn(guard, HARNESS)
        ready = body(HARNESS, '_ready')
        self.assertLess(ready.index('not development_inspection_enabled'), ready.index('Generator.new('))
        for fragment in ('[FERRITE, CARBITE, CUPRITE]', 'Context.protected_bounds(), Context.SHIP_REFERENCE',
                         '_generator.reservations()', 'counts != Generator.REQUIRED',
                         '_presenter.configure(_generator, world_seed, [CUPRITE])'):
            self.assertIn(fragment, ready)
        self.assertNotIn('development_inspection_enabled = true', SCENE)
        for path in ('scenes/main/playthrough_state.gd', 'scenes/world/planet_world_state.gd'):
            self.assertIn('26026', (ROOT / path).read_text())
        for file in (ROOT / 'scenes').rglob('*'):
            if file.suffix in ('.gd', '.tscn', '.tres') and 'experiments/resource_generation_v2' not in file.as_posix():
                self.assertNotIn('cuprite_inspection', file.read_text(encoding='utf-8'))

    def test_no_gameplay_authority_or_persistence_in_new_code(self):
        for source in (PRESENTER, CATALOG, HARNESS):
            code = '\n'.join(line.split('#')[0] for line in source.splitlines())
            for forbidden in ('ResourceDeposit', 'PlanetWorldState', 'PlacementRules',
                              'InventoryState', 'deploy_machine', 'get_deposits_in_area',
                              'FileAccess.WRITE', 'store_var', 'save_game', 'quantity', 'depletion'):
                self.assertNotIn(forbidden, code)
        for resource in ('"ferrite"', '"carbite"', '"cuprite"'):
            self.assertNotIn(resource, PRESENTER)
            self.assertNotIn(resource, CATALOG)

    def test_preserved_legacy_artwork_generation_and_runner_bytes(self):
        paths = ['assets', 'construction', 'inventory', 'persistence', 'tools', 'AGENTS.md',
                 'project.godot', 'scenes/main', 'scenes/world/planet_exterior.gd',
                 'scenes/world/planet_exterior.tscn', 'scenes/world/planet_world_state.gd',
                 'scenes/world/ferrite_deposit_presenter.gd', 'scenes/world/ferrite_region_generator.gd',
                 'scenes/world/cuprite_visual_prototype.tscn', 'scenes/world/crash_site_protection.gd',
                 'scenes/world/resource_generation_crash_site.gd', 'scenes/world/ordinary_resource_generator.gd',
                 'scenes/world/starting_resource_generator.gd', 'scenes/world/resource_generation_descriptors.gd',
                 'scenes/world/world_resource_definition.gd', 'scenes/world/resource_migration_diagnostics.gd']
        changed = subprocess.check_output(['git', 'diff', BASE, '--name-only', '--', *paths], cwd=ROOT, text=True)
        self.assertEqual(changed, '')
        # Checkout CRLF is preserved; Git stores the normalized source as LF.
        self.assertEqual((ROOT / 'scenes/world/cuprite_visual_prototype.tscn').read_bytes().replace(b'\r\n', b'\n'),
                         baseline('scenes/world/cuprite_visual_prototype.tscn').replace(b'\r\n', b'\n'))

    def test_authored_runtime_obligations_and_unchanged_runner_dispatch(self):
        for label in ('one sprite maximum per step', 'overlapping owner queries deduplicate stable IDs',
                      'reverse query order independence', 'old token cannot publish',
                      'cancel removes visuals and descriptors', 'movement retires off-area visuals',
                      'policy replacement clears old visuals', 'wrong seed descriptors fail closed',
                      'all seven inactive and active reservations preserved', 'complete disposal'):
            self.assertIn(label, ASSERTIONS)
        for runner in (ROOT / 'tools').glob('*.ps1'):
            self.assertNotIn('resource_presenter_v2_test', runner.read_text())

    def test_new_scene_and_script_references_resolve_statically(self):
        paths = [ROOT / 'scenes/world/resource_presenter_v2.gd',
                 ROOT / 'scenes/world/resource_presentation_catalog.gd',
                 ROOT / 'scenes/experiments/resource_generation_v2/cuprite_inspection.gd',
                 ROOT / 'scenes/experiments/resource_generation_v2/cuprite_inspection.tscn',
                 ROOT / 'tests/resource_presenter_v2_test.gd']
        for path in paths:
            for ref in re.findall(r'(?:preload\(|path=|extends )"res://([^"\n]+)"', path.read_text()):
                self.assertTrue((ROOT / ref).is_file(), (path.name, ref))
        self.assertIn('$HUD/Instructions', HARNESS)
        self.assertIn('name="Instructions" type="Label" parent="HUD"', SCENE)


if __name__ == '__main__':
    unittest.main()
