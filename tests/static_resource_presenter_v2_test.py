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
    def _assert_area_limits(self, source):
        for name, value in (('MAX_AREA_AXIS', 6144.0), ('MAX_LIVE_AREA_AXIS', 26624.0),
                            ('LIVE_PAGE_SIZE', 1536.0), ('MAX_LIVE_PAGES', 361),
                            ('MAX_OWNERS', 64)):
            declaration = re.search(r'^const ' + name + r': \w+ = ([\d.]+)', source, re.M)
            self.assertIsNotNone(declaration, name)
            self.assertEqual(float(declaration[1]), value, name)
        request = body(source, 'request')
        self.assertIn('var area_limit: float = MAX_LIVE_AREA_AXIS if _world != null else MAX_AREA_AXIS', request)
        for guard in ('not area.is_finite()', 'not area.end.is_finite()',
                      'area.size.x <= 0.0 or area.size.y <= 0.0',
                      'area.size.x > area_limit or area.size.y > area_limit'):
            self.assertIn(guard, request)
        self.assertIn('return _failure("Invalid context or presentation area")', request)
        self.assertIn('return Catalog.failure("Invalid context or presentation area")', request)
        live, offline = request.split('\tvar plan :=', 1)
        self.assertIn('var page_size: float = LIVE_PAGE_SIZE', live)
        self.assertIn('(last.x - first.x + 1) * (last.y - first.y + 1) > MAX_LIVE_PAGES:\n\t\t\treturn _failure("Presentation page budget exceeded")', live)
        self.assertLess(live.index('area.size.x > area_limit'), live.index('_pages.append('))
        self.assertLess(live.index('> MAX_LIVE_PAGES:'), live.index('_pages.append('))
        self.assertLess(live.index('_pages.append('), live.index('_active = true'))
        self.assertIn('_source.query_owners(area.grow(_reach))', offline)
        self.assertIn('if not plan.ok:\n\t\treturn plan', offline)
        self.assertIn('if plan.owners.size() > MAX_OWNERS:\n\t\treturn Catalog.failure("Presentation owner budget exceeded")', offline)
        self.assertLess(offline.index('> MAX_OWNERS:'), offline.index('_active = true'))
        step = body(source, 'step')
        self.assertIn('_world.query_resource_descriptors_v2(page.grow(_reach), _world_token)', step)

    def _assert_descriptor_limits(self, source):
        for name, expected in (('MAX_DESCRIPTORS', 775), ('MAX_LIVE_DESCRIPTORS', 5815)):
            declaration = re.search(r'^const ' + name + r': int = (\d+)', source, re.M)
            self.assertIsNotNone(declaration, name)
            self.assertEqual(int(declaration[1]), expected)
        register = body(source, '_register_member')
        self.assertIn('var descriptor_limit: int = MAX_LIVE_DESCRIPTORS if _world != null else MAX_DESCRIPTORS', register)
        self.assertIn('if _registrations.size() > descriptor_limit:\n\t\treturn _failure("Presentation descriptor budget exceeded")', register)
        step = body(source, 'step')
        self.assertIn('if queried.deposits.size() > MAX_DESCRIPTORS:\n\t\t\t\treturn _failure("Presentation query budget exceeded")', step)
        self.assertLess(step.index('queried.deposits.size() > MAX_DESCRIPTORS'),
                        step.index('_members = queried.deposits.filter('))

    def _assert_world_read_boundary(self, source):
        code = '\n'.join(line.split('#')[0] for line in source.splitlines())
        allowed = {'resource_generation_v2_context', 'query_resource_descriptors_v2'}
        # Check every world member access, including dynamic call/get/set attempts.
        members = set(re.findall(r'\b(?:_world|world)\.(\w+)', code))
        self.assertEqual(members, allowed)
        self.assertNotRegex(code, r'\b(?:_world|world)\s*\[')
        self.assertNotRegex(code, r'\bvar\s+\w+\s*:?=\s*(?:_world|world)\s*(?:\n|$)')
        for forbidden in ('InventoryState', 'PlacementRules', 'ResourceDeposit',
                          'inventory.', 'deploy_machine', 'advance_production',
                          '_resource_v2', 'get_deposits_in_area', 'FileAccess.WRITE',
                          'FileAccess.READ_WRITE', 'FileAccess.WRITE_READ',
                          'store_var', 'save_game', 'quantity', 'depletion'):
            self.assertNotIn(forbidden, code)

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
        self._assert_area_limits(PRESENTER)

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
                         'MAX_CATALOGS: int = 8',
                         'result.locations.size() > MAX_LOCATIONS_PER_OWNER',
                         '_textures.size() >= TEXTURE_LIMIT', '_textures.erase(_textures.keys()[0])'):
            self.assertIn(fragment, PRESENTER)
        self.assertEqual(64*4*3 + 7, 775)
        self._assert_descriptor_limits(PRESENTER)
        self.assertIn('_pages.pop_front()', step)
        self.assertIn('_members.pop_front()', step)
        self.assertIn('_presenter.step(_token)', body(HARNESS, '_process'))
        self.assertNotRegex(body(HARNESS, '_process'), re.compile(r'^\s*while ', re.M))

    def test_cancellation_context_and_failure_clear_every_visual(self):
        step = body(PRESENTER, 'step')
        self.assertLess(step.index('token != _token or not _active'), step.index('_source.region(region_owner)'))
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
        # All three live resources opt into the same shared presenter.
        for resource in ('ferrite', 'cuprite', 'carbite'):
            self.assertIn(f'presentation_catalog = "res://scenes/world/resource_presentations/v2/{resource}.json"',
                          (ROOT / f'scenes/world/resource_definitions/v2/{resource}.tres').read_text())

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
        self._assert_world_read_boundary(PRESENTER)
        for source in (PRESENTER, CATALOG, HARNESS):
            code = '\n'.join(line.split('#')[0] for line in source.splitlines())
            for forbidden in ('ResourceDeposit', 'PlacementRules',
                              'InventoryState', 'deploy_machine', 'get_deposits_in_area',
                              'FileAccess.WRITE', 'store_var', 'save_game', 'quantity', 'depletion'):
                self.assertNotIn(forbidden, code)
            if source != PRESENTER:
                self.assertNotIn('PlanetWorldState', code)
        for resource in ('"ferrite"', '"carbite"', '"cuprite"'):
            self.assertNotIn(resource, PRESENTER)
            self.assertNotIn(resource, CATALOG)

    def test_adapter_bounds_reject_source_mutations(self):
        mutations = (
            ('relaxed offline area', 'MAX_AREA_AXIS: float = 6144.0', 'MAX_AREA_AXIS: float = 99999.0', self._assert_area_limits),
            ('relaxed live area', 'MAX_LIVE_AREA_AXIS: float = 26624.0', 'MAX_LIVE_AREA_AXIS: float = 99999.0', self._assert_area_limits),
            ('missing area check', 'area.size.x > area_limit', 'false', self._assert_area_limits),
            ('relaxed page budget', '> MAX_LIVE_PAGES:', '> 99999:', self._assert_area_limits),
            ('relaxed owner budget', '> MAX_OWNERS:', '> 99999:', self._assert_area_limits),
            ('relaxed offline descriptors', 'MAX_DESCRIPTORS: int = 775', 'MAX_DESCRIPTORS: int = 99999', self._assert_descriptor_limits),
            ('relaxed live descriptors', 'MAX_LIVE_DESCRIPTORS: int = 5815', 'MAX_LIVE_DESCRIPTORS: int = 99999', self._assert_descriptor_limits),
            ('missing accumulation check', '_registrations.size() > descriptor_limit', 'false', self._assert_descriptor_limits),
            ('relaxed per-query cap', 'queried.deposits.size() > MAX_DESCRIPTORS', 'queried.deposits.size() > MAX_LIVE_DESCRIPTORS', self._assert_descriptor_limits),
        )
        for label, old, new, check in mutations:
            with self.subTest(mutation=label):
                mutant = PRESENTER.replace(old, new, 1)
                self.assertNotEqual(mutant, PRESENTER)
                with self.assertRaises(AssertionError):
                    check(mutant)

    def test_world_read_boundary_rejects_unauthorized_calls(self):
        for call in ('_world.deploy_machine()', 'world.advance_production(1.0)',
                     '_world.collect_output(1)', '_world.configure_resource_generation_v2()',
                     '_world.query_deposit_descriptors(area)', '_world.get_deposits_in_area(area)',
                     '_world._resource_v2._source.query(area)',
                     '_world.call("deploy_machine")', '_world.get("_resource_v2")',
                     '_world.set("seed_value", 1)', '_world["seed_value"] = 1',
                     'var authority := _world\n\tauthority.deploy_machine()'):
            with self.subTest(call=call):
                with self.assertRaises(AssertionError):
                    self._assert_world_read_boundary(PRESENTER + '\nfunc unauthorized():\n\t' + call)

    def test_cuprite_prototype_scene_preserved(self):
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
