"""Fresh-session Ferrite cutover contracts. No Godot or project code executes."""
import hashlib
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = '1dbdcbdc8a1ee22b411b5ded056d0a2574e1ff2a'


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def body(source, name):
    return re.search(r'^func ' + name + r'\(.*?(?=^func |\Z)', source, re.M | re.S)[0]


class FerriteLiveAuthorityTests(unittest.TestCase):
    def test_no_active_legacy_authority_or_visuals(self):
        world = read('scenes/world/planet_world_state.gd')
        exterior = read('scenes/world/planet_exterior.gd')
        scene = read('scenes/world/planet_exterior.tscn')
        for token in ('FerriteRegionGenerator', 'FerriteDepositPresenter', 'crash_site_ferrite',
                      'introductory_ferrite.tres', 'deposit_at(', '_ferrite_presenter', '_ferrite_token'):
            self.assertNotIn(token, world + exterior + scene)
        self.assertNotIn('FerriteGround', scene)
        self.assertNotIn('FacetedFerrite', scene)
        self.assertNotIn('func get_deposit', world)
        # Exact historical presenter source and UID remain preserved, without an active script.
        original = subprocess.check_output(['git', 'show', BASE + ':scenes/world/ferrite_deposit_presenter.gd'], cwd=ROOT)
        self.assertEqual((ROOT / 'scenes/world/ferrite_deposit_presenter.gd.txt').read_bytes().replace(b'\r\n', b'\n'), original.replace(b'\r\n', b'\n'))
        self.assertTrue((ROOT / 'scenes/world/ferrite_deposit_presenter.gd.uid').is_file())

    def test_generation_assets_and_execution_controls_unchanged(self):
        paths = ['scenes/world/ordinary_resource_generator.gd', 'scenes/world/starting_resource_generator.gd',
                 'scenes/world/resource_generation_v2_integration.gd',
                 'scenes/world/resource_generation_descriptors.gd', 'scenes/world/resource_generation_crash_site.gd',
                 'scenes/world/resource_presenter_v2.gd', 'scenes/world/resource_presentation_catalog.gd',
                 'tools/run-local-tests.ps1', 'tools/run-behavioral-tests.ps1', 'tests/behavioral/test_runner.gd',
                 'scenes/world/introductory_ferrite.tres', 'scenes/world/ferrite_region_generator.gd']
        for resource in ('cuprite', 'carbite'):
            paths.extend([f'scenes/world/resource_definitions/v2/{resource}.tres',
                          f'scenes/world/resource_presentations/v2/{resource}.json'])
        paths += ['scenes/world/resource_presentations/v2/ferrite.json', 'inventory/extractor.tres']
        for path in paths:
            with self.subTest(path=path):
                old = subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)
                self.assertEqual((ROOT / path).read_bytes().replace(b'\r\n', b'\n'), old.replace(b'\r\n', b'\n'))
        art = ROOT / 'assets/environment/exterior/ferrite/ferrite_v2_production_candidate_v1.png'
        self.assertEqual(hashlib.sha256(art.read_bytes()).hexdigest(),
                         'bd0f7696d64f8f96dca3cbfa0baecb7bba7da96876242eabc5056916574825a0')

    def test_shared_three_resource_presentation_and_readiness(self):
        exterior = read('scenes/world/planet_exterior.gd')
        setup = body(exterior, '_initialize_world')
        self.assertEqual(setup.count('ResourcePresenterV2.new()'), 1)
        for resource in ('ferrite', 'cuprite', 'carbite'):
            self.assertIn(f'resource_definitions/v2/{resource}.tres', setup)
        self.assertIn('presentation_catalog = "res://scenes/world/resource_presentations/v2/ferrite.json"',
                      read('scenes/world/resource_definitions/v2/ferrite.tres'))
        for name in ('arrival_is_ready', '_initial_completed'):
            self.assertIn('_resource_presenter.is_complete(_resource_token)', body(exterior, name))
        for name in ('arrival_is_ready', 'preparation_is_ready'):
            self.assertIn('result.get("resource_token", -1) == _resource_token', body(exterior, name))
        for path in ('scenes/main/main.gd', 'scenes/main/main_v2.gd', 'scenes/application/application.gd'):
            self.assertIn('is_resource_generation_v2_ready()', read(path))
            self.assertNotIn('is_resource_generation_ready()', read(path))

    def test_discovery_uses_real_starting_identity_and_context(self):
        progression = body(read('scenes/main/playthrough_state.gd'), 'discover_ferrite')
        for token in ('resource_descriptor_v2_by_id(deposit_id, token)', 'starting_resource_reservations_v2(token)',
                      'resolved.descriptor.resource_type != "ferrite"', 'member == resolved.descriptor',
                      'if not starting:', 'ferrite_discovered = true', 'ferrite_discovery_completed.emit()'):
            self.assertIn(token, progression)
        self.assertLess(progression.index('if not starting:'), progression.index('ferrite_discovered = true'))
        setup = body(read('scenes/world/planet_exterior.gd'), '_configure_discovery')
        for token in ('starting_resource_reservations_v2(context.token)', 'location.resource_type != "ferrite"',
                      'interaction.deposit_id = member.deposit_id', 'interaction.context_token = context.token',
                      'ExtractorAnchorRules.bounds(member.anchor_cells)', '_discovery_token == context.token'):
            self.assertIn(token, setup)
        interaction = read('scenes/interaction/ferrite_inspection.gd')
        self.assertIn('_progression.discover_ferrite(deposit_id, context_token)', interaction)
        self.assertNotIn('crash_site_ferrite', interaction + progression)

    def test_output_context_and_claim_release_are_owned(self):
        world = read('scenes/world/planet_world_state.gd')
        commit = body(world, '_deploy_machine_transaction')
        self.assertIn('machine["v2_context_token"] = v2_ticket.token', commit)
        output = body(world, 'extractor_output_item')
        self.assertIn('machine.get("v2_context_token") != context.token', output)
        self.assertIn('extractor_occupant_v2(machine.v2_deposit_id) != machine.id', output)
        self.assertNotIn('deposit_at(', output)
        recovery = body(world, 'recover_machine')
        self.assertIn('if extractor_occupant_v2(deposit_id) == machine_id:', recovery)
        self.assertLess(recovery.index('inventory.add_items'), recovery.index('_extractor_claims_v2.erase'))

    def test_highlights_use_descriptor_anchors(self):
        highlight = body(read('scenes/world/planet_exterior.gd'), '_refresh_highlights')
        self.assertIn('query_resource_descriptors_v2(', highlight)
        self.assertIn('ExtractorAnchorRules.bounds(member.anchor_cells)', highlight)
        self.assertIn('seen.has(member.deposit_id)', highlight)
        self.assertNotIn('intersect_polygons', highlight)

    def test_cutover_projection_rejects_unrelated_scene_and_story_changes(self):
        from initial_exterior_preservation import without_initial_preparation
        for path, old, new in (
            ('scenes/world/planet_exterior.tscn', 'position = Vector2(-384, -64)',
             'position = Vector2(1, 1)'),
            ('scenes/main/playthrough_state.gd', 'var ferrite_acquired: bool = false',
             'var ferrite_acquired: bool = true'),
        ):
            original = read(path)
            self.assertIn(old, original)
            with self.assertRaises(AssertionError):
                without_initial_preparation(path, original.replace(old, new, 1).encode('utf-8'))


if __name__ == '__main__':
    unittest.main()
